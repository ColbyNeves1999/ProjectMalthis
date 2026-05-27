import uuid

from core.models import Campaign, User, roleEnum
from core.database import SessionDep
from core.campaign import CampaignCreate, CampaignRead
from routers.usersRouters import current_active_user
from core.campaignMember import check_campaign_membership, create_member, delete_campaign_links, check_campaign_ownership
from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy import select, delete, update

router = APIRouter()

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
    await create_member(session, current_user.id, db_campaign.id, roleEnum.Dungeon_Master.value)
    return db_campaign

# Endpoint to list all campaigns a user owns
@router.get("/campaigns/userOwnedCampaigns/")
async def list_user_owned_campaigns(session: SessionDep, current_user: User = Depends(current_active_user)) -> list[CampaignRead]:
    stmt = select(Campaign).where(Campaign.owner_id == current_user.id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Endpoint to get information about a specific campaign
@router.get("/campaigns/specificCampaign/{campaign_id}/")
async def get_campaign(session: SessionDep, current_user: User = Depends(current_active_user), campaign_id: uuid.UUID = None) -> CampaignRead:

    is_member = await check_campaign_membership(session, current_user.id, campaign_id)

    if is_member:
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await session.execute(stmt)
        return result.scalars().first()
    else:
        raise HTTPException(status_code=403, detail="User is not a member of this campaign.")
    
# Endpoint to delete a campaign the user owns
@router.delete("/campaigns/DeleteCampaign/{campaign_id}/")
async def delete_campaign(campaign_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user)) -> None:

    temp = await check_campaign_ownership(session, current_user.id, campaign_id)

    if temp is False:
        raise HTTPException(status_code=403, detail="User is not the owner of this campaign.")
    else:
        await delete_campaign_links(session, campaign_id)

        stmt = delete(Campaign).where(Campaign.id == campaign_id, Campaign.owner_id == current_user.id)
        await session.execute(stmt)
        await session.commit()
