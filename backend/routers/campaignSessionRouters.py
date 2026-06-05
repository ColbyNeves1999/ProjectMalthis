import uuid

from core.models import User
from core.campaignSession import CampaignSessionRead, CampaignSessionUpdate, create_session, get_one_session, get_session_by_number, get_sessions, update_session, delete_session
from core.database import SessionDep
from routers.usersRouters import current_active_user
from fastapi import APIRouter, Depends, UploadFile, Form

router = APIRouter()

#################################################################################################
# Post Endpoints

# Endpoint to create a new campaign
# user_id and role are passed in the request body via FastAPI built in functions
@router.post("/campaigns/{campaign_id}/sessions/")
async def create_campaign_session(campaign_id: uuid.UUID, file: UploadFile, session: SessionDep, session_name: str = Form(...), session_number: int = Form(...), current_user: User = Depends(current_active_user)) -> CampaignSessionRead:
    
    return await create_session(session, current_user.id, campaign_id, file, session_name, session_number)

#################################################################################################
# Get Endpoints

# Endpoint to get a single session for a campaign via its session number
@router.get("/campaigns/{campaign_id}/sessions/sessionNumber/{session_number}/")
async def get_campaign_session(session: SessionDep, campaign_id: uuid.UUID, session_number: int, current_user: User = Depends(current_active_user)) -> CampaignSessionRead | None:
    return await get_session_by_number(session, current_user.id, campaign_id, session_number)

# Endpoint to get a single session for a campaign via its session id
@router.get("/campaigns/{campaign_id}/sessions/sessionID/{session_id}/")
async def get_campaign_session_by_id(session: SessionDep, campaign_id: uuid.UUID, session_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> CampaignSessionRead | None:
    return await get_one_session(session, current_user.id, campaign_id, session_id)

# Endpoint to list all sessions for a campaign
@router.get("/campaigns/{campaign_id}/sessions/")
async def list_campaign_sessions(session: SessionDep, campaign_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> list[CampaignSessionRead]:
    return await get_sessions(session, current_user.id, campaign_id)

#################################################################################################
# Patch Endpoints

# Endpoint to update a session for a campaign
@router.patch("/campaigns/{campaign_id}/sessions/session/{session_id}/")
async def update_campaign_session(session: SessionDep, campaign_id: uuid.UUID, session_id: uuid.UUID, session_update: CampaignSessionUpdate, current_user: User = Depends(current_active_user)) -> CampaignSessionRead:
    return await update_session(session, current_user.id, campaign_id, session_id, session_update)

#################################################################################################
# Delete Endpoints

# Endpoint to delete a session for a campaign
@router.delete("/campaigns/{campaign_id}/sessions/session/{session_id}/")
async def delete_campaign_session(session: SessionDep, campaign_id: uuid.UUID, session_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> None:
    await delete_session(session, current_user.id, campaign_id, session_id)