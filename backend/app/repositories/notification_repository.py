"""
GeoPulse — Notification Repository

Data-access layer for the `notifications` collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.config.database import get_database


async def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new notification."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "userId": user_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "data": data or {},
        "isRead": False,
        "createdAt": now,
    }
    result = await db.notifications.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get notifications for a user."""
    db = get_database()
    query: Dict[str, Any] = {"userId": user_id}
    if unread_only:
        query["isRead"] = False
    cursor = db.notifications.find(query).sort("createdAt", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_unread_count(user_id: str) -> int:
    """Count unread notifications."""
    db = get_database()
    return await db.notifications.count_documents({"userId": user_id, "isRead": False})


async def mark_read(notification_id: str, user_id: str) -> bool:
    """Mark a single notification as read."""
    db = get_database()
    result = await db.notifications.update_one(
        {"_id": ObjectId(notification_id), "userId": user_id},
        {"$set": {"isRead": True}},
    )
    return result.modified_count > 0


async def mark_all_read(user_id: str) -> int:
    """Mark all notifications as read."""
    db = get_database()
    result = await db.notifications.update_many(
        {"userId": user_id, "isRead": False},
        {"$set": {"isRead": True}},
    )
    return result.modified_count
