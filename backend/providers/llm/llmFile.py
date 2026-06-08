import os
import json

from providers.llm.base import LLMProvider
from backend.core.entity import g
from ollama import AsyncClient
from fastapi import HTTPException

# Is given the transcription of the audio file and returns a summary of the session. 
# This is used to provide a summary of the session to the user as well as to provide a identify entities.
class OllamaProvider(LLMProvider):
    
    # Initializes the Ollama model based on the specified URL and model name in the environment variables.
    def __init__(self):
        self.model_url = os.environ.get("OLLAMA_URL")
        self.model_size = os.environ.get("OLLAMA_MODEL", "llama3")
    
    # Given a transcription of the session, return a concise summary of the session, highlighting the key points.
    async def llm_session_summary(self, transcription: str) -> str:
        response = ""
        async for part in await AsyncClient(host=self.model_url).chat(model=self.model_size, messages=[{'role': 'user', 'content': f"Summarize the following transcript in a concise manner, highlighting the key points, characters, and main topics discussed. The summary should be clear and easy to understand, providing an overview of the session without going into excessive detail.\n\n{transcription}"}
], stream=True):
            response += part['message']['content']
        return response

    # Given a transcription of the session, extract all named entities and objects (people, places, organizations, items) from the transcript.
    # Returns that list of entities.
    async def llm_entity_extraction(self, transcription: str) -> list[dict]:
        response = ""
        async for part in await AsyncClient(host=self.model_url).chat(model=self.model_size, messages=[{'role': 'user', 'content': f"Extract all named entities and objects (people, places, organizations, items) from the following transcript. Return ONLY a JSON array of objects, each with 'name', 'type' (character, location, faction, item, or event), and 'description' fields. No other text.\n\n{transcription}"}
], stream=True):
            response += part['message']['content']
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse entity extraction response as JSON.")
        
    # Takes a given entity data and a new summary of the character and requests Ollam to create a new summary for the character.
    async def llm_entity_merging(self, entity_data: str, new_summary:str) -> str:
        response = ""
        async for part in await AsyncClient(host=self.model_url).chat(model=self.model_size, messages=[{'role': 'user', 'content': f"I am providing you data on an existing entity from a DND campaign database and I am also providing you with a new summary of the character's action in the most recent session. Create a new summary using both of these sets of data. This new summary should be all encompassing of the old data and the new data. No other text.\n\n Existing entity data: {entity_data}\n\n New entity data: {new_summary}"}], stream=True):
            response += part['message']['content']
        return response
    
