import uuid
import os

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from core.database import User, get_user_db

SECRET = os.environ.get("SECRET_KEY")

# Manages the handler for all user related operations (register, login, forgot password, etc.)
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    # Handles post registration logic
    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.id} has registered.")
        # Things like welcome emails will be put here.

    # Handles password reset logic
    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")
        # Things like sending a password reset email will be put here.

    # Handles verification logic
    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")
        # Things like sending a verification email will be put here.

# Makes the UserManager available to the rest of the app through dependency injection.
async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

# Handles the way tokens are transported between the client and server.
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# Defines the strategy for generating and verifying tokens, in this case JWTs.
def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

# Combines the transport and strategy into a single authentication backend for FastAPI Users to use.
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Initializes the FastAPI system using the User model, UserManager, and authentication backend defined above.
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# The dependency that will be called by other functions needing to access the currently logged in user.
current_active_user = fastapi_users.current_user(active=True)