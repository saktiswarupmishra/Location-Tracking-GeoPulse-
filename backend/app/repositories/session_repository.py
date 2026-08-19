"""
GeoPulse — Session Repository (§14)

CRUD for user_sessions collection.
Tracks device sessions with refresh token family IDs
for rotation-based theft detection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.config.database import get_database
from app.config.security import hash_token


async def create_session(
    user_id: str,
    refresh_token: str,
    family_id: str,
    device_id: str | None = None,
    platform: str | None = None,
) -> Dict[str, Any]:
    """Create a new device session on login."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "userId": user_id,
        "deviceId": device_id,
        "platform": platform,
        "refreshTokenHash": hash_token(refresh_token),
        "tokenFamilyId": family_id,
        "createdAt": now,
        "lastUsedAt": now,
        "revokedAt": None,
    }
    result = await db.user_sessions.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def find_by_token_hash(token_hash: str) -> Optional[Dict[str, Any]]:
    """Find a session by its hashed refresh token."""
    db = get_database()
    return await db.user_sessions.find_one({"refreshTokenHash": token_hash})


async def find_by_family(family_id: str) -> List[Dict[str, Any]]:
    """Find all sessions in a token family."""
    db = get_database()
    cursor = db.user_sessions.find({"tokenFamilyId": family_id})
    return await cursor.to_list(length=None)


async def rotate_token(
    old_token_hash: str,
    new_refresh_token: str,
    family_id: str,
) -> bool:
    """
    Rotate: mark the old session's token hash as used,
    replace with the new token hash, and update lastUsedAt.
    """
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.user_sessions.update_one(
        {"refreshTokenHash": old_token_hash, "revokedAt": None},
        {
            "$set": {
                "refreshTokenHash": hash_token(new_refresh_token),
                "lastUsedAt": now,
            }
        },
    )
    return result.modified_count > 0


async def revoke_family(family_id: str) -> int:
    """
    §13 — Revoke ALL sessions in a token family.
    Used when token reuse is detected (possible theft).
    """
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.user_sessions.update_many(
        {"tokenFamilyId": family_id, "revokedAt": None},
        {"$set": {"revokedAt": now}},
    )
    return result.modified_count


async def revoke_session(session_id: str, user_id: str) -> bool:
    """Revoke a specific session (user-initiated device removal)."""
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.user_sessions.update_one(
        {"_id": ObjectId(session_id), "userId": user_id, "revokedAt": None},
        {"$set": {"revokedAt": now}},
    )
    return result.modified_count > 0


async def revoke_all_for_user(user_id: str) -> int:
    """Revoke all sessions for a user (account deletion / password change)."""
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.user_sessions.update_many(
        {"userId": user_id, "revokedAt": None},
        {"$set": {"revokedAt": now}},
    )
    return result.modified_count


async def get_active_sessions(user_id: str) -> List[Dict[str, Any]]:
    """List all active (non-revoked) sessions for a user."""
    db = get_database()
    cursor = db.user_sessions.find(
        {"userId": user_id, "revokedAt": None}
    ).sort("lastUsedAt", -1)
    return await cursor.to_list(length=50)
