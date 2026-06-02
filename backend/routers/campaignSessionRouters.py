import uuid

from core.models import User, CampaignMember, Campaign, CampaignSession, jobStatusEnum
from core.campaignSession import CampaignSessionCreate, CampaignSessionRead, CampaignSessionUpdate, create_session
from core.database import SessionDep
from core.campaign import CampaignRead
from routers.usersRouters import current_active_user
from fastapi import HTTPException, APIRouter, Depends, UploadFile, Form
from sqlalchemy import select, delete, update

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
#################################################################################################
# Patch Endpoints
#################################################################################################
# Delete Endpoints
