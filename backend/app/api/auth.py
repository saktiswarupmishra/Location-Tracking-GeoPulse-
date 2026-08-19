"""
GeoPulse — Auth API Routes (v1.1 Hardened)

POST /api/v1/auth/send-otp
POST /api/v1/auth/verify-otp
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/ws-ticket
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config.security import get_current_user_id
from app.schemas.auth import (
    MessageResponse,
    RefreshRequest,
    SendOTPRequest,
    TokenResponse,
    VerifyOTPRequest,
    WsTicketResponse,
)
from app.services import auth_service, ws_ticket_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/send-otp", response_model=MessageResponse)
async def send_otp(request: SendOTPRequest):
    """Send an OTP to the given phone number."""
    result = await auth_service.send_otp(request.phone)
    detail = result.get("dev_code")
    return MessageResponse(message=result["message"], detail=detail)


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and return JWT tokens with device session tracking."""
    tokens, is_new = await auth_service.verify_otp(
        phone=request.phone,
        code=request.code,
        name=request.name,
        device_id=request.device_id,
        platform=request.platform,
    )
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        is_new_user=is_new,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: RefreshRequest):
    """Refresh access token using a refresh token (§13 rotation)."""
    tokens = await auth_service.refresh_tokens(request.refresh_token)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshRequest | None = None,
    user_id: str = Depends(get_current_user_id),
):
    """Logout and invalidate the refresh token."""
    refresh_token = request.refresh_token if request else None
    await auth_service.logout(user_id, refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.post("/ws-ticket", response_model=WsTicketResponse)
async def get_ws_ticket(
    user_id: str = Depends(get_current_user_id),
):
    """§15 — Issue a short-lived one-time WebSocket ticket."""
    ticket = await ws_ticket_service.create_ticket(user_id)
    return WsTicketResponse(ticket=ticket)
