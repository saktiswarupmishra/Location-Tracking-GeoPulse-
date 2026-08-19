"""
GeoPulse — Geofence State Repository (§19)

Persistent geofence state — replaces in-memory state dict.
Survives server restarts and supports horizontal scaling.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config.database import get_database


async def get_state(user_id: str, geofence_id: str) -> Optional[Dict[str, Any]]:
    """Get the current state for a user/geofence pair."""
    db = get_database()
    return await db.geofence_states.find_one({
        "userId": user_id,
        "geofenceId": geofence_id,
    })


async def update_state(
    user_id: str,
    geofence_id: str,
    is_inside: bool,
) -> None:
    """Upsert the geofence state for a user/geofence pair."""
    db = get_database()
    now = datetime.now(timezone.utc)
    await db.geofence_states.update_one(
        {"userId": user_id, "geofenceId": geofence_id},
        {
            "$set": {
                "isInside": is_inside,
                "lastTransitionAt": now,
                "updatedAt": now,
            },
            "$setOnInsert": {
                "userId": user_id,
                "geofenceId": geofence_id,
                "createdAt": now,
            },
        },
        upsert=True,
    )


async def get_user_states(user_id: str) -> list[Dict[str, Any]]:
    """Get all geofence states for a user."""
    db = get_database()
    cursor = db.geofence_states.find({"userId": user_id})
    return await cursor.to_list(length=100)


async def delete_for_geofence(geofence_id: str) -> int:
    """Delete state records when a geofence is deleted."""
    db = get_database()
    result = await db.geofence_states.delete_many({"geofenceId": geofence_id})
    return result.deleted_count


async def delete_all_for_user(user_id: str) -> int:
    """Delete all geofence states for a user (account deletion)."""
    db = get_database()
    result = await db.geofence_states.delete_many({"userId": user_id})
    return result.deleted_count
