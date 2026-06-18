from fastapi import FastAPI, Depends
from core.database import User, create_db_and_tables
from core.users import UserCreate, UserRead, UserUpdate
from routers.usersRouters import auth_backend, current_active_user, fastapi_users
from contextlib import asynccontextmanager
from routers import campaignRouters, campaignMemberRouters, campaignInviteRouters, campaignSessionRouters, entityRouters, entityRelationshipsRouters

# Provided by FastAPI Documentation: https://fastapi.tiangolo.com/advanced/events/#lifespan-events
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
    yield

# Create the FastAPI app and include the lifespan function
app = FastAPI(title="Project Malthis", lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "Project Malthis is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# Router inclusions from the routers directory
app.include_router(campaignRouters.router, tags=["Campaigns"])
app.include_router(campaignMemberRouters.router, tags=["Campaign Members"])
app.include_router(campaignInviteRouters.router, tags=["Campaigns Invites"])
app.include_router(campaignSessionRouters.router, tags=["Sessions"])
app.include_router(entityRouters.router, tags=["Entities"])
app.include_router(entityRelationshipsRouters.router, tags=["Entity Relationships"])

#################################################################################################
# Authentication and User Management Routes provided by FastAPI Users' Documentation: 
# https://fastapi-users.github.io/fastapi-users/latest/
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
#################################################################################################

@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}