import uuid

from sqlalchemy import select, update, delete, or_
from core.models import entityRelationshipEnum, EntityRelationships
from core.campaign import check_campaign_ownership
from core.database import SessionDep
from pydantic import BaseModel

# Hanles the creation of the entity relationships
class EntityRelationshipCreate(BaseModel):
    entity_one_id: uuid.UUID
    entity_two_id: uuid.UUID
    relationship: entityRelationshipEnum

# Handles the entity relationship read process and returns the information.
class EntityRelationshipRead(BaseModel):

    id: uuid.UUID
    entity_one_id: uuid.UUID
    entity_two_id: uuid.UUID
    relationship: entityRelationshipEnum

    class Config:
        from_attributes = True

class EntityRelationshipUpdate(BaseModel):
    relationship: entityRelationshipEnum

# Creates a relationship between two entities.
async def create_entity_relationship(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, entitiesRelationship: EntityRelationshipCreate) -> EntityRelationshipRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)
    
    db_entity_relationship = EntityRelationships(**entitiesRelationship.model_dump())
    session.add(db_entity_relationship)
    await session.commit()
    await session.refresh(db_entity_relationship)
    return db_entity_relationship

# Get's the relationship between two entities.
async def get_entity_relationship(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, entity_one_id: uuid.UUID, entity_two_id: uuid.UUID) -> EntityRelationshipRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = select(EntityRelationships).where(EntityRelationships.entity_one_id == entity_one_id, EntityRelationships.entity_two_id == entity_two_id)
    result = await session.execute(stmt)
    return result.scalars().first()

# Get's all the relationships for a specific entity.
async def get_all_entity_relationship(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, entity_id: uuid.UUID) -> list[EntityRelationshipRead]:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = select(EntityRelationships).where(or_(EntityRelationships.entity_one_id == entity_id, EntityRelationships.entity_two_id == entity_id))
    result = await session.execute(stmt)
    return result.scalars().all()

# Updates the relationship between two entities
async def update_entity_relationship(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, relationship_id: uuid.UUID, entitiesRelationship: EntityRelationshipUpdate) -> EntityRelationships:

    await check_campaign_ownership(session, user_id, campaign_id)

    update_data = entitiesRelationship.model_dump(exclude_unset=True)
    stmt = update(EntityRelationships).where(EntityRelationships.id == relationship_id).values(**update_data)
    await session.execute(stmt)
    await session.commit()
    stmt = select(EntityRelationships).where(EntityRelationships.id == relationship_id)
    result = await session.execute(stmt)
    return result.scalars().first()

# Deletes the relationship between two entities.
async def delete_entity_relationships(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, relationship_id: uuid.UUID) -> None:
    
    await check_campaign_ownership(session, user_id, campaign_id)

    stmt = delete(EntityRelationships).where(EntityRelationships.id == relationship_id)
    await session.execute(stmt)
    await session.commit()
