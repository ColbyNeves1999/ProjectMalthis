from abc import ABC, abstractmethod

# This file defines the base class for LLM providers, which can be extended to implement specific LLM functionalities.
# Intended so that we can easily swap out LLM providers in the future without changing the core logic of the application.
class LLMProvider(ABC):
    
    # Abstract method to generate a session summary from a given transcript. Must be implemented by any subclass.
    @abstractmethod
    def llm_session_summary(self, transcript: str) -> str:
        ...

    # Abstract method to extract entities from a given transcript. Must be implemented by any subclass.
    @abstractmethod
    def llm_entity_extraction(self, transcript: str) -> list[dict]:
        ...

    # Abstract method to help merge entities. Must be implemented by any subclass.
    @abstractmethod
    def llm_entity_merging(self, entity_data: str, new_summary:str) -> str:
        ...
    