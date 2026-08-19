"""
GeoPulse — Audit Repository (§12)

Records security-sensitive operations with structured data.
Never stores raw location data inside audit logs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config.database import get_database


# Valid audit actions
AUDIT_ACTIONS = {
    "LOGIN", "OTP_VERIFIED", "LOGOUT",
    "SHARING_REQUESTED", "SHARING_ACCEPTED", "SHARING_REJECTED",
    "LOCATION_ACCESS", "LOCATION_REVOKED", "LOCATION_STOPPED",
    "SOS_TRIGGERED", "SOS_ACKNOWLEDGED", "SOS_RESOLVED",
    "ACCOUNT_DELETED", "DEVICE_ADDED", "DEVICE_REMOVED",
    "BLOCK_CREATED", "BLOCK_REMOVED",
    "CONSENT_GRANTED", "CONSENT_REVOKED",
    "TOKEN_REFRESHED", "TOKEN_FAMILY_REVOKED",
}


async def create_audit_log(
    actor_id: str,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: Dict[str, Any] | None = None,
    request_id: str | None = None,
) -> Dict[str, Any]:
    """Record a security-sensitive operation."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "actorId": actor_id,
        "action": action,
        "resourceType": resource_type,
        "resourceId": resource_id,
        "metadata": metadata or {},
        "requestId": request_id,
        "timestamp": now,
    }
    result = await db.audit_logs.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_audit_logs(
    actor_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Query audit logs with optional filters."""
    db = get_database()
    query: Dict[str, Any] = {}
    if actor_id:
        query["actorId"] = actor_id
    if action:
        query["action"] = action
    if resource_type:
        query["resourceType"] = resource_type
    if resource_id:
        query["resourceId"] = resource_id

    cursor = db.audit_logs.find(query).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)
