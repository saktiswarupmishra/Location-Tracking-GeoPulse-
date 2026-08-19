"""
GeoPulse — Device Token Repository (§23)

Manages push notification device tokens (FCM/APNs).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config.database import get_database


async def register_token(
    user_id: str,
    device_id: str,
    push_token: str,
    platform: str,
) -> Dict[str, Any]:
    """Register or update a push notification token."""
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.device_tokens.update_one(
        {"userId": user_id, "deviceId": device_id},
        {
            "$set": {
                "userId": user_id,
                "deviceId": device_id,
                "pushToken": push_token,
                "platform": platform,
                "isActive": True,
                "updatedAt": now,
            },
            "$setOnInsert": {"createdAt": now},
        },
        upsert=True,
    )
    return {"userId": user_id, "deviceId": device_id, "registered": True}


async def deactivate_token(user_id: str, device_id: str) -> bool:
    """Deactivate a device token."""
    db = get_database()
    result = await db.device_tokens.update_one(
        {"userId": user_id, "deviceId": device_id},
        {"$set": {"isActive": False, "updatedAt": datetime.now(timezone.utc)}},
    )
    return result.modified_count > 0


async def get_active_tokens(user_id: str) -> List[Dict[str, Any]]:
    """Get all active push tokens for a user."""
    db = get_database()
    cursor = db.device_tokens.find({"userId": user_id, "isActive": True})
    return await cursor.to_list(length=20)


async def delete_all_for_user(user_id: str) -> int:
    """Delete all device tokens for a user (account deletion)."""
    db = get_database()
    result = await db.device_tokens.delete_many({"userId": user_id})
    return result.deleted_count
