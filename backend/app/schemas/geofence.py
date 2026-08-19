"""
GeoPulse — Geofence Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GeofenceCreate(BaseModel):
    """Create a new geofence zone."""
    name: str = Field(..., max_length=100, examples=["Home"])
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(..., gt=0, le=50000, examples=[500])


class GeofenceResponse(BaseModel):
    """A geofence zone."""
    id: str
    user_id: str
    name: str
    latitude: float
    longitude: float
    radius_meters: float
    is_active: bool = True
    created_at: Optional[datetime] = None


class GeofenceEvent(BaseModel):
    """Geofence enter/exit event."""
    geofence_id: str
    geofence_name: str
    event_type: str  # "entered" | "exited"
    user_id: str
    timestamp: datetime
