"""
GeoPulse — SOS / Emergency Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SOSTriggerRequest(BaseModel):
    """Request to trigger an SOS alert."""
    message: Optional[str] = None


class SOSAlert(BaseModel):
    """SOS alert sent to emergency contacts."""
    id: str
    user_id: str
    user_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    message: Optional[str] = None
    triggered_at: datetime


class EmergencyContactsUpdate(BaseModel):
    """Update emergency contact list."""
    contact_ids: List[str]
