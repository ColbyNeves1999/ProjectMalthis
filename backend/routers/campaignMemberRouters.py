import uuid

from core.models import Campaign, User, CampaignMember
from core.database import SessionDep
from core.campaignMember import CampaignMemberCreate, CampaignMemberRead
from routers.usersRouters import current_active_user
from fastapi import HTTPException, APIRouter, Depends

router = APIRouter()

# Endpoint to create a link between a user and a campaign
# campaign_id is passed as a path parameter
# user_id and role are passed in the request body via FastAPI built in functions
@router.post("/campaign_members/{campaign_id}/")
async def create_campaign_link(campaign_id: uuid.UUID, campaign_member: CampaignMemberCreate, session: SessionDep, current_user: User = Depends(current_active_user)) -> CampaignMemberRead:
    
    # .model_dump() is a Pydantic function that translates a Pydantic model to SQLAlchemy model
    db_campaign_member = CampaignMember(**campaign_member.model_dump())
    db_campaign_member.user_id = current_user.id
    db_campaign_member.campaign_id = campaign_id
    session.add(db_campaign_member)
    await session.commit()
    await session.refresh(db_campaign_member)
    return db_campaign_member
