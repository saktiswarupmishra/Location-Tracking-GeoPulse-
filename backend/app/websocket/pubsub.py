"""
GeoPulse — Redis Pub/Sub Listener for WebSocket

Each connected user gets a background task that subscribes
to their relevant Redis channels and forwards messages
to the WebSocket.

Channels per user:
- location:{tracked_user_id}  — live location updates from users they're authorized to view
- sharing:{user_id}           — sharing status changes
- notifications:{user_id}     — real-time notifications
- sos:{user_id}               — SOS alerts
- geofence:{user_id}          — geofence events
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Dict

from app.config.redis import get_redis
from app.repositories import sharing_repository

if TYPE_CHECKING:
    from app.websocket.manager import ConnectionManager

logger = logging.getLogger("geopulse.ws.pubsub")

# Track active subscriber tasks: user_id → asyncio.Task
_subscriber_tasks: Dict[str, asyncio.Task] = {}


async def start_user_subscriber(
    user_id: str,
    manager: "ConnectionManager",
) -> None:
    """
    Subscribe to all relevant Redis channels for a connected user
    and forward messages to their WebSocket.
    """
    try:
        redis = get_redis()
        pubsub = redis.pubsub()

        # Subscribe to user-specific channels
        channels = [
            f"sharing:{user_id}",
            f"notifications:{user_id}",
            f"sos:{user_id}",
            f"geofence:{user_id}",
        ]

        # Subscribe to location channels for users this person can view
        try:
            from app.repositories import sharing_repository as sr
            viewable_owners = await _get_viewable_owners(user_id)
            for owner_id in viewable_owners:
                channels.append(f"location:{owner_id}")
        except Exception as e:
            logger.warning("Failed to get viewable owners for %s: %s", user_id, e)

        await pubsub.subscribe(*channels)
        logger.info("Redis subscriber started for %s on %d channels", user_id, len(channels))

        # Listen loop
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                payload = json.loads(data)

                # Forward to the user's WebSocket
                sent = await manager.send_to_user(user_id, payload)
                if not sent:
                    # User disconnected, stop listening
                    break
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Error processing Redis message for %s: %s", user_id, e)

    except asyncio.CancelledError:
        logger.info("Redis subscriber cancelled for %s", user_id)
    except Exception as e:
        logger.error("Redis subscriber error for %s: %s", user_id, e)
    finally:
        try:
            await pubsub.unsubscribe()
            await pubsub.close()
        except Exception:
            pass


async def stop_user_subscriber(user_id: str) -> None:
    """Cancel the subscriber task for a user."""
    task = _subscriber_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()


async def _get_viewable_owners(user_id: str) -> list[str]:
    """Get all user IDs whose location this user can view."""
    from app.config.database import get_database
    from datetime import datetime, timezone

    db = get_database()
    now = datetime.now(timezone.utc)
    cursor = db.location_shares.find(
        {
            "viewerId": user_id,
            "status": "accepted",
            "permissions.liveLocation": True,
            "$or": [
                {"expiresAt": None},
                {"expiresAt": {"$gt": now}},
            ],
        },
        {"ownerId": 1},
    )
    docs = await cursor.to_list(length=500)
    return [doc["ownerId"] for doc in docs]
