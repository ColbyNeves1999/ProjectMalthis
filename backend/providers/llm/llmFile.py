import os
import json
import re

from providers.llm.base import LLMProvider
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
        response = await AsyncClient(host=self.model_url).chat(
        model=self.model_size,
        messages=[{'role': 'user', 'content': f"""You are a Dungeons and Dragons session analyst. Extract all named entities from the following transcript. Return ONLY a valid JSON array. Each object must have exactly these three fields: - "name": the entity's name as a string - "type": must be exactly one of these values: "Player", "Player Character", "NPC", "Monster", "Location", "Item" - "description": a 1-2 sentence description of the entity based on context from the transcript. Never leave this empty. Rules: - Real player names (people talking) should be type "Player" - Character names should be type "Player Character" or "NPC" depending on context - Return ONLY the JSON array, no other text, no markdown, no explanation Transcript: {transcription}"""}],
        format='json'
        )
        
        raw = response['message']['content']
        print(f"Raw entity response: {raw}")

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for val in parsed.values():
                    if isinstance(val, list):
                        return val
                return [parsed]
            return []
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Raw response was:\n{raw}")
            return []
            

    # Takes a given entity data and a new summary of the character and requests Ollam to create a new summary for the character.
    async def llm_entity_merging(self, entity_data: str, new_summary:str) -> str:
        response = ""
        async for part in await AsyncClient(host=self.model_url).chat(model=self.model_size, messages=[{'role': 'user', 'content': f"I am providing you data on an existing entity from a DND campaign database and I am also providing you with a new summary of the character's action in the most recent session. Create a new summary using both of these sets of data. This new summary should be all encompassing of the old data and the new data. No other text.\n\n Existing entity data: {entity_data}\n\n New entity data: {new_summary}"}], stream=True):
            response += part['message']['content']
        return response
    
