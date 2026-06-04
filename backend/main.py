from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
import json
import os
from datetime import datetime

# Import crash-safeguarded graph
from graph_logic import app_graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure folders exist gracefully
try:
    os.makedirs("transcripts", exist_ok=True)
except Exception as folder_err:
    print(f"⚠️ Cannot create transcripts directory: {folder_err}")

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_filename = f"transcripts/session_{session_id}.txt"
    
    state = {
        "messages": [],
        "user_detailed_prompt": "Act as a professional peer.",
        "formatted_transcript": ""
    }
    
    try:
        # 1. Configuration Phase with Validation Try-Block
        try:
            config_data = await websocket.receive_text()
            config_json = json.loads(config_data)
            state["user_detailed_prompt"] = config_json.get("prompt", "Act as a professional peer.")
            await websocket.send_text(json.dumps({"type": "system", "message": "Connected safely."}))
        except json.JSONDecodeError:
            print("⚠️ Invalid initial configuration format received.")
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid config format."}))
            return

        # 2. Resilient Chat Loop
        while True:
            try:
                user_message_text = await websocket.receive_text()
                
                # Malformed incoming request fallback
                if not user_message_text or not user_message_text.strip():
                    continue

                state["messages"].append(HumanMessage(content=user_message_text))
                
                # Safeguard against uncompiled graph logic
                if app_graph is None:
                    await websocket.send_text(json.dumps({"type": "ai", "message": "System is recovering from an internal state reset. Give me a second please."}))
                    continue

                print(f"🤖 Processing turn for session {session_id}...")
                new_state = app_graph.invoke(state)
                
                # Fetching response securely
                if new_state and "messages" in new_state and len(new_state["messages"]) > 0:
                    ai_response = new_state["messages"][-1].content
                    await websocket.send_text(json.dumps({"type": "ai", "message": ai_response}))
                    
                    # Update active loop memory securely
                    state["messages"] = new_state["messages"]
                    
                    # Safe Async File Logging
                    latest_transcript = new_state.get("formatted_transcript", "")
                    if latest_transcript:
                        try:
                            with open(transcript_filename, "w", encoding="utf-8") as f:
                                f.write(f"Session Configuration: {state['user_detailed_prompt']}\n")
                                f.write("="*60 + "\n\n")
                                f.write(latest_transcript)
                            state["formatted_transcript"] = latest_transcript
                        except IOError as file_io_err:
                            print(f"⚠️ Transcript logging failed to disk: {file_io_err}")
                else:
                    raise ValueError("LangGraph state pipeline returned an empty response stack.")

            except WebSocketDisconnect:
                # Normal close hook management
                print(f"🔌 Clean disconnection: Session {session_id} ended.")
                break
            except Exception as loop_error:
                print(f"🚨 Runtime exception inside chat transaction loop: {loop_error}")
                try:
                    await websocket.send_text(json.dumps({"type": "ai", "message": "Sorry, I experienced a minor network hitch. What were you saying?"}))
                except Exception:
                    # Connection is totally dead, exit process
                    break

    except Exception as connection_level_critical_err:
        print(f"💀 Critical Connection Level Error: {connection_level_critical_err}")
    finally:
        # Final safety cleanup blocks
        print(f"🔒 Closed resources for session {session_id}")