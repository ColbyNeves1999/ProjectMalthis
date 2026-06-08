import uuid

from core.models import User
from core.entity import EntityCreate, EntityRead, EntityUpdate, create_entity, get_one_entity_by_id, get_one_entity_by_name, get_all_entities, update_entity, delete_entity
from core.database import SessionDep
from core.campaign import check_campaign_ownership
from routers.usersRouters import current_active_user
from fastapi import APIRouter, Depends
from worker import process_entity_merger

router = APIRouter()

#################################################################################################
# Post Endpoints

# Endpoint to create a new entity
# user_id and role are passed in the request body via FastAPI built in functions
@router.post("/campaigns/{campaign_id}/entities/{session_id}")
async def create_entity_endpoint(session: SessionDep, entityData: EntityCreate, campaign_id: uuid.UUID, session_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> EntityRead:
    
    return await create_entity(session, entityData, campaign_id, current_user.id, session_id)

#################################################################################################
# Get Endpoints

# Endpoint to get a single entity for a campaign via its ID
@router.get("/campaigns/{campaign_id}/entities/entityID/{entity_id}/")
async def get_campaign_session_name(session: SessionDep, campaign_id: uuid.UUID, entity_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> EntityRead | None:
    return await get_one_entity_by_id(session, current_user.id, campaign_id, entity_id)

# Endpoint to get a single entity for a campaign via its name
@router.get("/campaigns/{campaign_id}/entities/entityName/{entity_name}/")
async def get_entity_by_name(session: SessionDep, campaign_id: uuid.UUID, entity_name: str, current_user: User = Depends(current_active_user)) -> EntityRead | None:
    return await get_one_entity_by_name(session, current_user.id, campaign_id, entity_name)

# Endpoint to list all entites for a campaign
@router.get("/campaigns/{campaign_id}/entities/allCampaignEntities/")
async def list_campaign_sessions(session: SessionDep, campaign_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> list[EntityRead]:
    return await get_all_entities(session, current_user.id, campaign_id)

#################################################################################################
# Patch Endpoints

# Endpoint to update an entity for a campaign
@router.patch("/campaigns/{campaign_id}/entities/updateEntity/{entity_id}/")
async def update_entity_in_campaign(session: SessionDep, campaign_id: uuid.UUID, entity_id: uuid.UUID, entity_update: EntityUpdate, current_user: User = Depends(current_active_user)) -> EntityRead:
    return await update_entity(session, current_user.id, campaign_id, entity_id, entity_update)

# Endpoint to handle the merging of an entity with new data.
@router.patch("/campaigns/{campaign_id}/entities/mergeEntity/{entity_id}")
async def update_entity_in_campaign(session: SessionDep, campaign_id: uuid.UUID, entity_id: uuid.UUID, incoming_data: EntityCreate, current_user: User = Depends(current_active_user)) -> EntityRead:

    await check_campaign_ownership(session, current_user.id, campaign_id)

    return await process_entity_merger(str(entity_id), incoming_data.incoming_data)

#################################################################################################
# Delete Endpoints

# Endpoint to delete an entity for a campaign
@router.delete("/campaigns/{campaign_id}/entities/deleteEntity/{entity_id}/")
async def delete_entity_endpoint(session: SessionDep, campaign_id: uuid.UUID, entity_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> None:
    await delete_entity(session, current_user.id, campaign_id, entity_id)