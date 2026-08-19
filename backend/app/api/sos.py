"""
GeoPulse — SOS / Emergency API Routes

POST /api/v1/sos/trigger
GET  /api/v1/sos/contacts
PUT  /api/v1/sos/contacts
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config.security import get_current_user_id
from app.schemas.sos import EmergencyContactsUpdate, SOSTriggerRequest
from app.services import sos_service

router = APIRouter(prefix="/api/v1/sos", tags=["SOS / Emergency"])


@router.post("/trigger", response_model=dict)
async def trigger_sos(
    request: SOSTriggerRequest | None = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    Trigger an SOS emergency alert.

    Sends the user's current location to all configured
    emergency contacts.
    """
    message = request.message if request else None
    result = await sos_service.trigger_sos(user_id, message)
    return result


@router.get("/contacts", response_model=list)
async def get_emergency_contacts(user_id: str = Depends(get_current_user_id)):
    """Get the user's emergency contacts."""
    return await sos_service.get_emergency_contacts(user_id)


@router.put("/contacts", response_model=dict)
async def set_emergency_contacts(
    request: EmergencyContactsUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Set the user's emergency contacts."""
    valid_ids = await sos_service.set_emergency_contacts(user_id, request.contact_ids)
    return {
        "message": "Emergency contacts updated",
        "contacts": valid_ids,
    }
