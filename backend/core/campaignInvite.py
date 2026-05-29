import uuid
import secrets

from pydantic import BaseModel
from sqlalchemy import select, delete, update
from datetime import datetime, timezone
from core.database import SessionDep
from core.campaign import check_campaign_ownership
from core.campaignMember import create_member, roleEnum
from core.models import CampaignInvite, CampaignJoinRequest, requestStatusEnum
from fastapi import HTTPException

# Handles the campaign link creation process.
class CampaignLinkCreate(BaseModel):
    expires_at: datetime | None = None

# Handles the campaign link read process and returns the information.
class CampaignLinkRead(BaseModel):

    id: uuid.UUID
    token: str
    campaign_id: uuid.UUID
    expires_at: datetime | None
    created_at: datetime | None
    is_valid: bool

    class Config:
        from_attributes = True

# Handles the campaign link update process
class CampaignLinkUpdate(BaseModel):
    is_valid: bool
    expires_at: datetime | None = None

# Handles the campaign join request creation process
class CampaignJoinRequestRead(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    user_id: uuid.UUID
    status: requestStatusEnum
    created_at: datetime
    reviewed_at: datetime | None

    class Config:
        from_attributes = True

# Handles the campaign join request update process
class CampaignJoinRequestUpdate(BaseModel):
    status: requestStatusEnum

# Handles the token validation process for a campaign join request
class CampaignJoinRequestToken(BaseModel):
    token: str

#################################################################################################
# Invite Link Functions

# Creates a connection between a user and a campaign with a specific role.
async def create_link(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, expiration_date: datetime | None) -> CampaignLinkRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)
    
    #Generates a token for the invite link, then creates the invite link and saves it to the database.
    token_generation = secrets.token_urlsafe(32)
    db_campaign_link = CampaignInvite(expires_at=expiration_date)
    db_campaign_link.campaign_id = campaign_id
    db_campaign_link.token = token_generation
    session.add(db_campaign_link)
    await session.commit()
    await session.refresh(db_campaign_link)
    return db_campaign_link

# Gets the information of a campaign invite link.
async def get_campaign_invite(session: SessionDep, campaign_id: uuid.UUID) -> CampaignLinkRead:
    
    stmt = select(CampaignInvite).where(CampaignInvite.campaign_id == campaign_id)
    result = await session.execute(stmt)
    db_campaign_link = result.scalars().first()
    if db_campaign_link is None:
        raise HTTPException(status_code=404, detail="Campaign invite not found")
    return db_campaign_link

# Changes the data of a campaign invite link if the user is the owner of the campaign.
async def update_invite_link(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, update_data: CampaignLinkUpdate) -> CampaignLinkRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)
    update_data = update_data.model_dump(exclude_unset=True)
    stmt = update(CampaignInvite).where(CampaignInvite.campaign_id == campaign_id).values(**update_data)
    await session.execute(stmt)
    await session.commit()
    return await get_campaign_invite(session, campaign_id)

# Deletes the connection between a campaign and an invite link.
async def delete_invite_link(session: SessionDep, campaign_id: uuid.UUID) -> None:
    stmt = delete(CampaignInvite).where(CampaignInvite.campaign_id == campaign_id)
    await session.execute(stmt)
    await session.commit()

#################################################################################################
# Join Request Functions

# Creates a connection between a user and a campaign with a specific role.
async def create_join_request(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, token: CampaignJoinRequestToken) -> CampaignJoinRequestRead:
    
    print(f"campaign_id: {campaign_id}, user_id: {user_id}, token: {token.token}")

    # Check if the token is valid
    stmt = select(CampaignInvite).where(CampaignInvite.campaign_id == campaign_id, CampaignInvite.token == token.token, CampaignInvite.is_valid == True)
    result = await session.execute(stmt)
    db_campaign_link = result.scalars().first()
    if db_campaign_link is None:
        raise HTTPException(status_code=400, detail="Non-active token")

    # Actually create the join request
    db_join_request = CampaignJoinRequest(status=requestStatusEnum.Pending)
    db_join_request.campaign_id = campaign_id
    db_join_request.user_id = user_id
    session.add(db_join_request)
    await session.commit()
    await session.refresh(db_join_request)
    return db_join_request

# Gets the information of all campaign join request for a DM.
async def get_join_requests(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID) -> list[CampaignJoinRequestRead]:

    await check_campaign_ownership(session, user_id, campaign_id)
    stmt = select(CampaignJoinRequest).where(CampaignJoinRequest.campaign_id == campaign_id)
    result = await session.execute(stmt)
    db_join_request = result.scalars().all()
    return db_join_request

# Gets the specific join request information for a user and a campaign.
async def get_specific_join_request(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, request_id: uuid.UUID) -> CampaignJoinRequestRead:
    
    await check_campaign_ownership(session, user_id, campaign_id)
    stmt = select(CampaignJoinRequest).where(CampaignJoinRequest.campaign_id == campaign_id, CampaignJoinRequest.id == request_id)
    result = await session.execute(stmt)
    db_join_request = result.scalars().first()
    if db_join_request is None:
        raise HTTPException(status_code=404, detail="Campaign join request not found")
    return db_join_request

# Gets the information of all campaign join request for a user.
async def user_get_join_requests(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID) -> list[CampaignJoinRequestRead]:
    stmt = select(CampaignJoinRequest).where(CampaignJoinRequest.campaign_id == campaign_id, CampaignJoinRequest.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()

# Changes the status of a campaign join request if the user is the owner of the campaign.
async def approve_join_request(session: SessionDep, user_id: uuid.UUID, campaign_id: uuid.UUID, request_id: uuid.UUID, approval: CampaignJoinRequestUpdate) -> CampaignJoinRequestRead:
   
    # Requests a specific join request to check if it exists and if the user has the right to approve/reject it
    request = await get_specific_join_request(session, user_id, campaign_id, request_id)
    if request.status != requestStatusEnum.Pending:
        raise HTTPException(status_code=400, detail="Request already reviewed")
    
    # Update the join request status to the approver's decision, and sets when it was reviewed
    stmt = update(CampaignJoinRequest).where(CampaignJoinRequest.id == request_id).values(status=approval.status, reviewed_at=datetime.now(timezone.utc))
    await session.execute(stmt)
    await session.commit()

    # Creates a campaign membership if the request was approved
    if approval.status == requestStatusEnum.Approved:
        await create_member(session, request.user_id, campaign_id, roleEnum.Player)

    return await get_specific_join_request(session, user_id, campaign_id, request_id)