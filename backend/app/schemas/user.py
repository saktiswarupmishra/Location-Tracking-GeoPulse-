"""
GeoPulse — User Schemas

Pydantic v2 models for user profile, search, and privacy.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Discoverability(str, Enum):
    EVERYONE = "everyone"
    CONTACTS = "contacts"
    NOBODY = "nobody"


class PrivacySettings(BaseModel):
    """User privacy preferences."""
    discoverability: Discoverability = Discoverability.EVERYONE
    location_sharing_enabled: bool = True


class UserProfile(BaseModel):
    """Full user profile returned to the authenticated user."""
    id: str
    phone: str
    name: str
    profile_image: Optional[str] = None
    email: Optional[str] = None
    is_online: bool = False
    last_active: Optional[datetime] = None
    privacy_settings: PrivacySettings = PrivacySettings()
    emergency_contacts: List[str] = []
    created_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Fields a user can update on their own profile."""
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    profile_image: Optional[str] = None
    privacy_settings: Optional[PrivacySettings] = None


class UserSearchResult(BaseModel):
    """
    Minimal information returned when searching by phone number.
    Must NOT include location, GPS, address, or movement data.
    """
    id: str
    name: str
    profile_image: Optional[str] = None
    is_online: bool = False
