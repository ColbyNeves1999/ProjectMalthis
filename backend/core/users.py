import uuid

from fastapi_users import schemas

# Handles the user read process and returns the information.
class UserRead(schemas.BaseUser[uuid.UUID]):
    pass

# Handles the user creation process.
class UserCreate(schemas.BaseUserCreate):
    pass

# Handles the user update process.
class UserUpdate(schemas.BaseUserUpdate):
    pass