import uuid
import os
import asyncio

from providers.llm.llmFile import OllamaProvider
from providers.transcription.transcriptionFile import WhisperTranscriptionProvider
from celery import Celery
from core.models import CampaignSession, Entities, jobStatusEnum
from core.entity import EntityCreate
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
# Convert async URL to sync URL for the worker
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(engine)

# Celery configuration for the worker.
# Provided by Celery Documentation: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#configuring-celery
celery_app = Celery(
    'worker',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

# This function processes the audio file for a given session ID.
def process_audio_file(session_id: str):

    engine = create_engine(SYNC_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    # Create an asynchronous session with the database to fetch and update the campaign session data.
    with SessionLocal() as session:

        # Fetch the campaign session data from the database using the provided session ID.
        stmt = select(CampaignSession).where(CampaignSession.id == session_id)
        result = session.execute(stmt)
        campaign_session_data =  result.scalars().first()

        # Update the job status to "Processing" before starting the processing of the audio file.
        campaign_session_data.job_status = jobStatusEnum.Processing
        session.commit()

        campaign_session_data.job_status = jobStatusEnum.Processing
        session.commit()
        session.refresh(campaign_session_data)

        # Process the audio file using the Whisper transcription provider and 
        # update the campaign session data with the transcript and summary.
        try:
            
            # Use the Whisper transcription provider to transcribe the audio file and update the campaign session data with the transcript.
            whisper = WhisperTranscriptionProvider()
            transcription = asyncio.run(whisper.file_transcribe(campaign_session_data.audio_path))

            campaign_session_data.transcript = transcription

            # Use the Ollama LLM to generate a summary of the transcription and update the campaign session data with the summary.
            ollama = OllamaProvider()
            summary = asyncio.run(ollama.llm_session_summary(transcription))

            # TODO: Implement entity extraction using Ollama LLM and update the campaign session data with the extracted entities.
            entities = asyncio.run(ollama.llm_entity_extraction(transcription))

            print("Here are your entities:", sep="\n")
            for entity in entities:
                print(entity, sep="\n")

            campaign_session_data.summary = summary
            campaign_session_data.job_status = jobStatusEnum.Needs_Review

            session.add(campaign_session_data)
            session.commit()
            session.refresh(campaign_session_data)

            return campaign_session_data
    
        # If any exception occurs during the processing of the audio file, update the campaign session data with a "Failed" status and raise the exception.
        except Exception as e:
            campaign_session_data.job_status = jobStatusEnum.Failed
            session.commit()
            raise e

# This function does a merge of an entity and incoming data.
def merge_with_existing_entity(entity_id: str, merge_data: EntityCreate):

    engine = create_engine(SYNC_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    # Create an asynchronous session with the database to fetch and update the entity data.
    with SessionLocal() as session:

        # Fetch the entity data from the database using the provided entity ID.
        stmt = select(Entities).where(Entities.id == uuid.UUID(entity_id))
        result = session.execute(stmt)
        entity_data =  result.scalars().first()

        # Requests Ollama to merge the existing entity description with the new data.
        try:

            # Use the Ollama LLM to merge and generate data for the existing character.
            ollama = OllamaProvider()
            summary = asyncio.run(ollama.llm_entity_merging(entity_data.description, merge_data))

            entity_data.description = summary

            session.add(entity_data)
            session.commit()
            session.refresh(entity_data)

            return entity_data
    
        # If any exception occurs during the merging of the entity data, raise the exception.
        except Exception as e:
            session.commit()
            raise e

# Celery task that calls the process_audio_file function with the provided session ID.
@celery_app.task
def process_audio_task(session_id: uuid.UUID):
    process_audio_file(session_id)

# Celery task that calls the process_audio_file function with the provided session ID.
@celery_app.task
def process_entity_merger(entity_id: str, merge_data: str):
    merge_with_existing_entity(entity_id, merge_data)
    