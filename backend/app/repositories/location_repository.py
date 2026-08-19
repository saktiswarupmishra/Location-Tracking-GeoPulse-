"""
GeoPulse — Location Repository (v1.1 Hardened)

PyMongo Async. Stores server timestamps, sequence numbers,
integrity status, and accuracy level on all location records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.config.database import get_database


# ──────────────────────────────────────────
# Live Location
# ──────────────────────────────────────────

async def upsert_live_location(user_id: str, data: Dict[str, Any]) -> None:
    """
    Insert or update the current live location for a user.
    Uses upsert so there is always exactly one document per user.
    Includes server timestamp (§5), integrity status (§10), accuracy level (§9).
    """
    db = get_database()
    now = datetime.now(timezone.utc)
    await db.live_locations.update_one(
        {"userId": user_id},
        {
            "$set": {
                "userId": user_id,
                "location": {
                    "type": "Point",
                    "coordinates": [data["longitude"], data["latitude"]],
                },
                "accuracy": data.get("accuracy"),
                "accuracyLevel": data.get("accuracy_level", "unknown"),
                "speed": data.get("speed"),
                "heading": data.get("heading"),
                "altitude": data.get("altitude"),
                "clientTimestamp": data.get("timestamp"),
                "serverTimestamp": data.get("server_timestamp", now),
                "sequence": data.get("sequence", 0),
                "integrityStatus": data.get("integrity_status", "clean"),
                "sessionId": data.get("session_id"),
                "updatedAt": now,
            }
        },
        upsert=True,
    )


async def get_live_location(user_id: str) -> Optional[Dict[str, Any]]:
    """Get the current live location for a user."""
    db = get_database()
    return await db.live_locations.find_one({"userId": user_id})


async def delete_live_location(user_id: str) -> None:
    """Remove a user's live location (when sharing stops)."""
    db = get_database()
    await db.live_locations.delete_one({"userId": user_id})


# ──────────────────────────────────────────
# Location History
# ──────────────────────────────────────────

async def save_history_point(user_id: str, data: Dict[str, Any]) -> None:
    """Append a location point to the user's history with server timestamp."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "userId": user_id,
        "location": {
            "type": "Point",
            "coordinates": [data["longitude"], data["latitude"]],
        },
        "accuracy": data.get("accuracy"),
        "accuracyLevel": data.get("accuracy_level", "unknown"),
        "speed": data.get("speed"),
        "heading": data.get("heading"),
        "clientTimestamp": data.get("timestamp"),
        "serverTimestamp": data.get("server_timestamp", now),
        "sequence": data.get("sequence", 0),
        "integrityStatus": data.get("integrity_status", "clean"),
        "sessionId": data.get("session_id"),
    }
    await db.location_history.insert_one(doc)


async def get_history(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Retrieve location history for a user within a date range."""
    db = get_database()
    query: Dict[str, Any] = {"userId": user_id}
    if start_date or end_date:
        ts_filter: Dict[str, Any] = {}
        if start_date:
            ts_filter["$gte"] = start_date
        if end_date:
            ts_filter["$lte"] = end_date
        query["serverTimestamp"] = ts_filter

    cursor = db.location_history.find(query).sort("serverTimestamp", 1).limit(limit)
    return await cursor.to_list(length=limit)


async def delete_history(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> int:
    """Delete location history for a user (optionally within a date range)."""
    db = get_database()
    query: Dict[str, Any] = {"userId": user_id}
    if start_date or end_date:
        ts_filter: Dict[str, Any] = {}
        if start_date:
            ts_filter["$gte"] = start_date
        if end_date:
            ts_filter["$lte"] = end_date
        query["serverTimestamp"] = ts_filter

    result = await db.location_history.delete_many(query)
    return result.deleted_count


async def delete_all_history(user_id: str) -> int:
    """Delete ALL location history for a user."""
    db = get_database()
    result = await db.location_history.delete_many({"userId": user_id})
    return result.deleted_count
