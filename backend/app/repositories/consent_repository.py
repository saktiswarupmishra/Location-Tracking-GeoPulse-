"""
GeoPulse — Consent Repository (§11)

Immutable consent records for location sharing grants/revocations.
Provides audit trail for all location-sharing authorization changes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.config.database import get_database


async def create_consent(
    owner_id: str,
    viewer_id: str,
    action: str,
    sharing_id: str,
    permissions: Dict[str, bool] | None = None,
    consent_version: str = "1.0",
) -> Dict[str, Any]:
    """
    Create an immutable consent record.
    action: "granted" | "revoked" | "expired" | "rejected"
    """
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "ownerId": owner_id,
        "viewerId": viewer_id,
        "action": action,
        "sharingId": sharing_id,
        "permissions": permissions or {},
        "consentVersion": consent_version,
        "timestamp": now,
    }
    result = await db.location_consents.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_consent_history(
    owner_id: str,
    viewer_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get consent history between two users."""
    db = get_database()
    cursor = db.location_consents.find({
        "ownerId": owner_id,
        "viewerId": viewer_id,
    }).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_all_consents_for_user(
    user_id: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get all consent records where user is owner or viewer."""
    db = get_database()
    cursor = db.location_consents.find({
        "$or": [{"ownerId": user_id}, {"viewerId": user_id}]
    }).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)
