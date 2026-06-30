import os
import io
import tempfile
from groq import Groq
from pydub import AudioSegment

class STTEngine:
    def __init__(self):
        self.client = Groq() # assumes GROQ_API_KEY is in env
        
    def transcribe_audio_bytes(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        if not audio_bytes:
            return ""
            
        try:
            # We assume the incoming bytes are raw 16-bit PCM mono
            audio_segment = AudioSegment(
                data=audio_bytes,
                sample_width=2, # 16-bit
                frame_rate=sample_rate,
                channels=1
            )
            
            # Export to a temporary wav file (in memory or temp file)
            # Groq API requires a file-like object with a filename
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_filename = f.name
                audio_segment.export(temp_filename, format="wav")
                
            # Call Groq Whisper
            with open(temp_filename, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(temp_filename, file.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )
                
            os.remove(temp_filename)
            return transcription.strip()
            
        except Exception as e:
            print(f"STT Error: {e}")
            return ""
