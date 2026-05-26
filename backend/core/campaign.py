from pydantic import BaseModel
import uuid

#Handles the campaign creation process.
class CampaignCreate(BaseModel):
    name: str
    description: str | None = None

# Handles the campaign read process and returns the information.
class CampaignRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    
    class Config:
        from_attributes = True
