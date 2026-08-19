"""
GeoPulse — Block Repository (§28)

Dedicated blocks collection — replaces embedded blockedUsers[] array.
Blocking auto-revokes existing sharing relationships.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.config.database import get_database


async def create_block(blocker_id: str, blocked_id: str) -> Dict[str, Any]:
    """Block a user."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "blockerId": blocker_id,
        "blockedId": blocked_id,
        "createdAt": now,
    }
    await db.blocks.update_one(
        {"blockerId": blocker_id, "blockedId": blocked_id},
        {"$setOnInsert": doc},
        upsert=True,
    )
    return doc


async def remove_block(blocker_id: str, blocked_id: str) -> bool:
    """Unblock a user."""
    db = get_database()
    result = await db.blocks.delete_one({
        "blockerId": blocker_id,
        "blockedId": blocked_id,
    })
    return result.deleted_count > 0


async def is_blocked(user_id: str, other_id: str) -> bool:
    """Check if either user has blocked the other."""
    db = get_database()
    block = await db.blocks.find_one({
        "$or": [
            {"blockerId": user_id, "blockedId": other_id},
            {"blockerId": other_id, "blockedId": user_id},
        ]
    })
    return block is not None


async def get_blocked_users(user_id: str) -> List[str]:
    """Get list of user IDs blocked by this user."""
    db = get_database()
    cursor = db.blocks.find({"blockerId": user_id}, {"blockedId": 1})
    docs = await cursor.to_list(length=500)
    return [d["blockedId"] for d in docs]


async def delete_all_for_user(user_id: str) -> int:
    """Delete all block records for a user (account deletion)."""
    db = get_database()
    result = await db.blocks.delete_many({
        "$or": [{"blockerId": user_id}, {"blockedId": user_id}]
    })
    return result.deleted_count
