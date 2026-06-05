import whisper
import os
import asyncio

from providers.transcription.base import TranscriptionProvider

# Grabs the transcript of an audio file using the Whisper AI model.
class WhisperTranscriptionProvider(TranscriptionProvider):
    
    # Initializes the Whisper model based on the specified size in the environment variable.
    def __init__(self):
        model_size = os.environ.get("WHISPER_MODEL", "base")
        self.model = whisper.load_model(model_size)

    # Transcribes an audio file and returns the text.
    async def file_transcribe(self, audio_file_path: str) -> str:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.model.transcribe, audio_file_path)
        return result["text"]
