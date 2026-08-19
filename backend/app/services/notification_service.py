"""
GeoPulse — Notification Service

Creates notifications in MongoDB and publishes real-time
events via Redis for WebSocket delivery.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.config.redis import get_redis
from app.repositories import notification_repository

logger = logging.getLogger("geopulse.notification")


async def send_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a notification and publish it for real-time delivery.
    """
    # Store in MongoDB
    notif = await notification_repository.create_notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        data=data,
    )

    # Publish to Redis for WebSocket delivery
    try:
        redis = get_redis()
        await redis.publish(
            f"notifications:{user_id}",
            json.dumps({
                "event": "NOTIFICATION",
                "notification": {
                    "id": str(notif["_id"]),
                    "type": notification_type,
                    "title": title,
                    "message": message,
                    "data": data or {},
                    "created_at": notif["createdAt"].isoformat(),
                },
            }),
        )
    except Exception as e:
        logger.warning("Failed to publish notification: %s", e)

    return notif


async def get_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get notifications with unread count."""
    notifs = await notification_repository.get_notifications(
        user_id, unread_only=unread_only, limit=limit,
    )
    unread_count = await notification_repository.get_unread_count(user_id)

    formatted = []
    for n in notifs:
        formatted.append({
            "id": str(n["_id"]),
            "user_id": n["userId"],
            "type": n["type"],
            "title": n["title"],
            "message": n["message"],
            "data": n.get("data", {}),
            "is_read": n.get("isRead", False),
            "created_at": n.get("createdAt"),
        })

    return {"notifications": formatted, "unread_count": unread_count}


async def mark_read(user_id: str, notification_id: str) -> bool:
    """Mark a notification as read."""
    return await notification_repository.mark_read(notification_id, user_id)


async def mark_all_read(user_id: str) -> int:
    """Mark all notifications as read."""
    return await notification_repository.mark_all_read(user_id)
