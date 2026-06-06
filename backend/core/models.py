import uuid
import enum

from datetime import datetime, timezone
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY

# Creates the base table that all tables in the database will inherit from
class Base(DeclarativeBase):
    pass

# The User table, built on FastAPI Users' default fields (email, password, etc.)
class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

# Enum for the different roles a user can have in a campaign
class roleEnum(enum.Enum):
    Dungeon_Master = "Dungeon Master"
    Player = "Player"
    Spectator = "Spectator"

# Enum for the different statuses a campaign join request can have
class requestStatusEnum(enum.Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"

# Enum for the different statuses a campaign session job can have
class jobStatusEnum(enum.Enum):
    Pending = "Pending"
    Processing = "Processing"
    Needs_Review = "Needs Review"
    Completed = "Completed"
    Failed = "Failed"

# Enum for the different classifications of an entity
class entityClassEnum(enum.Enum):
    Player = "Player"
    Player_Character = "Player Character"
    NPC = "NPC"
    Monster = "Monster"
    Location = "Location"
    Item = "Item"

# Enum for the different relationships between entities
class entityRelationshipEnum(enum.Enum):
    Allies = "Allies"
    Enemies = "Enemies"
    Possesses = "Possesses"
    Located_In = "Located In"
    Employs = "Employs"
    Ruled_By = "Ruled By"
    Worships = "Worships"
    Created = "Created"
    Betrayed = "Betrayed"
    Leads = "Leads"
    Borders = "Borders"
    Contains = "Contains"
    Originates_From = "Originates From"
    Part_Of = "Part Of"
    Related_To = "Related To"
    Killed = "Killed"
    Resurrected = "Resurrected"
    Quested_For = "Quested For"
    Sells = "Sells"
    Trades_With = "Trades With"
    Imprisoned_By = "Imprisoned By"
    Transformed_Into = "Transformed Into"
    Seeks = "Seeks"

# Campaign Schema
class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# CampaignMember Schema
class CampaignMember(Base):
    __tablename__ = "campaign_members"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    role: Mapped[roleEnum] = mapped_column(Enum(roleEnum), nullable=False)

# Campaign Invite Schema
class CampaignInvite(Base):
    __tablename__ = "campaign_invites"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id"), unique=True, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_valid: Mapped[bool] = mapped_column(default=True)

# Campaign Join Request Schema
class CampaignJoinRequest(Base):
    __tablename__ = "campaign_join_requests"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    status: Mapped[requestStatusEnum] = mapped_column(Enum(requestStatusEnum), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

# Campaign Session Schema
class CampaignSession(Base):
    __tablename__ = "campaign_sessions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    session_name: Mapped[str] = mapped_column(String, nullable=False)
    audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    job_status: Mapped[jobStatusEnum] = mapped_column(Enum(jobStatusEnum), nullable=False, default=jobStatusEnum.Pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    transcript: Mapped[str] = mapped_column(String, nullable=True)
    session_number: Mapped[int] = mapped_column(nullable=False, default=0)

# Entity Schema
class Entities(Base):
    __tablename__ = "entities"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    entity_class: Mapped[entityClassEnum] = mapped_column(Enum(entityClassEnum), nullable=False)
    first_seen: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns_sessions.id"), nullable=True)
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    notes: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Entity Relationship Schema
class EntityRelationships(Base):
    __tablename__ = "entity_relationships"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_one_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), nullable=False)
    relationship: Mapped[entityRelationshipEnum] = mapped_column(Enum(entityRelationshipEnum), nullable=False)
    entity_two_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), nullable=False)