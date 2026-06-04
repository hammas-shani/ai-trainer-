import subprocess
import base64
import os
import uuid
import re
import sys

def text_to_speech_bytes(text: str) -> str:
    try:
        # Action tags remove karega
        cleaned = re.sub(r'\*.*?\*|\[.*?\]', '', text).strip()
        if not cleaned:
            cleaned = "I am listening."

        filename = f"audio_{uuid.uuid4().hex}.mp3"
        
        # Subprocess execution
        command = [
            sys.executable, "-m", "edge_tts",
            "--voice", "en-US-ChristopherNeural",
            "--rate", "+5%",
            "--text", cleaned,
            "--write-media", filename
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print("TTS ERROR:", result.stderr)
            return ""

        with open(filename, "rb") as f:
            audio = f.read()

        if os.path.exists(filename):
            os.remove(filename)

        return base64.b64encode(audio).decode()

    except Exception as e:
        print("TTS ERROR:", e)
        return ""