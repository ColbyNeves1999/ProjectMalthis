import uuid

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, DateTime, ForeignKey, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

import os

DATABASE_URL = os.environ.get("DATABASE_URL")

# Creates the base table that all tables in the database will inherit from
class Base(DeclarativeBase):
    pass

# The User table, built on FastAPI Users' default fields (email, password, etc.)
class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

# Creates the database engine and session factory for Project Malthis
engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Creates the database and tables for Project Malthis.
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Opens a database session for each request and closes it when done.
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# Provides FastAPI Users with access to the User table for auth operations (login, register, etc.)
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)