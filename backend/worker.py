import asyncio
import uuid

from providers.llm.llmFile import OllamaProvider
from providers.transcription.transcriptionFile import WhisperTranscriptionProvider
from celery import Celery
from core.models import CampaignSession
from sqlalchemy import select, delete, update
from core.database import async_session_maker

# Celery configuration for the worker.
# Provided by Celery Documentation: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#configuring-celery
celery_app = Celery(
    'worker',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

# This function processes the audio file for a given session ID.
async def process_audio_file(session_id: str):

    # Create an asynchronous session with the database to fetch and update the campaign session data.
    async with async_session_maker() as session:

        # Fetch the campaign session data from the database using the provided session ID.
        stmt = select(CampaignSession).where(CampaignSession.id == session_id)
        result = await session.execute(stmt)
        campaign_session_data =  result.scalars().first()

        # Update the job status to "Processing" before starting the processing of the audio file.
        campaign_session_data.job_status = "Processing"
        await session.commit()

        # Process the audio file using the Whisper transcription provider and 
        # update the campaign session data with the transcript and summary.
        try:
            
            # Use the Whisper transcription provider to transcribe the audio file and update the campaign session data with the transcript.
            whisper = WhisperTranscriptionProvider()
            transcription = await whisper.file_transcribe(campaign_session_data.audio_path)

            campaign_session_data.transcript = transcription

            # Use the Ollama LLM to generate a summary of the transcription and update the campaign session data with the summary.
            ollama = OllamaProvider()
            summary = await ollama.llm_session_summary(transcription)

            # TODO: Implement entity extraction using Ollama LLM and update the campaign session data with the extracted entities.
            #entities = await ollama.llm_entity_extraction(transcription)

            campaign_session_data.summary = summary
            campaign_session_data.job_status = "Completed"

            session.add(campaign_session_data)
            await session.commit()
            await session.refresh(campaign_session_data)

            return campaign_session_data
    
        # If any exception occurs during the processing of the audio file, update the campaign session data with a "Failed" status and raise the exception.
        except Exception as e:
            campaign_session_data.job_status = "Failed"
            await session.commit()
            raise e

# Celery task that calls the process_audio_file function with the provided session ID.
@celery_app.task
def process_audio_task(session_id: uuid.UUID):
    asyncio.run(process_audio_file(session_id))
    