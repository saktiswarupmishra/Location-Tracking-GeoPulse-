"""
GeoPulse — Sessions API Routes (§14)

GET    /api/v1/sessions — list active device sessions
DELETE /api/v1/sessions/{id} — revoke a specific session
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config.security import get_current_user_id
from app.repositories import session_repository, audit_repository

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


class SessionInfo(BaseModel):
    id: str
    device_id: str | None = None
    platform: str | None = None
    last_used_at: str | None = None
    created_at: str | None = None


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]


class MessageResponse(BaseModel):
    message: str


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: str = Depends(get_current_user_id),
):
    """List all active device sessions for the authenticated user."""
    sessions = await session_repository.get_active_sessions(user_id)
    return SessionListResponse(
        sessions=[
            SessionInfo(
                id=str(s["_id"]),
                device_id=s.get("deviceId"),
                platform=s.get("platform"),
                last_used_at=s.get("lastUsedAt", "").isoformat() if s.get("lastUsedAt") else None,
                created_at=s.get("createdAt", "").isoformat() if s.get("createdAt") else None,
            )
            for s in sessions
        ]
    )


@router.delete("/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Revoke a specific device session (remote logout)."""
    revoked = await session_repository.revoke_session(session_id, user_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Session not found")

    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="DEVICE_REMOVED",
        resource_type="session",
        resource_id=session_id,
    )

    return MessageResponse(message="Session revoked successfully")
