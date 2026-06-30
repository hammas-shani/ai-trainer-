from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from graph_logic import app_graph
from audio_service import text_to_speech_bytes 
from prompt_builder import build_system_prompt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
SESSIONS = {}

class SessionStartRequest(BaseModel):
    sessionType: str
    userExpertise: str = ""
    projectType: str = ""
    clientPersona: str = ""
    callGoal: str = ""
    field: str = ""
    seniority: str = ""
    focus: str = ""
    tone: str = ""
    customNotes: str = ""

@app.post("/api/session/start")
async def start_session(payload: SessionStartRequest):
    try:
        sys_prompt = build_system_prompt(payload.model_dump(), stage="Greeting", user_facts={})
        session_id = str(uuid.uuid4())
        
        state = {
            "messages": [],
            "session_id": session_id,
            "system_prompt": sys_prompt,
            "user_detailed_prompt": "",
            "formatted_transcript": "",
            "current_stage": "Greeting",
            "user_facts": {}
        }
        
        # Invoke AI to get the first greeting
        new_state = await app_graph.ainvoke(state)
        
        ai_response_obj = new_state["messages"][-1]
        if isinstance(ai_response_obj, dict):
            ai_response = ai_response_obj.get("content", "")
        else:
            ai_response = ai_response_obj.content
            
        print(f"🤖 AI Initial Greeting: {ai_response}")
        
        audio_b64 = await text_to_speech_bytes(ai_response)
        
        # Save state with the AI's first message appended
        state["messages"].append(AIMessage(content=ai_response))
        SESSIONS[session_id] = state
        
        return {
            "sessionId": session_id,
            "openingMessage": ai_response,
            "audio": audio_b64 if audio_b64 else ""
        }
    except Exception as e:
        print(f"🚨 Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in SESSIONS:
        await websocket.send_text(json.dumps({"type": "error", "message": "Session not found"}))
        await websocket.close()
        return
        
    state = SESSIONS[session_id]
    
    from vad_engine import VADEngine
    from stt_engine import STTEngine
    try:
        vad_engine = VADEngine()
        stt_engine = STTEngine()
    except Exception as e:
        print(f"Failed to initialize engines: {e}")
        await websocket.close()
        return
    
    audio_buffer = bytearray()
    silence_frames = 0
    is_ai_speaking = False
    current_ai_task = None
    
    async def handle_sentence(sentence_text: str):
        # Generate audio and send
        audio_b64 = await text_to_speech_bytes(sentence_text)
        await websocket.send_text(json.dumps({
            "type": "ai",
            "message": sentence_text,
            "audio": audio_b64 if audio_b64 else ""
        }))
        
    state["handle_sentence_callback"] = handle_sentence
    
    try:
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                
                # Check VAD (in thread to avoid blocking loop)
                is_speech = await asyncio.to_thread(vad_engine.is_speech, chunk)
                
                if is_speech:
                    silence_frames = 0
                    if is_ai_speaking and current_ai_task:
                        # BARGE-IN DETECTED
                        print(f"🛑 Barge-in detected [{session_id}]")
                        current_ai_task.cancel()
                        current_ai_task = None
                        is_ai_speaking = False
                        await websocket.send_text(json.dumps({"type": "interrupted"}))
                        audio_buffer.clear()
                else:
                    silence_frames += 1
                    
                # If ~800ms of silence (assuming ~3-4 frames of 250ms) and we have audio
                if silence_frames >= 4 and len(audio_buffer) > 16000: 
                    # End of utterance
                    audio_bytes = bytes(audio_buffer)
                    audio_buffer.clear()
                    silence_frames = 0
                    
                    user_text = await asyncio.to_thread(stt_engine.transcribe_audio_bytes, audio_bytes)
                    if user_text.strip():
                        print(f"👤 User [{session_id}]: {user_text}")
                        state["messages"].append(HumanMessage(content=user_text))
                        await websocket.send_text(json.dumps({"type": "user_text", "text": user_text}))
                        
                        # Trigger graph logic for AI response
                        is_ai_speaking = True
                        
                        async def run_ai():
                            nonlocal is_ai_speaking
                            try:
                                new_state = await app_graph.ainvoke(state)
                                state["messages"] = new_state["messages"]
                                SESSIONS[session_id] = state
                            except asyncio.CancelledError:
                                print("AI Generation Cancelled")
                            except Exception as e:
                                print(f"Graph Error: {e}")
                            finally:
                                is_ai_speaking = False
                                
                        current_ai_task = asyncio.create_task(run_ai())
                        
            elif "text" in message:
                raw_data = message["text"]
                try:
                    data = json.loads(raw_data)
                    if isinstance(data, dict):
                        if data.get("type") == "system" and data.get("event") == "user_silent":
                            print(f"🔇 SILENCE TIMEOUT [{session_id}]")
                            user_text = "[SYSTEM EVENT: User has been completely silent for 30 seconds. Ask them if they are still there or if they need a moment, gently.]"
                            state["messages"].append(HumanMessage(content=user_text))
                            
                            is_ai_speaking = True
                            async def run_ai_timeout():
                                nonlocal is_ai_speaking
                                try:
                                    new_state = await app_graph.ainvoke(state)
                                    state["messages"] = new_state["messages"]
                                    SESSIONS[session_id] = state
                                except asyncio.CancelledError:
                                    pass
                                finally:
                                    is_ai_speaking = False
                                    
                            current_ai_task = asyncio.create_task(run_ai_timeout())
                except json.JSONDecodeError:
                    pass
                    
    except WebSocketDisconnect:
        print(f"🔌 Disconnected {session_id}")
    except Exception as e:
        print(f"🚨 Critical Error {session_id}: {e}")