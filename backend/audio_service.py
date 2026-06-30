import asyncio
import edge_tts
import base64
import uuid
import os
from config import config

async def text_to_speech_bytes(text: str) -> str:
    """
    Uses edge-tts Python API directly to avoid subprocess overhead.
    Returns base64 encoded mp3 string.
    """
    try:
        # Clean text
        cleaned = text.replace("*", "").replace("[", "").replace("]", "").strip()
        if not cleaned:
            cleaned = "I am listening."

        filename = f"audio_{uuid.uuid4().hex}.mp3"
        
        communicate = edge_tts.Communicate(cleaned, config.TTS_VOICE, rate=config.TTS_RATE)
        
        await communicate.save(filename)
        
        if not os.path.exists(filename):
            return ""
            
        with open(filename, "rb") as f:
            audio_data = f.read()
            
        os.remove(filename)
        
        return base64.b64encode(audio_data).decode()
        
    except Exception as e:
        print(f"🚨 TTS ERROR: {e}")
        return ""