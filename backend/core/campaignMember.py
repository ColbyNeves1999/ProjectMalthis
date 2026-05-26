from pydantic import BaseModel
import uuid

# Handles the campaign member creation process.
class CampaignMemberCreate(BaseModel):
    user_id: uuid.UUID
    campaign_id: uuid.UUID
    role: str

# Handles the campaign member read process and returns the information.
class CampaignMemberRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    campaign_id: uuid.UUID
    role: str

    class Config:
        from_attributes = True
