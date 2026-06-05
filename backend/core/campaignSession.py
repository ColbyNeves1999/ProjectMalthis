import uuid
import os
import aiofiles

from core.campaign import check_campaign_ownership
from core.database import SessionDep
from core.models import jobStatusEnum, CampaignSession
from pydantic import BaseModel
from sqlalchemy import select, delete
from fastapi import HTTPException, UploadFile
from datetime import datetime
from worker import process_audio_task

# Handles the campaign session creation process.
class CampaignSessionCreate(BaseModel):
    session_name: str
    session_number: int

# Handles the campaign session read process and returns the information.
class CampaignSessionRead(BaseModel):

    id: uuid.UUID
    user_id: uuid.UUID
    campaign_id: uuid.UUID
    session_name: str
    audio_path: str | None
    job_status: jobStatusEnum
    created_at: datetime
    summary: str | None
    transcript: str | None
    session_number: int

    class Config:
        from_attributes = True

# Handles the campaign session update process.
class CampaignSessionUpdate(BaseModel):
    session_name: str | None
    summary: str | None

# Acceptable file types for session uploads, as assumed by Whisper AI.
ALLOWED_FILE_TYPES = {"audio/mp3", "audio/wav", "audio/flac", "audio/m4a", "audio/ogg", "audio/opus", "audio/webm", "audio/mpeg"}

#################################################################################################
# Session Functions

# Creates a session for a campaign via an uploaded file.
async def create_session(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, file: UploadFile, session_name: str, session_number: int) -> CampaignSessionRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Supported types are: mp3, wav, flac, m4a, ogg, opus, webm, mpeg.")

    temp = await get_session_by_number(session, user_id, campaign_id, session_number)
    if temp is not None:
        raise HTTPException(status_code=400, detail="Session of this number already exists for this campaign.")

    db_campaign_session = CampaignSession(session_name=session_name)
    db_campaign_session.user_id = user_id
    db_campaign_session.campaign_id = campaign_id
    db_campaign_session.session_number = session_number

    session.add(db_campaign_session)
    await session.commit()
    await session.refresh(db_campaign_session)

    # Save the uploaded file to the server with a unique name based on the session ID, and update the session with the file path.
    original_filename = os.path.splitext(file.filename)[1]
    audio_filename = f"{db_campaign_session.id}{original_filename}"
    db_campaign_session.audio_path = f"/app/audio/{audio_filename}"
    async with aiofiles.open(db_campaign_session.audio_path, "wb") as f:
        await f.write(await file.read())

    session.add(db_campaign_session)
    await session.commit()
    await session.refresh(db_campaign_session)

    # Celery task to process the audio file and update the session with the transcript and summary.
    process_audio_task.delay(str(db_campaign_session.id))

    return db_campaign_session

# Gets a session for a campaign
async def get_one_session(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, session_id: uuid.UUID) -> CampaignSessionRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = select(CampaignSession).where(CampaignSession.campaign_id == campaign_id, CampaignSession.id == session_id)
    result = await session.execute(stmt)
    db_campaign_session =  result.scalars().first()

    if not db_campaign_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return db_campaign_session

# Gets all sessions for a campaign
async def get_sessions(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID) -> list[CampaignSessionRead]:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = select(CampaignSession).where(CampaignSession.campaign_id == campaign_id)
    result = await session.execute(stmt)
    db_campaign_sessions =  result.scalars().all()

    return db_campaign_sessions

# Gets a session for a campaign via the session number, which is unique within a campaign.
async def get_session_by_number(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, session_number: int) -> CampaignSessionRead | None:
    
    await check_campaign_ownership(session, user_id, campaign_id)
    
    stmt = select(CampaignSession).where(CampaignSession.campaign_id == campaign_id, CampaignSession.session_number == session_number)
    result = await session.execute(stmt)
    db_campaign_session =  result.scalars().first()

    return db_campaign_session

# Updates a session for a campaign
async def update_session(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, session_id: uuid.UUID, session_update: CampaignSessionUpdate) -> CampaignSessionRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    updating_session = await get_one_session(session, user_id, campaign_id, session_id)

    if session_update.session_name is not None:
        updating_session.session_name = session_update.session_name

    if session_update.summary is not None:
        updating_session.summary = session_update.summary

    session.add(updating_session)
    await session.commit()
    await session.refresh(updating_session)

    return updating_session

# Deletes a session for a campaign
async def delete_session(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, session_id: uuid.UUID) -> None:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    temp = await get_one_session(session, user_id, campaign_id, session_id)
    
    if temp is not None:
        try:
            os.remove(temp.audio_path)
        except Exception as e:
            raise HTTPException(status_code=404, detail="An error occurred while trying to delete the session's audio file.")

    stmt = delete(CampaignSession).where(CampaignSession.campaign_id == campaign_id, CampaignSession.id == session_id)
    result = await session.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    await session.commit()