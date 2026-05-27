import uuid

from core.models import Campaign, User, roleEnum
from core.database import SessionDep
from core.campaign import CampaignCreate, CampaignRead, CampaignUpdate, check_campaign_ownership, change_campaign_data
from routers.usersRouters import current_active_user
from core.campaignMember import check_campaign_membership, create_member, delete_campaign_links
from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy import select, delete

router = APIRouter()
#################################################################################################
# Post Endpoints

# Endpoint to create a new campaign
# user_id and role are passed in the request body via FastAPI built in functions
@router.post("/campaigns/")
async def create_campaigns(campaign: CampaignCreate, session: SessionDep, current_user: User = Depends(current_active_user)) -> CampaignRead:
    
    # .model_dump() is a Pydantic function that translates a Pydantic model to SQLAlchemy model
    db_campaign = Campaign(**campaign.model_dump())
    db_campaign.owner_id = current_user.id
    session.add(db_campaign)
    await session.commit()
    await session.refresh(db_campaign)
    await create_member(session, current_user.id, db_campaign.id, roleEnum.Dungeon_Master)
    return db_campaign

#################################################################################################
# Get Endpoints

# Endpoint to list all campaigns a user owns
@router.get("/campaigns/userOwnedCampaigns/")
async def list_user_owned_campaigns(session: SessionDep, current_user: User = Depends(current_active_user)) -> list[CampaignRead]:
    stmt = select(Campaign).where(Campaign.owner_id == current_user.id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Endpoint to get information about a specific campaign
@router.get("/campaigns/specificCampaign/{campaign_id}/")
async def get_campaign(session: SessionDep, current_user: User = Depends(current_active_user), campaign_id: uuid.UUID = None) -> CampaignRead:

    await check_campaign_membership(session, current_user.id, campaign_id)

    stmt = select(Campaign).where(Campaign.id == campaign_id)
    result = await session.execute(stmt)
    return result.scalars().first()

#################################################################################################
# Patch Endpoints

# Endpoint to change the name of a campaign the user owns
@router.patch("/campaigns/ChangeCampaignData/{campaign_id}/")
async def change_campaign_data_endpoint(campaign_id: uuid.UUID, session: SessionDep, campaign_data: CampaignUpdate, current_user: User = Depends(current_active_user)) -> CampaignRead:

        return await change_campaign_data(session, current_user.id, campaign_id, campaign_data)

#################################################################################################
# Delete Endpoints

# Endpoint to delete a campaign the user owns
@router.delete("/campaigns/DeleteCampaign/{campaign_id}/")
async def delete_campaign(campaign_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user)) -> None:

    await check_campaign_ownership(session, current_user.id, campaign_id)

    await delete_campaign_links(session, campaign_id)
    stmt = delete(Campaign).where(Campaign.id == campaign_id, Campaign.owner_id == current_user.id)
    await session.execute(stmt)
    await session.commit()
