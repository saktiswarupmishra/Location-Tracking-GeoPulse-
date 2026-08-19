"""
GeoPulse — Privacy & Safety API Routes (§28, §29, §30)

POST   /api/v1/users/block/{user_id}
DELETE /api/v1/users/block/{user_id}
POST   /api/v1/users/report
DELETE /api/v1/users/me — full account deletion
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config.security import get_current_user_id
from app.repositories import (
    audit_repository,
    block_repository,
    report_repository,
    sharing_repository,
    user_repository,
    location_repository,
    session_repository,
    device_token_repository,
    emergency_contact_repository,
    geofence_state_repository,
)

router = APIRouter(prefix="/api/v1/users", tags=["Privacy & Safety"])


class ReportRequest(BaseModel):
    reported_user_id: str
    reason: str = Field(..., max_length=50)
    description: str = Field("", max_length=1000)


class MessageResponse(BaseModel):
    message: str


# ── Block (§28) ──

@router.post("/block/{target_id}", response_model=MessageResponse)
async def block_user(
    target_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Block a user — auto-revokes all sharing relationships."""
    if user_id == target_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    await block_repository.create_block(user_id, target_id)

    # Auto-revoke sharing in both directions
    await sharing_repository.revoke_all_for_user_pair(user_id, target_id)

    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="BLOCK_CREATED",
        resource_type="block",
        resource_id=target_id,
    )

    return MessageResponse(message="User blocked successfully")


@router.delete("/block/{target_id}", response_model=MessageResponse)
async def unblock_user(
    target_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Unblock a user."""
    removed = await block_repository.remove_block(user_id, target_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Block not found")

    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="BLOCK_REMOVED",
        resource_type="block",
        resource_id=target_id,
    )

    return MessageResponse(message="User unblocked successfully")


# ── Report (§29) ──

@router.post("/report", response_model=MessageResponse)
async def report_user(
    request: ReportRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Report a user for safety violations."""
    if user_id == request.reported_user_id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")

    await report_repository.create_report(
        reporter_id=user_id,
        reported_user_id=request.reported_user_id,
        reason=request.reason,
        description=request.description,
    )

    return MessageResponse(message="Report submitted successfully")


# ── Account Deletion (§30) ──

@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    user_id: str = Depends(get_current_user_id),
):
    """
    §30 — Full account deletion.
    Revokes all shares, sessions, tokens, and deletes all user data.
    """
    # Revoke all active sharing
    await sharing_repository.revoke_all_for_user(user_id)

    # Revoke all sessions
    await session_repository.revoke_all_for_user(user_id)

    # Delete all user data
    await location_repository.delete_live_location(user_id)
    await location_repository.delete_all_history(user_id)
    await device_token_repository.delete_all_for_user(user_id)
    await emergency_contact_repository.delete_all_for_user(user_id)
    await block_repository.delete_all_for_user(user_id)
    await report_repository.delete_all_for_user(user_id)
    await geofence_state_repository.delete_all_for_user(user_id)

    # Audit before deletion
    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="ACCOUNT_DELETED",
        resource_type="user",
        resource_id=user_id,
    )

    # Delete the user
    await user_repository.delete_user(user_id)

    return MessageResponse(message="Account deleted successfully")
