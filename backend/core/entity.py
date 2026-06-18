import uuid

from sqlalchemy import select, update, delete
from core.models import Entities, entityClassEnum, entityRelationshipEnum
from core.database import SessionDep
from core.campaign import check_campaign_ownership
from pydantic import BaseModel
from fastapi import HTTPException
from datetime import datetime

#Handles the entity creation process.
class EntityCreate(BaseModel):
    name: str
    description: str | None = None
    entity_class: entityClassEnum
    notes: str | None = None

# Handles the entity read process and returns the information.
class EntityRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    campaign_id: uuid.UUID
    entity_class: entityClassEnum
    first_seen: uuid.UUID
    aliases: list[str] | None = None
    notes: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Handles the entity update process
class EntityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    entity_class: entityClassEnum | None = None
    aliases: list[str] | None = None
    notes: str | None = None

class EntityCreateResponse(BaseModel):
    entity: EntityRead | None = None
    duplicate_found: bool = False
    incoming_data: EntityCreate | None = None  # the new data that triggered the duplicate

# Creates entities and adds the to the database and returns a response if there's a duplicate, otherwise it just makes the entity.
async def create_entity(session: SessionDep, entityData: EntityCreate, campaign_id: uuid.UUID, user_id: uuid.UUID, session_id: uuid.UUID) -> EntityCreateResponse | None:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    db_entity = Entities(**entityData.model_dump())

    existing_entity = await get_one_entity_by_name(session, user_id, campaign_id, db_entity.name)

    if existing_entity is None:
        db_entity.campaign_id = campaign_id
        db_entity.first_seen = session_id
        session.add(db_entity)
        await session.commit()
        await session.refresh(db_entity)
        return EntityCreateResponse(entity=db_entity, duplicate_found=False, incoming_data=None)
    else:
        return EntityCreateResponse(entity=existing_entity, duplicate_found=True, incoming_data=entityData)


# Gets an Entity from a campaign by ID.
async def get_one_entity_by_id(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, entity_id: uuid.UUID) -> EntityRead:
    
    # TODO: Determine efficient way to seperate Entities so members can see public entities, but not hidden by DM entities
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = select(Entities).where(Entities.campaign_id == campaign_id, Entities.id == entity_id)
    result = await session.execute(stmt)
    db_entity =  result.scalars().first()

    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return db_entity

# API FACING - Returns EntityRead Pydantic schema for use by endpoints sending data to the frontend.
# Performs an ownership check before returning data.
# Use this in router endpoints when returning entity data to the user.
async def get_one_entity_by_name(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, entity_name: str) -> EntityRead | None:
    
    # TODO: Determine efficient way to seperate Entities so members can see public entities, but not hidden by DM entities
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = select(Entities).where(Entities.campaign_id == campaign_id, Entities.name == entity_name)
    result = await session.execute(stmt)
    db_entity =  result.scalars().first()

    #if not db_entity:
    #    raise HTTPException(status_code=404, detail="Entity not found")

    return db_entity

# TODO: Considering consolidating this later. Too annoyed with this to expand futher at the moment.
# INTERNAL USE ONLY - Returns raw SQLAlchemy Entities object for use by other backend functions.
# Does NOT perform an ownership check - assumes the calling function has already verified ownership.
# Use this when you need to modify or pass the entity to another function.
async def find_entity_by_name(session: SessionDep, campaign_id: uuid.UUID, entity_name: str) -> Entities | None:

    stmt = select(Entities).where(Entities.campaign_id == campaign_id, Entities.name == entity_name)
    result = await session.execute(stmt)
    return result.scalars().first()

# Gets all Entities from a campaign.
async def get_all_entities(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID) -> list[EntityRead]:
    
    # TODO: Determine efficient way to seperate Entities so members can see public entities, but not hidden by DM entities
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = select(Entities).where(Entities.campaign_id == campaign_id)
    result = await session.execute(stmt)
    db_entity =  result.scalars().all()

    return db_entity

# Updates a session for a campaign
async def update_entity(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, entity_id: uuid.UUID, entity_update: EntityUpdate) -> EntityRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    updating_entity = await get_one_entity_by_id(session, user_id, campaign_id, entity_id)

    if entity_update.name is not None:
        updating_entity.name = entity_update.name

    if entity_update.description is not None:
        updating_entity.description = entity_update.description

    if entity_update.entity_class is not None:
        updating_entity.entity_class = entity_update.entity_class

    if entity_update.aliases is not None:
        if updating_entity.aliases is None:
            updating_entity.aliases = entity_update.aliases
        else:
            updating_entity.aliases = updating_entity.aliases + entity_update.aliases

    if entity_update.notes is not None:
        updating_entity.notes = entity_update.notes

    session.add(updating_entity)
    await session.commit()
    await session.refresh(updating_entity)

    return updating_entity

# Deletes an entity from a campaign
async def delete_entity(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, entity_id: uuid.UUID) -> None:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = delete(Entities).where(Entities.campaign_id == campaign_id, Entities.id == entity_id)
    result = await session.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entity not found")

    await session.commit()