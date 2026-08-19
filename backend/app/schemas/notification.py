"""
GeoPulse — Notification Schemas
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class NotificationType(str, Enum):
    LOCATION_REQUEST = "LOCATION_REQUEST"
    REQUEST_ACCEPTED = "REQUEST_ACCEPTED"
    REQUEST_REJECTED = "REQUEST_REJECTED"
    LOCATION_STARTED = "LOCATION_STARTED"
    LOCATION_STOPPED = "LOCATION_STOPPED"
    SOS = "SOS"
    GEOFENCE_ENTER = "GEOFENCE_ENTER"
    GEOFENCE_EXIT = "GEOFENCE_EXIT"


class NotificationResponse(BaseModel):
    """A single notification."""
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any] = {}
    is_read: bool = False
    created_at: Optional[datetime] = None


class NotificationListResponse(BaseModel):
    """List of notifications."""
    notifications: List[NotificationResponse] = []
    unread_count: int = 0
