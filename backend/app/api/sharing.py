"""
GeoPulse — Location Sharing API Routes

POST /api/v1/sharing/request
GET  /api/v1/sharing/requests
POST /api/v1/sharing/{id}/accept
POST /api/v1/sharing/{id}/reject
POST /api/v1/sharing/{id}/revoke
POST /api/v1/sharing/{id}/stop
GET  /api/v1/sharing/active
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config.security import get_current_user_id
from app.schemas.auth import MessageResponse
from app.schemas.sharing import CreateSharingRequest, SharingResponse
from app.services import sharing_service

router = APIRouter(prefix="/api/v1/sharing", tags=["Location Sharing"])


@router.post("/request", response_model=dict)
async def send_sharing_request(
    request: CreateSharingRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Send a location-sharing request to another user."""
    permissions = {
        "liveLocation": request.permissions.live_location,
        "locationHistory": request.permissions.location_history,
    }
    share = await sharing_service.send_request(
        requester_id=user_id,
        target_phone=request.target_phone,
        permissions=permissions,
    )
    return {
        "message": "Location sharing request sent",
        "share_id": str(share["_id"]),
        "status": share["status"],
    }


@router.get("/requests", response_model=list)
async def get_pending_requests(user_id: str = Depends(get_current_user_id)):
    """Get all pending incoming location-sharing requests."""
    return await sharing_service.get_pending_requests(user_id)


@router.post("/{share_id}/accept", response_model=dict)
async def accept_request(
    share_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Accept a location-sharing request."""
    share = await sharing_service.accept_request(share_id, user_id)
    return {"message": "Request accepted", "share": share}


@router.post("/{share_id}/reject", response_model=MessageResponse)
async def reject_request(
    share_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Reject a location-sharing request."""
    await sharing_service.reject_request(share_id, user_id)
    return MessageResponse(message="Request rejected")


@router.post("/{share_id}/revoke", response_model=MessageResponse)
async def revoke_access(
    share_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Revoke an active location-sharing relationship."""
    await sharing_service.revoke_access(share_id, user_id)
    return MessageResponse(message="Access revoked")


@router.post("/{share_id}/stop", response_model=MessageResponse)
async def stop_sharing(
    share_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Stop sharing your location (owner action)."""
    await sharing_service.stop_sharing(share_id, user_id)
    return MessageResponse(message="Location sharing stopped")


@router.get("/active", response_model=dict)
async def get_active_shares(user_id: str = Depends(get_current_user_id)):
    """Get all sharing relationships (incoming & outgoing)."""
    return await sharing_service.get_active_shares(user_id)
