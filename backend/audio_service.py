from gtts import gTTS
import io
import base64

def text_to_speech_bytes(text: str) -> str:
    try:
        cleaned_text = text.replace("*laughs*", "").replace("*chuckles*", "").strip()
        if not cleaned_text:
            cleaned_text = "I am listening."

        fp = io.BytesIO()
        tts = gTTS(text=cleaned_text, lang='en', slow=False)
        tts.write_to_fp(fp)
        
        fp.seek(0)
        audio_data = fp.read()

        if not audio_data:
            return ""

        return base64.b64encode(audio_data).decode("utf-8")
    except Exception as e:
        print(f"🚨 TTS Error: {e}")
        return ""