"""
GeoPulse — Location Schemas (v1.1 Hardened)

Pydantic v2 models for GPS coordinates, location updates, freshness, and history.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class GeoJSONPoint(BaseModel):
    """MongoDB GeoJSON Point — coordinates are [longitude, latitude]."""
    type: str = "Point"
    coordinates: List[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="[longitude, latitude]",
    )

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[float]) -> List[float]:
        lon, lat = v
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        return v


class LocationUpdate(BaseModel):
    """Incoming location update from the mobile client."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0, description="Accuracy in meters")
    speed: Optional[float] = Field(None, ge=0, description="Speed in m/s")
    heading: Optional[float] = Field(None, ge=0, le=360, description="Heading in degrees")
    altitude: Optional[float] = None
    timestamp: Optional[datetime] = None
    sequence: int = Field(default=0, ge=0)
    battery_level: Optional[float] = None
    is_charging: Optional[bool] = None

    def to_geojson(self) -> GeoJSONPoint:
        """Convert lat/lng to GeoJSON Point (lon, lat order)."""
        return GeoJSONPoint(coordinates=[self.longitude, self.latitude])


class LocationResponse(BaseModel):
    """Location data returned to an authorized viewer."""
    user_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    accuracy_level: Optional[str] = "unknown"
    speed: Optional[float] = None
    heading: Optional[float] = None
    altitude: Optional[float] = None
    timestamp: Optional[datetime] = None
    sequence: Optional[int] = 0
    integrity_status: Optional[str] = "clean"
    freshness_status: Optional[str] = "live"
    session_id: Optional[str] = None
    is_live: bool = True
    updated_at: Optional[datetime] = None


class LocationHistoryPoint(BaseModel):
    """A single point in location history."""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    accuracy_level: Optional[str] = "unknown"
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: Optional[datetime] = None
    integrity_status: Optional[str] = "clean"


class LocationHistoryResponse(BaseModel):
    """Location history for a date range."""
    user_id: str
    points: List[LocationHistoryPoint] = []
    total_points: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class LocationHistoryQuery(BaseModel):
    """Query parameters for location history."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=1000, le=5000)
