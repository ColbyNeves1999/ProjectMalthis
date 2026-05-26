from core.models import Campaign, User
from core.database import SessionDep
from core.campaign import CampaignCreate, CampaignRead
from routers.usersRouters import current_active_user
from fastapi import HTTPException, APIRouter, Depends

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
    return db_campaign
