from typing import Annotated

from collections.abc import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from core.models import Base, User

import os

DATABASE_URL = os.environ.get("DATABASE_URL")

#################################################################################################
# Logic provided by SQLAlchemy and FastAPI Users documentation.

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

# Generates a type that is used to inject the database session
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
#################################################################################################