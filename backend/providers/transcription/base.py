from abc import ABC, abstractmethod

# Base class for transcription providers. Defines the interface that all transcription providers must implement.
class TranscriptionProvider(ABC):
    
    # Abstract method to transcribe an audio file. Must be implemented by subclasses.
    @abstractmethod
    def file_transcribe(self, audio_file_path: str) -> str:
        ...