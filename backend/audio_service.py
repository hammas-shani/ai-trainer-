from gtts import gTTS
import io
import base64

def text_to_speech_bytes(text: str) -> str:
    """
    Converts text to safe, high-quality audio bytes using a 100% thread-safe synchronous buffer.
    Completely eliminates async event loop collisions.
    """
    try:
        # Text se expressions saaf karein
        cleaned_text = text.replace("*laughs*", "").replace("*chuckles*", "").strip()
        if not cleaned_text:
            cleaned_text = "I am listening, please go ahead."

        print(f"🎙️ Generating Safe Audio Buffer for: '{cleaned_text[:40]}...'")

        # Memory buffer initialize karein
        fp = io.BytesIO()
        
        # Google TTS engine (English - US Accent)
        tts = gTTS(text=cleaned_text, lang='en', tld='com', slow=false)
        tts.write_to_fp(fp)
        
        # Seek to start of the bytes buffer
        fp.seek(0)
        audio_data = fp.read()

        if not audio_data:
            print("🚨 Critical: Audio buffer string is empty!")
            return ""

        # Encode to clean Base64 transfer string
        base64_audio = base64.b64encode(audio_data).decode("utf-8")
        return base64_audio

    except Exception as e:
        print(f"🚨 Synchronous TTS Service Failed: {e}")
        return ""