from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
import json
import os
from datetime import datetime
from graph_logic import app_graph

# 👇 YEH LINE LAZMI HAI: TTS service import karein
from audio_service import text_to_speech_bytes 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("transcripts", exist_ok=True)

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    state = {
        "messages": [],
        "user_detailed_prompt": "Act as a professional.",
        "formatted_transcript": ""
    }
    
    try:
        config_data = await websocket.receive_text()
        config_json = json.loads(config_data)
        state["user_detailed_prompt"] = config_json.get("prompt", "Act as a professional.")
        await websocket.send_text(json.dumps({"type": "system", "message": "Connected safely."}))

        while True:
            user_message_text = await websocket.receive_text()
            if not user_message_text or not user_message_text.strip():
                continue

            state["messages"].append(HumanMessage(content=user_message_text))
            
            print(f"🤖 AI is thinking...")
            new_state = app_graph.invoke(state)
            
            if new_state and "messages" in new_state and len(new_state["messages"]) > 0:
                ai_response_text = new_state["messages"][-1].content
                
                # 👇 YEH BLOCK AWAZ GENERATE KARTA HAI AUR BHEJTA HAI
                print("🔊 Generating Audio Bytes...")
                audio_b64 = text_to_speech_bytes(ai_response_text)
                
                payload = {
                    "type": "ai",
                    "message": ai_response_text,
                    "audio": audio_b64  # Base64 string frontend ko jayegi
                }
                await websocket.send_text(json.dumps(payload))
                
                state["messages"] = new_state["messages"]
                
    except WebSocketDisconnect:
        print(f"🔌 Disconnected.")
    except Exception as e:
        print(f"🚨 Error: {e}")