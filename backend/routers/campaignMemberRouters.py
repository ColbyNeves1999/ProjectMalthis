import uuid

from core.models import User, CampaignMember
from core.database import SessionDep
from core.campaignMember import CampaignMemberCreate, CampaignMemberRead, create_member
from core.campaign import CampaignRead
from routers.usersRouters import current_active_user
from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy import select, delete, update

router = APIRouter()

# Endpoint to create a link between a user and a campaign
# campaign_id is passed as a path parameter
# user_id and role are passed in the request body via FastAPI built in functions
@router.post("/campaign_members/{campaign_id}/")
async def create_campaign_link(campaign_id: uuid.UUID, campaign_member: CampaignMemberCreate, session: SessionDep, current_user: User = Depends(current_active_user)) -> CampaignMemberRead:
    
    return await create_member(session, current_user.id, campaign_id, campaign_member.role)

# Endpoint that lists all campaigns a user is associated with
@router.get("/campaign_members/userAssociatedCampaigns/")
async def list_associated_campaigns(session: SessionDep, current_user: User = Depends(current_active_user)) -> list[CampaignMemberRead]:
    
    stmt = select(CampaignMember).where(CampaignMember.user_id == current_user.id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Endpoint that lists all users a campaign is associated with
@router.get("/campaign_members/campaignAssociatedUsers/{campaign_id}/")
async def list_associated_users(campaign_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user)) -> list[CampaignMemberRead]:
    
    stmt = select(CampaignMember).where(CampaignMember.campaign_id == campaign_id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Endpoint that deletes a campaign connection between a user and a campaign
@router.delete("/campaign_members/delete/{campaign_id}/")
async def delete_campaign_link(campaign_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user)) -> None:
    
    stmt = delete(CampaignMember).where(CampaignMember.user_id == current_user.id, CampaignMember.campaign_id == campaign_id)
    await session.execute(stmt)
    await session.commit()