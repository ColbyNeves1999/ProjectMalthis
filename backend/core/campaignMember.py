import uuid

from pydantic import BaseModel
from sqlalchemy import select, delete
from core.models import CampaignMember, Campaign, roleEnum
from core.database import SessionDep
from fastapi import HTTPException

# Handles the campaign member creation process.
class CampaignMemberCreate(BaseModel):
    role: roleEnum

# Handles the campaign member read process and returns the information.
class CampaignMemberRead(BaseModel):

    id: uuid.UUID
    user_id: uuid.UUID
    campaign_id: uuid.UUID
    role: str

    class Config:
        from_attributes = True

# Checks if a user is a member of a campaign.
async def check_campaign_membership(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID):
    stmt = select(CampaignMember).where(CampaignMember.user_id == user_id, CampaignMember.campaign_id == campaign_id)
    result = await session.execute(stmt)
    is_member = result.scalars().first()

    if is_member is None:
        raise HTTPException(status_code=403, detail="User is not a member of this campaign.")
    else:
        return True

# Checks if a user is the owner of a campaign.    
async def check_campaign_ownership(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID):
    stmt = select(Campaign).where(Campaign.owner_id == user_id, Campaign.id == campaign_id)
    result = await session.execute(stmt)
    is_owner = result.scalars().first()

    if is_owner is None:
        return False
    else:
        return True
    
# Creates a connection between a user and a campaign with a specific role.
async def create_member(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, role_title: roleEnum) -> CampaignMember:
    db_campaign_member = CampaignMember(role=role_title)
    db_campaign_member.user_id = user_id
    db_campaign_member.campaign_id = campaign_id
    session.add(db_campaign_member)
    await session.commit()
    await session.refresh(db_campaign_member)
    return db_campaign_member

# Lists all users associated with a campaign.
async def users_and_campaigns(session: SessionDep, campaign_id: uuid.UUID) -> list[CampaignMemberRead]:
    
    stmt = select(CampaignMember).where(CampaignMember.campaign_id == campaign_id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Deletes the connection between all users and a campaign.
async def delete_campaign_links(session: SessionDep, campaign_id: uuid.UUID) -> None:
    stmt = delete(CampaignMember).where(CampaignMember.campaign_id == campaign_id)
    await session.execute(stmt)
    await session.commit()