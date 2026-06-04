from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
from langchain_core.messages import HumanMessage # Naya Import
from graph_logic import app_graph
from audio_service import text_to_speech_bytes # Make sure file is audio_service.py

app = FastAPI()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    state = {
        "messages": [],
        "user_detailed_prompt": "Act as a professional interviewer."
    }
    
    try:
        while True:
            raw_data = await websocket.receive_text()
            if not raw_data: continue
            
            try:
                data = json.loads(raw_data)
                if isinstance(data, dict):
                    if data.get("prompt"):
                        state["user_detailed_prompt"] = data["prompt"]
                        continue
                    if data.get("type") == "stream":
                        continue # Ignore stream payload for AI generation
                    if data.get("type") == "final":
                        user_message = data.get("text", "").strip()
                    else:
                        user_message = raw_data.strip()
                else:
                    user_message = raw_data.strip()
            except json.JSONDecodeError:
                user_message = raw_data.strip()

            if not user_message:
                continue

            print(f"👤 User: {user_message}")
            
            # 🚀 THE FIX: Directly append as HumanMessage object
            state["messages"].append(HumanMessage(content=user_message))
            
            new_state = app_graph.invoke(state)
            
            # 🚀 THE FIX: Safely extract response whether it's dict or object
            ai_response_obj = new_state["messages"][-1]
            if isinstance(ai_response_obj, dict):
                ai_response = ai_response_obj.get("content", "")
            else:
                ai_response = ai_response_obj.content
                
            print(f"🤖 AI: {ai_response}")
            
            audio_b64 = text_to_speech_bytes(ai_response)

            await websocket.send_text(json.dumps({
                "type": "ai",
                "message": ai_response,
                "audio": audio_b64
            }))
            
    except WebSocketDisconnect:
        print("🔌 Disconnected")
    except Exception as e:
        print(f"🚨 Critical Error: {e}")
        import traceback
        traceback.print_exc()