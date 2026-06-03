import asyncio
import websockets
import json
import pyttsx3
import speech_recognition as sr

# -----------------------------------------
# Voice Engine Setup
# -----------------------------------------
engine = pyttsx3.init()
engine.setProperty('rate', 160)  
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) 

def speak(text):
    """AI ka text audio mein convert kar ke play karta hai"""
    engine.say(text)
    engine.runAndWait()

def listen():
    """User ki awaz microphone se sun kar text mein convert karta hai"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎙️ Your turn to speak... (Listen carefully to AI first)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
    
    try:
        print("⏳ Processing speech...")
        text = recognizer.recognize_google(audio)
        print(f"👤 You said: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Sorry, clear awaz nahi aayi. Dobara bolein.")
        return ""
    except sr.RequestError as e:
        print(f"❌ Network error: {e}")
        return ""

# -----------------------------------------
# WebSocket Client Logic
# -----------------------------------------
async def chat_session():
    uri = "ws://127.0.0.1:8000/ws/chat"
    
    print("🔄 Connecting to AI Server...")
    async with websockets.connect(uri) as websocket:
        
        # 1. Agent Configuration
        print("="*50)
        prompt = input("📝 Enter AI Role (e.g., You are a client. Interview me): ")
        print("="*50)
        
        await websocket.send(json.dumps({"prompt": prompt}))
        
        # Server ready message
        ready_msg = await websocket.recv()
        print(f"✅ {json.loads(ready_msg)['message']}")

        # -------------------------------------------------------------
        # NAYA LOGIC: AI KO PEHLE BOLNE PAR MAJBOOR KARNA
        # -------------------------------------------------------------
        print("\n⏳ Waiting for AI to start the meeting...")
        # Hum AI ko ek hidden trigger message bhej rahe hain taake woh pehle boley
        await websocket.send("Hello, I have joined the meeting. Please introduce yourself and start the conversation as per your role.")
        
        # AI ka pehla jawab receive karein aur sunayein
        first_response_data = await websocket.recv()
        first_response_json = json.loads(first_response_data)
        
        if first_response_json.get("type") == "ai":
            ai_first_text = first_response_json["message"]
            print(f"\n🤖 AI: {ai_first_text}\n")
            await asyncio.to_thread(speak, ai_first_text)
        # -------------------------------------------------------------

        # 2. Live Call Loop (Ab natural 2-way conversation hogi)
        while True:
            # Ab user AI ke sawal ka jawab dega
            user_text = await asyncio.to_thread(listen)
            
            if not user_text:
                continue
            if user_text.lower() in ['exit', 'quit', 'stop', 'bye']:
                print("Ending call...")
                break

            # Text backend ko bhejein
            await websocket.send(user_text)

            # AI ka agla cross-question ya reply wait karein
            print("🧠 AI is thinking...")
            response_data = await websocket.recv()
            response_json = json.loads(response_data)
            
            if response_json.get("type") == "ai":
                ai_text = response_json["message"]
                print(f"\n🤖 AI: {ai_text}\n")
                
                # AI ka response audio mein sunayein
                await asyncio.to_thread(speak, ai_text)

if __name__ == "__main__":
    asyncio.run(chat_session())