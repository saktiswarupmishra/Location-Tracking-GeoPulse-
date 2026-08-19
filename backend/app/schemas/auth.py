"""
GeoPulse — Authentication Schemas (v1.1 Hardened)

Pydantic v2 models for OTP, tokens, device sessions, and WS tickets.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SendOTPRequest(BaseModel):
    """Request to send an OTP to a phone number."""
    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        examples=["+919876543210"],
        description="Phone number in E.164 format",
    )


class VerifyOTPRequest(BaseModel):
    """Request to verify an OTP code."""
    phone: str = Field(..., min_length=10, max_length=15)
    code: str = Field(..., min_length=4, max_length=8)
    name: str | None = Field(
        None,
        max_length=100,
        description="Display name — required for new registrations",
    )
    device_id: str | None = Field(
        None,
        max_length=128,
        description="Unique device identifier",
    )
    platform: str | None = Field(
        None,
        max_length=20,
        description="Device platform: android, ios, web",
    )


class TokenResponse(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


class RefreshRequest(BaseModel):
    """Request to refresh an access token."""
    refresh_token: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    detail: str | None = None


class WsTicketResponse(BaseModel):
    """WebSocket ticket response (§15)."""
    ticket: str
