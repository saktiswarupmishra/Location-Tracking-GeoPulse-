"""
GeoPulse — Location Sharing Schemas

Pydantic v2 models for sharing requests, permissions, and status.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SharingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVOKED = "revoked"
    EXPIRED = "expired"


class SharingPermissions(BaseModel):
    """What the viewer is allowed to see."""
    live_location: bool = True
    location_history: bool = False


class SharingDuration(str, Enum):
    """Pre-defined sharing durations."""
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    EIGHT_HOURS = "8h"
    UNTIL_STOPPED = "until_stopped"


class CreateSharingRequest(BaseModel):
    """Request to share location with another user."""
    target_phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Phone number of the person to share with",
    )
    permissions: SharingPermissions = SharingPermissions()
    duration: SharingDuration = SharingDuration.UNTIL_STOPPED


class SharingResponse(BaseModel):
    """A single sharing relationship."""
    id: str
    owner_id: str
    viewer_id: str
    owner_name: Optional[str] = None
    viewer_name: Optional[str] = None
    status: SharingStatus
    permissions: SharingPermissions
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class SharingListResponse(BaseModel):
    """List of sharing relationships."""
    incoming: list[SharingResponse] = []
    outgoing: list[SharingResponse] = []
