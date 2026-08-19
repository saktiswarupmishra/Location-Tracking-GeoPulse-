"""
GeoPulse — Emergency Contact Repository (§22)

Dedicated emergency_contacts collection with priority support.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from bson import ObjectId

from app.config.database import get_database


async def add_contact(
    owner_id: str,
    contact_user_id: str,
    priority: int = 0,
) -> Dict[str, Any]:
    """Add an emergency contact."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "ownerId": owner_id,
        "contactUserId": contact_user_id,
        "priority": priority,
        "createdAt": now,
    }
    await db.emergency_contacts.update_one(
        {"ownerId": owner_id, "contactUserId": contact_user_id},
        {"$setOnInsert": doc},
        upsert=True,
    )
    return doc


async def remove_contact(owner_id: str, contact_user_id: str) -> bool:
    """Remove an emergency contact."""
    db = get_database()
    result = await db.emergency_contacts.delete_one({
        "ownerId": owner_id,
        "contactUserId": contact_user_id,
    })
    return result.deleted_count > 0


async def get_contacts(owner_id: str) -> List[Dict[str, Any]]:
    """Get all emergency contacts, ordered by priority."""
    db = get_database()
    cursor = db.emergency_contacts.find(
        {"ownerId": owner_id}
    ).sort("priority", 1)
    return await cursor.to_list(length=20)


async def get_contact_user_ids(owner_id: str) -> List[str]:
    """Get just the user IDs of emergency contacts."""
    contacts = await get_contacts(owner_id)
    return [c["contactUserId"] for c in contacts]


async def delete_all_for_user(owner_id: str) -> int:
    """Delete all emergency contacts for a user (account deletion)."""
    db = get_database()
    result = await db.emergency_contacts.delete_many({
        "$or": [{"ownerId": owner_id}, {"contactUserId": owner_id}]
    })
    return result.deleted_count
