"""
GeoPulse — SOS / Emergency Service (v1.1 Hardened)

Handles SOS trigger, lifecycle (active → acknowledged → resolved),
emergency contact management (§22), audit logging (§12), and notifications.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId

from fastapi import HTTPException, status

from app.config.database import get_database
from app.config.redis import get_redis
from app.repositories import (
    audit_repository,
    emergency_contact_repository,
    location_repository,
    user_repository,
)
from app.services import notification_service

logger = logging.getLogger("geopulse.sos")


async def trigger_sos(
    user_id: str,
    message: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Dict[str, Any]:
    """
    Trigger an SOS alert (§21):
    1. Get the user's latest available location (or use provided coords)
    2. Record the SOS event with status='active'
    3. Send emergency notification to all emergency contacts
    4. Publish WebSocket SOS event via Redis
    5. Audit log
    """
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    lat = latitude
    lon = longitude
    accuracy = None

    if lat is None or lon is None:
        location = await location_repository.get_live_location(user_id)
        if location:
            coords = location.get("location", {}).get("coordinates", [])
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
            accuracy = location.get("accuracy")

    now = datetime.now(timezone.utc)
    db = get_database()
    sos_doc = {
        "userId": user_id,
        "latitude": lat,
        "longitude": lon,
        "accuracy": accuracy,
        "message": message or "Emergency! I need assistance.",
        "status": "active",  # active | acknowledged | resolved
        "acknowledgedBy": [],
        "triggeredAt": now,
        "resolvedAt": None,
    }
    result = await db.sos_events.insert_one(sos_doc)
    sos_id = str(result.inserted_id)

    # Emergency contacts
    contact_ids = await emergency_contact_repository.get_contact_user_ids(user_id)
    user_name = user.get("name", "Unknown")

    for cid in contact_ids:
        await notification_service.send_notification(
            user_id=cid,
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
                "message": sos_doc["message"],
                "triggeredAt": now.isoformat(),
            },
        )

    # Publish via Redis
    try:
        redis = get_redis()
        event_payload = json.dumps({
            "event": "SOS_ALERT",
            "sosId": sos_id,
            "userId": user_id,
            "userName": user_name,
            "latitude": lat,
            "longitude": lon,
            "accuracy": accuracy,
            "message": sos_doc["message"],
            "triggeredAt": now.isoformat(),
        })
        for cid in contact_ids:
            await redis.publish(f"sos:{cid}", event_payload)
    except Exception as e:
        logger.warning("Failed to publish SOS event: %s", e)

    # Audit log
    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="SOS_TRIGGERED",
        resource_type="sos",
        resource_id=sos_id,
        metadata={"contacts_notified": len(contact_ids), "latitude": lat, "longitude": lon},
    )

    logger.warning("🚨 SOS triggered by user %s (%s)", user_id, user_name)

    return {
        "id": sos_id,
        "user_id": user_id,
        "user_name": user_name,
        "latitude": lat,
        "longitude": lon,
        "accuracy": accuracy,
        "message": sos_doc["message"],
        "status": "active",
        "triggered_at": now,
        "emergency_contacts_notified": len(contact_ids),
    }


async def acknowledge_sos(sos_id: str, ack_user_id: str) -> Dict[str, Any]:
    """Acknowledge an SOS alert by a contact."""
    db = get_database()
    now = datetime.now(timezone.utc)
    res = await db.sos_events.update_one(
        {"_id": ObjectId(sos_id), "status": "active"},
        {
            "$set": {"status": "acknowledged"},
            "$addToSet": {"acknowledgedBy": {"userId": ack_user_id, "timestamp": now}},
        },
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Active SOS event not found")

    await audit_repository.create_audit_log(
        actor_id=ack_user_id,
        action="SOS_ACKNOWLEDGED",
        resource_type="sos",
        resource_id=sos_id,
    )
    return {"message": "SOS acknowledged", "sos_id": sos_id}


async def resolve_sos(sos_id: str, user_id: str) -> Dict[str, Any]:
    """Resolve an SOS alert (by initiator or admin)."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = await db.sos_events.find_one({"_id": ObjectId(sos_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="SOS event not found")

    if doc["userId"] != user_id:
        raise HTTPException(status_code=403, detail="Only the initiator can resolve the SOS")

    await db.sos_events.update_one(
        {"_id": ObjectId(sos_id)},
        {"$set": {"status": "resolved", "resolvedAt": now}},
    )

    # Notify emergency contacts
    contact_ids = await emergency_contact_repository.get_contact_user_ids(user_id)
    user = await user_repository.find_by_id(user_id)
    user_name = user.get("name", "Someone")

    for cid in contact_ids:
        await notification_service.send_notification(
            user_id=cid,
            notification_type="SOS_RESOLVED",
            title="✅ Emergency Resolved",
            message=f"{user_name} has marked the emergency as resolved.",
            data={"sosId": sos_id, "resolvedAt": now.isoformat()},
        )

    # WebSocket event via Redis
    try:
        redis = get_redis()
        event_payload = json.dumps({
            "event": "SOS_RESOLVED",
            "sosId": sos_id,
            "userId": user_id,
            "resolvedAt": now.isoformat(),
        })
        for cid in contact_ids:
            await redis.publish(f"sos:{cid}", event_payload)
    except Exception:
        pass

    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="SOS_RESOLVED",
        resource_type="sos",
        resource_id=sos_id,
    )

    return {"message": "SOS resolved", "sos_id": sos_id, "resolved_at": now}


async def get_active_sos(user_id: str) -> List[Dict[str, Any]]:
    """Get active SOS events for user or emergency contacts."""
    db = get_database()
    # Find events initiated by this user
    cursor = db.sos_events.find({
        "userId": user_id,
        "status": {"$in": ["active", "acknowledged"]},
    }).sort("triggeredAt", -1)
    events = await cursor.to_list(length=10)

    # Also find events where user is emergency contact
    contact_records = await db.emergency_contacts.find({"contactUserId": user_id}).to_list(length=100)
    owner_ids = [c["ownerId"] for c in contact_records]
    if owner_ids:
        cursor2 = db.sos_events.find({
            "userId": {"$in": owner_ids},
            "status": {"$in": ["active", "acknowledged"]},
        }).sort("triggeredAt", -1)
        contact_events = await cursor2.to_list(length=20)
        events.extend(contact_events)

    result = []
    for e in events:
        result.append({
            "id": str(e["_id"]),
            "user_id": e["userId"],
            "latitude": e.get("latitude"),
            "longitude": e.get("longitude"),
            "accuracy": e.get("accuracy"),
            "message": e.get("message"),
            "status": e.get("status"),
            "triggered_at": e.get("triggeredAt"),
        })
    return result


async def get_emergency_contacts(user_id: str) -> List[Dict[str, Any]]:
    """Get the user's emergency contacts with profile details."""
    records = await emergency_contact_repository.get_contacts(user_id)
    contacts = []
    for rec in records:
        contact_user = await user_repository.find_by_id(rec["contactUserId"])
        if contact_user:
            contacts.append({
                "id": str(contact_user["_id"]),
                "name": contact_user["name"],
                "phone": contact_user["phone"],
                "profile_image": contact_user.get("profileImage"),
                "priority": rec.get("priority", 0),
                "created_at": rec.get("createdAt"),
            })
    return contacts


async def add_emergency_contact(owner_id: str, contact_user_id: str, priority: int = 0) -> Dict[str, Any]:
    """Add a single emergency contact."""
    target_user = await user_repository.find_by_id(contact_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    await emergency_contact_repository.add_contact(owner_id, contact_user_id, priority)
    return {"message": "Contact added", "contact_id": contact_user_id}


async def remove_emergency_contact(owner_id: str, contact_user_id: str) -> Dict[str, Any]:
    """Remove a single emergency contact."""
    removed = await emergency_contact_repository.remove_contact(owner_id, contact_user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact removed", "contact_id": contact_user_id}


async def set_emergency_contacts(user_id: str, contact_ids: List[str]) -> List[str]:
    """Set the full list of emergency contacts."""
    await emergency_contact_repository.delete_all_for_user(user_id)
    valid_ids = []
    for i, cid in enumerate(contact_ids):
        contact = await user_repository.find_by_id(cid)
        if contact:
            await emergency_contact_repository.add_contact(user_id, cid, priority=i)
            valid_ids.append(cid)
    return valid_ids
