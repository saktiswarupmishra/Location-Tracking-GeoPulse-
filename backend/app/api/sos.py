"""
GeoPulse — SOS / Emergency API Routes (v1.1 Hardened)

POST   /api/v1/sos/trigger
POST   /api/v1/sos
POST   /api/v1/sos/{id}/acknowledge
POST   /api/v1/sos/{id}/resolve
GET    /api/v1/sos/active
GET    /api/v1/sos/contacts
POST   /api/v1/sos/contacts
DELETE /api/v1/sos/contacts/{contact_id}
PUT    /api/v1/sos/contacts
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.config.security import get_current_user_id
from app.schemas.sos import EmergencyContactsUpdate, SOSTriggerRequest
from app.services import sos_service

router = APIRouter(prefix="/api/v1/sos", tags=["SOS / Emergency"])


class AddContactRequest(BaseModel):
    contact_user_id: str
    priority: int = 0


class MessageResponse(BaseModel):
    message: str


@router.post("/trigger", response_model=dict)
@router.post("", response_model=dict)
async def trigger_sos(
    request: SOSTriggerRequest | None = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    Trigger an SOS emergency alert.
    Sends live location to all emergency contacts via Push, Notification, and WebSocket.
    """
    message = request.message if request else None
    lat = request.latitude if request and hasattr(request, "latitude") else None
    lon = request.longitude if request and hasattr(request, "longitude") else None
    return await sos_service.trigger_sos(user_id, message=message, latitude=lat, longitude=lon)


@router.post("/{sos_id}/acknowledge", response_model=dict)
async def acknowledge_sos(
    sos_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Acknowledge receipt of an active SOS alert."""
    return await sos_service.acknowledge_sos(sos_id, user_id)


@router.post("/{sos_id}/resolve", response_model=dict)
async def resolve_sos(
    sos_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Resolve an active SOS alert."""
    return await sos_service.resolve_sos(sos_id, user_id)


@router.get("/active", response_model=list)
async def get_active_sos(
    user_id: str = Depends(get_current_user_id),
):
    """List active SOS alerts involving user or their emergency contacts."""
    return await sos_service.get_active_sos(user_id)


@router.get("/contacts", response_model=list)
async def get_emergency_contacts(user_id: str = Depends(get_current_user_id)):
    """Get the user's emergency contacts."""
    return await sos_service.get_emergency_contacts(user_id)


@router.post("/contacts", response_model=dict)
async def add_emergency_contact(
    request: AddContactRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Add a single emergency contact."""
    return await sos_service.add_emergency_contact(user_id, request.contact_user_id, request.priority)


@router.delete("/contacts/{contact_id}", response_model=dict)
async def remove_emergency_contact(
    contact_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Remove a single emergency contact."""
    return await sos_service.remove_emergency_contact(user_id, contact_id)


@router.put("/contacts", response_model=dict)
async def set_emergency_contacts(
    request: EmergencyContactsUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Set the full list of emergency contacts."""
    valid_ids = await sos_service.set_emergency_contacts(user_id, request.contact_ids)
    return {
        "message": "Emergency contacts updated",
        "contacts": valid_ids,
    }
