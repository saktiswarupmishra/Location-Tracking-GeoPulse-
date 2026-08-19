"""
GeoPulse — Sharing Repository (v1.1 Hardened)

PyMongo Async. Manages sharing relationships and authorization.
Added revoke_all_for_user_pair for block support.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.config.database import get_database


async def create_request(
    owner_id: str,
    viewer_id: str,
    permissions: Dict[str, bool] | None = None,
    expires_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a new sharing request (status=pending)."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "ownerId": owner_id,
        "viewerId": viewer_id,
        "status": "pending",
        "permissions": permissions or {"liveLocation": True, "locationHistory": False},
        "startedAt": None,
        "expiresAt": expires_at,
        "stoppedAt": None,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.location_shares.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def find_by_id(share_id: str) -> Optional[Dict[str, Any]]:
    """Find a sharing record by _id."""
    db = get_database()
    return await db.location_shares.find_one({"_id": ObjectId(share_id)})


async def find_pending_for_user(user_id: str) -> List[Dict[str, Any]]:
    """Find all pending incoming requests for a user (they are the viewer)."""
    db = get_database()
    cursor = db.location_shares.find({
        "viewerId": user_id,
        "status": "pending",
    }).sort("createdAt", -1)
    return await cursor.to_list(length=100)


async def find_active_shares_as_owner(user_id: str) -> List[Dict[str, Any]]:
    """Find all accepted shares where user is the owner (sharer)."""
    db = get_database()
    cursor = db.location_shares.find({
        "ownerId": user_id,
        "status": "accepted",
    }).sort("startedAt", -1)
    return await cursor.to_list(length=100)


async def find_active_shares_as_viewer(user_id: str) -> List[Dict[str, Any]]:
    """Find all accepted shares where user is the viewer."""
    db = get_database()
    cursor = db.location_shares.find({
        "viewerId": user_id,
        "status": "accepted",
    }).sort("startedAt", -1)
    return await cursor.to_list(length=100)


async def find_all_for_user(user_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Return all incoming & outgoing shares (any status) for a user."""
    db = get_database()
    incoming_cursor = db.location_shares.find({"viewerId": user_id}).sort("createdAt", -1)
    outgoing_cursor = db.location_shares.find({"ownerId": user_id}).sort("createdAt", -1)
    return {
        "incoming": await incoming_cursor.to_list(length=200),
        "outgoing": await outgoing_cursor.to_list(length=200),
    }


async def find_existing_request(owner_id: str, viewer_id: str) -> Optional[Dict[str, Any]]:
    """Check if a pending/accepted relationship already exists (either direction)."""
    db = get_database()
    return await db.location_shares.find_one({
        "$or": [
            {"ownerId": owner_id, "viewerId": viewer_id, "status": {"$in": ["pending", "accepted"]}},
            {"ownerId": viewer_id, "viewerId": owner_id, "status": {"$in": ["pending", "accepted"]}},
        ]
    })


async def update_status(share_id: str, new_status: str, **extra: Any) -> None:
    """Update the status of a sharing record."""
    db = get_database()
    update_fields: Dict[str, Any] = {
        "status": new_status,
        "updatedAt": datetime.now(timezone.utc),
    }
    if new_status == "accepted":
        update_fields["startedAt"] = datetime.now(timezone.utc)
    if new_status in ("revoked", "expired"):
        update_fields["stoppedAt"] = datetime.now(timezone.utc)
    update_fields.update(extra)
    await db.location_shares.update_one(
        {"_id": ObjectId(share_id)},
        {"$set": update_fields},
    )


async def is_authorized(owner_id: str, viewer_id: str) -> bool:
    """
    Check if viewer_id is authorized to view owner_id's live location.
    An active, accepted share with liveLocation permission must exist.
    """
    db = get_database()
    now = datetime.now(timezone.utc)
    share = await db.location_shares.find_one({
        "ownerId": owner_id,
        "viewerId": viewer_id,
        "status": "accepted",
        "permissions.liveLocation": True,
        "$or": [
            {"expiresAt": None},
            {"expiresAt": {"$gt": now}},
        ],
    })
    return share is not None


async def has_history_permission(owner_id: str, viewer_id: str) -> bool:
    """Check if viewer has history permission for owner's location."""
    db = get_database()
    now = datetime.now(timezone.utc)
    share = await db.location_shares.find_one({
        "ownerId": owner_id,
        "viewerId": viewer_id,
        "status": "accepted",
        "permissions.locationHistory": True,
        "$or": [
            {"expiresAt": None},
            {"expiresAt": {"$gt": now}},
        ],
    })
    return share is not None


async def get_authorized_viewer_ids(owner_id: str) -> List[str]:
    """Return all user IDs authorized to view owner_id's location."""
    db = get_database()
    now = datetime.now(timezone.utc)
    cursor = db.location_shares.find(
        {
            "ownerId": owner_id,
            "status": "accepted",
            "permissions.liveLocation": True,
            "$or": [
                {"expiresAt": None},
                {"expiresAt": {"$gt": now}},
            ],
        },
        {"viewerId": 1},
    )
    docs = await cursor.to_list(length=500)
    return [doc["viewerId"] for doc in docs]


async def revoke_all_for_user(user_id: str) -> None:
    """Revoke all active shares involving a user (for account deletion)."""
    db = get_database()
    now = datetime.now(timezone.utc)
    await db.location_shares.update_many(
        {
            "$or": [{"ownerId": user_id}, {"viewerId": user_id}],
            "status": {"$in": ["pending", "accepted"]},
        },
        {"$set": {"status": "revoked", "stoppedAt": now, "updatedAt": now}},
    )


async def revoke_all_for_user_pair(user_a: str, user_b: str) -> None:
    """§28 — Revoke all shares between two users (for blocking)."""
    db = get_database()
    now = datetime.now(timezone.utc)
    await db.location_shares.update_many(
        {
            "$or": [
                {"ownerId": user_a, "viewerId": user_b},
                {"ownerId": user_b, "viewerId": user_a},
            ],
            "status": {"$in": ["pending", "accepted"]},
        },
        {"$set": {"status": "revoked", "stoppedAt": now, "updatedAt": now}},
    )
