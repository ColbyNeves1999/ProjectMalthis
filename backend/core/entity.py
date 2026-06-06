import uuid

from sqlalchemy import select, update
from core.models import Entities, entityClassEnum, entityRelationshipEnum
from core.database import SessionDep
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
    aliases: list[str | None]
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

# Hanles the creation of the entity relationships
class EntityRelationshipCreate(BaseModel):
    relationship: entityRelationshipEnum

# Handles the campaign member read process and returns the information.
class EntityRelationshipRead(BaseModel):

    id: uuid.UUID
    entity_one_id: uuid.UUID
    entity_two_id: uuid.UUID
    relationship: entityRelationshipEnum

    class Config:
        from_attributes = True

class EntityRelationshipUpdate(BaseModel):
    relationship: entityRelationshipEnum

# 