import uuid

from pydantic import BaseModel
from sqlalchemy import select
from core.models import CampaignMember
from core.database import SessionDep
from fastapi import HTTPException

# Handles the campaign member creation process.
class CampaignMemberCreate(BaseModel):
    role: str

# Handles the campaign member read process and returns the information.
class CampaignMemberRead(BaseModel):

    id: uuid.UUID
    user_id: uuid.UUID
    campaign_id: uuid.UUID
    role: str

    class Config:
        from_attributes = True

async def check_campaign_membership(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID):
    stmt = select(CampaignMember).where(CampaignMember.user_id == user_id, CampaignMember.campaign_id == campaign_id)
    result = await session.execute(stmt)
    is_member = result.scalars().first()

    if is_member is None:
        raise HTTPException(status_code=403, detail="User is not a member of this campaign.")
    else:
        return True
    
async def create_member(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, role_title: str):
    db_campaign_member = CampaignMember(role=role_title)
    db_campaign_member.user_id = user_id
    db_campaign_member.campaign_id = campaign_id
    session.add(db_campaign_member)
    await session.commit()
    await session.refresh(db_campaign_member)
    return db_campaign_member