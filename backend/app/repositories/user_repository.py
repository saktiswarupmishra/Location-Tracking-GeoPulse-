"""
GeoPulse — User Repository (v1.1 Hardened)

PyMongo Async. Enhanced with privacy settings and
delegated block/emergency contact to dedicated collections.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.config.database import get_database


async def create_user(phone: str, name: str) -> Dict[str, Any]:
    """Create a new user. Returns the inserted document."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "phone": phone,
        "name": name,
        "profileImage": None,
        "email": None,
        "isOnline": False,
        "lastActive": now,
        "privacySettings": {
            "discoverability": "everyone",
            "locationSharingEnabled": True,
            "defaultShareDuration": "until_stopped",
            "showLastActive": True,
        },
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def find_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Find a user by phone number."""
    db = get_database()
    return await db.users.find_one({"phone": phone})


async def find_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Find a user by _id."""
    db = get_database()
    return await db.users.find_one({"_id": ObjectId(user_id)})


async def update_user(user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user fields. Returns the updated document."""
    db = get_database()
    data["updatedAt"] = datetime.now(timezone.utc)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": data},
    )
    return await find_by_id(user_id)


async def set_online_status(user_id: str, is_online: bool) -> None:
    """Update online/offline status and last-active timestamp."""
    db = get_database()
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "isOnline": is_online,
                "lastActive": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            }
        },
    )


async def delete_user(user_id: str) -> None:
    """Delete a user account."""
    db = get_database()
    await db.users.delete_one({"_id": ObjectId(user_id)})
