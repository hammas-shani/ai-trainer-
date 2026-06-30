import torch
import numpy as np

class VADEngine:
    def __init__(self):
        # Load Silero VAD from torch hub
        self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                          model='silero_vad',
                                          force_reload=False,
                                          onnx=False)
        (self.get_speech_timestamps,
         self.save_audio,
         self.read_audio,
         self.VADIterator,
         self.collect_chunks) = utils
         
        self.sample_rate = 16000

    def is_speech(self, audio_chunk_bytes: bytes, threshold: float = 0.5) -> bool:
        """
        Takes raw 16kHz PCM audio bytes, converts to float32 tensor,
        and returns True if speech probability > threshold.
        """
        if not audio_chunk_bytes:
            return False
            
        # Convert bytes to numpy array (int16)
        try:
            audio_np = np.frombuffer(audio_chunk_bytes, dtype=np.int16)
        except Exception:
            return False
            
        # Normalize to float32
        audio_float32 = audio_np.astype(np.float32) / 32768.0
        
        # Ensure we have at least 512 samples (min required for silero)
        if len(audio_float32) < 512:
            pad_len = 512 - len(audio_float32)
            audio_float32 = np.pad(audio_float32, (0, pad_len))
            
        tensor = torch.from_numpy(audio_float32)
        
        # Get speech probability
        with torch.no_grad():
            speech_prob = self.model(tensor, self.sample_rate).item()
            
        return speech_prob > threshold
