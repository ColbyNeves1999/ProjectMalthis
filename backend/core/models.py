import uuid
import enum

from datetime import datetime, timezone
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID

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

