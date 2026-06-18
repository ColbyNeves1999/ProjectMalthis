import uuid

from core.models import User
from core.entityRelationships import EntityRelationshipCreate, EntityRelationshipRead, EntityRelationshipUpdate, create_entity_relationship, get_entity_relationship, get_all_entity_relationship, update_entity_relationship, delete_entity_relationships
from core.database import SessionDep
from routers.usersRouters import current_active_user
from fastapi import APIRouter, Depends

router = APIRouter()

#################################################################################################
# Post Endpoints

# Endpoint to create a relationship between two entities
# user_id and role are passed in the request body via FastAPI built in functions
@router.post("/campaigns/{campaign_id}/relationships/")
async def generate_entity_relationships(session: SessionDep, relationshipData: EntityRelationshipCreate, campaign_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> EntityRelationshipRead:
    
    return await create_entity_relationship(session, current_user.id, campaign_id, relationshipData)

#################################################################################################
# Get Endpoints

# Endpoint to get a single entity relationship
@router.get("/campaigns/{campaign_id}/relationships/single/{entity_one_id}/{entity_two_id}")
async def get_singular_relationship(session: SessionDep, campaign_id: uuid.UUID, entity_one_id: uuid.UUID, entity_two_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> EntityRelationshipRead:
    return await get_entity_relationship(session, current_user.id, campaign_id, entity_one_id, entity_two_id)

# Endpoint to get all entity relationships for a single entity
@router.get("/campaigns/{campaign_id}/relationships/all/{entity_one_id}/")
async def get_all_of_entity_relationships(session: SessionDep, campaign_id: uuid.UUID, entity_one_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> list[EntityRelationshipRead]:
    return await get_all_entity_relationship(session, current_user.id, campaign_id, entity_one_id)

#################################################################################################
# Patch Endpoints

# Endpoint to update an entity relationship
@router.patch("/campaigns/{campaign_id}/relationships/{relationship_id}/")
async def update_relationship_in_campaign(session: SessionDep, campaign_id: uuid.UUID, relationship_id: uuid.UUID, relationship_update: EntityRelationshipUpdate, current_user: User = Depends(current_active_user)) -> EntityRelationshipRead:
    return await update_entity_relationship(session, current_user.id, campaign_id, relationship_id, relationship_update)

#################################################################################################
# Delete Endpoints

# Endpoint to delete a relationship
@router.delete("/campaigns/{campaign_id}/relationships/{relationship_id}/")
async def delete_relationship_endpoint(session: SessionDep, campaign_id: uuid.UUID, relationship_id: uuid.UUID, current_user: User = Depends(current_active_user)) -> None:
    await delete_entity_relationships(session, current_user.id, campaign_id, relationship_id)