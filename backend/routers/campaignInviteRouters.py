import uuid

from core.models import User, requestStatusEnum
from core.campaignInvite import CampaignJoinRequestToken, CampaignJoinRequestRead, CampaignJoinRequestUpdate, CampaignLinkRead, CampaignLinkUpdate, create_link, delete_invite_link, update_invite_link, get_campaign_invite, create_join_request, get_join_requests, approve_join_request, user_get_join_requests, get_specific_join_request
from core.database import SessionDep
from routers.usersRouters import current_active_user
from fastapi import APIRouter, Depends
from datetime import datetime

router = APIRouter()
#################################################################################################
# Post Endpoints

# Endpoint to create a new campaign invite link
@router.post("/campaigns/{campaign_id}/inviteLinkCreation/")
async def create_campaign_invite_link(campaign_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user), expiration_date: datetime | None = None) -> CampaignLinkRead:
    
    return await create_link(session, current_user.id, campaign_id, expiration_date)

# Endpoint to create a campaign join request using an invite token
@router.post("/campaigns/{campaign_id}/joinRequest/")
async def create_campaign_join_request(campaign_id: uuid.UUID, session: SessionDep, token: CampaignJoinRequestToken, current_user: User = Depends(current_active_user)) -> CampaignJoinRequestRead:
    return await create_join_request(session, current_user.id, campaign_id, token)

#################################################################################################
# Get Endpoints

# Endpoint to get information about a campaign invite link
@router.get("/campaigns/{campaign_id}/inviteLink/")
async def get_campaign_invite_link(campaign_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user)) -> CampaignLinkRead:
    return await get_campaign_invite(session, campaign_id)

# Endpoint to get all join requests for a campaign, only accessible by the campaign owner
@router.get("/campaigns/{campaign_id}/joinRequests/")
async def get_campaign_join_requests_endpoint(campaign_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user)) -> list[CampaignJoinRequestRead]:
    return await get_join_requests(session, current_user.id, campaign_id)

# Endpoint to get a specific join request for a campaign, only accessible by the campaign owner
@router.get("/campaigns/{campaign_id}/specificRequests/{request_id}/")
async def get_specific_join_request_endpoint(campaign_id: uuid.UUID, request_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user)) -> CampaignJoinRequestRead:
    return await get_specific_join_request(session, current_user.id, campaign_id, request_id)

# Endpoint to get all join requests for a campaign that the user has made, only accessible by the user
@router.get("/campaigns/{campaign_id}/userJoinRequests/")
async def user_get_join_requests_endpoint(campaign_id: uuid.UUID, session: SessionDep, current_user: User = Depends(current_active_user)) -> list[CampaignJoinRequestRead]:
    return await user_get_join_requests(session, current_user.id, campaign_id)

#################################################################################################
# Patch Endpoints

# Endpoint to update a campaign invite link
@router.patch("/campaigns/{campaign_id}/inviteLink/")
async def update_campaign_invite_link(campaign_id: uuid.UUID, session: SessionDep, update_data: CampaignLinkUpdate, current_user: User = Depends(current_active_user)) -> CampaignLinkRead:
    return await update_invite_link(session, current_user.id, campaign_id, update_data)

# Endpoint to approve or reject a campaign join request, only accessible by the campaign owner
@router.patch("/campaigns/{campaign_id}/approveJoinRequest/{request_id}/")
async def approve_campaign_join_request(campaign_id: uuid.UUID, session: SessionDep, request_id: uuid.UUID,  approval: CampaignJoinRequestUpdate, current_user: User = Depends(current_active_user)) -> CampaignJoinRequestRead:
    return await approve_join_request(session, current_user.id, campaign_id, request_id, approval)

#################################################################################################
# Delete Endpoints

# Endpoint to delete a campaign invite link
@router.delete("/campaigns/{campaign_id}/inviteLink/")
async def delete_campaign_invite_link(campaign_id: uuid.UUID, session: SessionDep) -> None:
    await delete_invite_link(session, campaign_id)