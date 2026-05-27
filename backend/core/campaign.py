import uuid

from sqlalchemy import select, delete, update
from core.models import Campaign
from core.database import SessionDep
from pydantic import BaseModel
from fastapi import HTTPException
#Handles the campaign creation process.
class CampaignCreate(BaseModel):
    name: str
    description: str | None = None

# Handles the campaign read process and returns the information.
class CampaignRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    
    class Config:
        from_attributes = True

class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

# Checks if a user is the owner of a campaign.    
async def check_campaign_ownership(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID):
    stmt = select(Campaign).where(Campaign.owner_id == user_id, Campaign.id == campaign_id)
    result = await session.execute(stmt)
    is_owner = result.scalars().first()

    if is_owner is None:
        raise HTTPException(status_code=403, detail="User is not the owner of this campaign.")
    else:
        return is_owner

# Changes the data of a campaign if the user is the owner of the campaign.
async def change_campaign_data(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, campaign_data: CampaignUpdate) -> CampaignRead:

    await check_campaign_ownership(session, user_id, campaign_id)
    
    update_data = campaign_data.model_dump(exclude_unset=True)
    stmt = update(Campaign).where(Campaign.id == campaign_id, Campaign.owner_id == user_id).values(**update_data)
    result = await session.execute(stmt)
    await session.commit()
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    result = await session.execute(stmt)
    return result.scalars().first()