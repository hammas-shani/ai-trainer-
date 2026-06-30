import os

class Config:
    # LLM Settings
    MODEL_NAME = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.7
    MAX_TOKENS = 4000
    
    # Audio Settings
    TTS_VOICE = "en-US-ChristopherNeural"
    TTS_RATE = "+5%"
    
    # Conversation Health
    MAX_AI_SENTENCES = 3
    MIN_CONFIDENCE_THRESHOLD = 0.5
    SILENCE_TIMEOUT_SEC = 10
    
    # Stages
    STAGES_INTERVIEW = [
        "Greeting", "Ice Breaking", "Background Discovery", 
        "Technical Discussion", "Behavioral Discussion", "Summary", "Closing"
    ]
    STAGES_CLIENT_CALL = [
        "Greeting", "Ice Breaking", "Background Discovery",
        "Project Deep Dive", "Negotiation", "Summary", "Closing"
    ]
    
config = Config()
