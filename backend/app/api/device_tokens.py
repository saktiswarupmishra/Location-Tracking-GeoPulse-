"""
GeoPulse — Device Token API Routes (§23)

POST   /api/v1/devices/token — register push notification token
DELETE /api/v1/devices/token — deactivate token
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.config.security import get_current_user_id
from app.repositories import device_token_repository

router = APIRouter(prefix="/api/v1/devices", tags=["Device Tokens"])


class RegisterTokenRequest(BaseModel):
    device_id: str = Field(..., max_length=128)
    push_token: str = Field(..., max_length=512)
    platform: str = Field(..., max_length=20)  # android, ios


class DeactivateTokenRequest(BaseModel):
    device_id: str = Field(..., max_length=128)


class MessageResponse(BaseModel):
    message: str


@router.post("/token", response_model=MessageResponse)
async def register_token(
    request: RegisterTokenRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Register a push notification device token."""
    await device_token_repository.register_token(
        user_id=user_id,
        device_id=request.device_id,
        push_token=request.push_token,
        platform=request.platform,
    )
    return MessageResponse(message="Device token registered")


@router.delete("/token", response_model=MessageResponse)
async def deactivate_token(
    request: DeactivateTokenRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Deactivate a push notification device token."""
    await device_token_repository.deactivate_token(
        user_id=user_id,
        device_id=request.device_id,
    )
    return MessageResponse(message="Device token deactivated")
