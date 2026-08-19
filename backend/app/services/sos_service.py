"""
GeoPulse — SOS / Emergency Service

Handles SOS trigger, emergency contact management,
and emergency alert notifications.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.config.database import get_database
from app.config.redis import get_redis
from app.repositories import location_repository, user_repository
from app.services import notification_service

logger = logging.getLogger("geopulse.sos")


async def trigger_sos(user_id: str, message: str | None = None) -> Dict[str, Any]:
    """
    Trigger an SOS alert:
    1. Get the user's latest available location
    2. Send emergency notification to all emergency contacts
    3. Record the SOS event
    4. Publish WebSocket SOS event
    """
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Get latest location (may be None)
    location = await location_repository.get_live_location(user_id)
    lat = None
    lon = None
    accuracy = None
    if location:
        coords = location.get("location", {}).get("coordinates", [])
        if len(coords) >= 2:
            lon, lat = coords[0], coords[1]
        accuracy = location.get("accuracy")

    now = datetime.now(timezone.utc)

    # Record SOS event
    db = get_database()
    sos_doc = {
        "userId": user_id,
        "latitude": lat,
        "longitude": lon,
        "accuracy": accuracy,
        "message": message,
        "triggeredAt": now,
    }
    result = await db.sos_events.insert_one(sos_doc)
    sos_id = str(result.inserted_id)

    # Notify emergency contacts
    emergency_contacts = user.get("emergencyContacts", [])
    user_name = user.get("name", "Unknown")

    for contact_id in emergency_contacts:
        await notification_service.send_notification(
            user_id=contact_id,
            notification_type="SOS",
            title="🚨 Emergency Alert",
            message=f"{user_name} has triggered an SOS alert!",
            data={
                "sosId": sos_id,
                "userId": user_id,
                "userName": user_name,
                "latitude": lat,
                "longitude": lon,
                "accuracy": accuracy,
                "message": message,
                "triggeredAt": now.isoformat(),
            },
        )

    # Publish via Redis for WebSocket
    try:
        redis = get_redis()
        for contact_id in emergency_contacts:
            await redis.publish(
                f"sos:{contact_id}",
                json.dumps({
                    "event": "SOS_TRIGGERED",
                    "userId": user_id,
                    "userName": user_name,
                    "latitude": lat,
                    "longitude": lon,
                    "accuracy": accuracy,
                    "message": message,
                    "triggeredAt": now.isoformat(),
                }),
            )
    except Exception as e:
        logger.warning("Failed to publish SOS event: %s", e)

    logger.warning("🚨 SOS triggered by user %s (%s)", user_id, user_name)

    return {
        "id": sos_id,
        "user_id": user_id,
        "user_name": user_name,
        "latitude": lat,
        "longitude": lon,
        "accuracy": accuracy,
        "message": message,
        "triggered_at": now,
        "emergency_contacts_notified": len(emergency_contacts),
    }


async def get_emergency_contacts(user_id: str) -> List[Dict[str, Any]]:
    """Get the user's emergency contacts with profile details."""
    contact_ids = await user_repository.get_emergency_contacts(user_id)
    contacts = []
    for cid in contact_ids:
        contact = await user_repository.find_by_id(cid)
        if contact:
            contacts.append({
                "id": str(contact["_id"]),
                "name": contact["name"],
                "phone": contact["phone"],
                "profile_image": contact.get("profileImage"),
            })
    return contacts


async def set_emergency_contacts(user_id: str, contact_ids: List[str]) -> List[str]:
    """Set the user's emergency contacts."""
    # Validate all contact IDs exist
    valid_ids = []
    for cid in contact_ids:
        contact = await user_repository.find_by_id(cid)
        if contact:
            valid_ids.append(cid)

    await user_repository.set_emergency_contacts(user_id, valid_ids)
    return valid_ids
