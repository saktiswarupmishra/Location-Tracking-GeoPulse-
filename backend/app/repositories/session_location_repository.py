"""
GeoPulse — Location Session Repository (§2)

Manages location tracking sessions. A session represents
an active period of location sharing between two users.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from ulid import ULID

from app.config.database import get_database


async def start_session(
    owner_id: str,
    sharing_id: str,
) -> Dict[str, Any]:
    """Start a new location tracking session."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "sessionId": str(ULID()),
        "ownerId": owner_id,
        "sharingId": sharing_id,
        "status": "active",  # active | paused | stopped
        "startedAt": now,
        "lastLocationAt": None,
        "stoppedAt": None,
        "pausedAt": None,
        "resumedAt": None,
        "lastSequence": 0,
        "totalUpdates": 0,
    }
    result = await db.location_sessions.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def find_active_session(owner_id: str) -> Optional[Dict[str, Any]]:
    """Find the current active session for a user."""
    db = get_database()
    return await db.location_sessions.find_one({
        "ownerId": owner_id,
        "status": {"$in": ["active", "paused"]},
    })


async def find_by_session_id(session_id: str) -> Optional[Dict[str, Any]]:
    """Find a session by its ULID session ID."""
    db = get_database()
    return await db.location_sessions.find_one({"sessionId": session_id})


async def stop_session(owner_id: str) -> bool:
    """Stop the active session for a user."""
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.location_sessions.update_one(
        {"ownerId": owner_id, "status": {"$in": ["active", "paused"]}},
        {"$set": {"status": "stopped", "stoppedAt": now}},
    )
    return result.modified_count > 0


async def pause_session(owner_id: str) -> bool:
    """Pause the active session (background mode)."""
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.location_sessions.update_one(
        {"ownerId": owner_id, "status": "active"},
        {"$set": {"status": "paused", "pausedAt": now}},
    )
    return result.modified_count > 0


async def resume_session(owner_id: str) -> bool:
    """Resume a paused session."""
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.location_sessions.update_one(
        {"ownerId": owner_id, "status": "paused"},
        {"$set": {"status": "active", "resumedAt": now}},
    )
    return result.modified_count > 0


async def update_session_location(
    owner_id: str,
    sequence: int,
) -> bool:
    """Update the session with latest location metadata."""
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.location_sessions.update_one(
        {"ownerId": owner_id, "status": "active"},
        {
            "$set": {"lastLocationAt": now, "lastSequence": sequence},
            "$inc": {"totalUpdates": 1},
        },
    )
    return result.modified_count > 0


async def stop_all_for_sharing(sharing_id: str) -> int:
    """Stop all sessions linked to a sharing relationship."""
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.location_sessions.update_many(
        {"sharingId": sharing_id, "status": {"$in": ["active", "paused"]}},
        {"$set": {"status": "stopped", "stoppedAt": now}},
    )
    return result.modified_count
