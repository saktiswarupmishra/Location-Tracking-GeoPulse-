"""
GeoPulse — Sharing Service (v1.1 Hardened)

Business logic for location-sharing requests, acceptance,
rejection, revocation, and stop.
Integrates block checks (§28), consent recording (§11),
session management (§2), audit logging (§12), and notifications.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.config.redis import get_redis
from app.repositories import (
    audit_repository,
    block_repository,
    consent_repository,
    session_location_repository,
    sharing_repository,
    user_repository,
)
from app.services import notification_service
from app.utils.phone import normalize_phone

logger = logging.getLogger("geopulse.sharing")


async def send_request(
    requester_id: str,
    target_phone: str,
    permissions: Dict[str, bool] | None = None,
    expires_at: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Send a location-sharing request.

    The requester asks to VIEW the target's location:
    owner=target, viewer=requester.
    """
    target_phone = normalize_phone(target_phone)

    # Find target user
    target_user = await user_repository.find_by_phone(target_phone)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with this phone number",
        )

    target_id = str(target_user["_id"])

    # Can't request from yourself
    if target_id == requester_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send a sharing request to yourself",
        )

    # §28 Check if blocked (either direction)
    if await block_repository.is_blocked(target_id, requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to send request to this user",
        )

    # Check for existing request
    existing = await sharing_repository.find_existing_request(target_id, requester_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A sharing request already exists with this user",
        )

    # Create the request
    effective_permissions = permissions or {"liveLocation": True, "locationHistory": False}
    share = await sharing_repository.create_request(
        owner_id=target_id,
        viewer_id=requester_id,
        permissions=effective_permissions,
        expires_at=expires_at,
    )
    share_id = str(share["_id"])

    # §12 Audit log
    await audit_repository.create_audit_log(
        actor_id=requester_id,
        action="SHARING_REQUEST_SENT",
        resource_type="share",
        resource_id=share_id,
        metadata={"target_id": target_id, "permissions": effective_permissions},
    )

    # Notify the target user
    requester = await user_repository.find_by_id(requester_id)
    requester_name = requester["name"] if requester else "Someone"

    await notification_service.send_notification(
        user_id=target_id,
        notification_type="LOCATION_REQUEST",
        title="Location Sharing Request",
        message=f"{requester_name} wants to view your live location.",
        data={"shareId": share_id, "requesterId": requester_id},
    )

    logger.info("Sharing request sent: %s → %s", requester_id, target_id)
    return share


async def accept_request(share_id: str, user_id: str) -> Dict[str, Any]:
    """
    Accept a sharing request. Only the owner (person being asked
    to share) can accept.
    """
    share = await sharing_repository.find_by_id(share_id)
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if share["ownerId"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if share["status"] != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    await sharing_repository.update_status(share_id, "accepted")

    # §11 Record immutable consent
    await consent_repository.create_consent(
        owner_id=user_id,
        viewer_id=share["viewerId"],
        action="granted",
        sharing_id=share_id,
        permissions=share.get("permissions"),
    )

    # §2 Start a location session
    await session_location_repository.start_session(
        owner_id=user_id,
        sharing_id=share_id,
    )

    # §12 Audit log
    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="SHARING_ACCEPTED",
        resource_type="share",
        resource_id=share_id,
        metadata={"viewer_id": share["viewerId"]},
    )

    # Notify the viewer (requester)
    owner = await user_repository.find_by_id(user_id)
    owner_name = owner["name"] if owner else "Someone"

    await notification_service.send_notification(
        user_id=share["viewerId"],
        notification_type="REQUEST_ACCEPTED",
        title="Request Accepted",
        message=f"{owner_name} accepted your location sharing request.",
        data={"shareId": share_id},
    )

    # Publish WebSocket event
    try:
        redis = get_redis()
        await redis.publish(
            f"sharing:{share['viewerId']}",
            json.dumps({
                "event": "SHARING_ACCEPTED",
                "shareId": share_id,
                "ownerId": user_id,
            }),
        )
    except Exception:
        pass

    logger.info("Sharing request accepted: %s", share_id)
    return await sharing_repository.find_by_id(share_id)


async def reject_request(share_id: str, user_id: str) -> None:
    """Reject a sharing request. Only the owner can reject."""
    share = await sharing_repository.find_by_id(share_id)
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if share["ownerId"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if share["status"] != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    await sharing_repository.update_status(share_id, "rejected")

    # §11 Record consent rejection
    await consent_repository.create_consent(
        owner_id=user_id,
        viewer_id=share["viewerId"],
        action="rejected",
        sharing_id=share_id,
    )

    # §12 Audit log
    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="SHARING_REJECTED",
        resource_type="share",
        resource_id=share_id,
    )

    # Notify the viewer
    await notification_service.send_notification(
        user_id=share["viewerId"],
        notification_type="REQUEST_REJECTED",
        title="Request Rejected",
        message="Your location sharing request was declined.",
        data={"shareId": share_id},
    )

    logger.info("Sharing request rejected: %s", share_id)


async def revoke_access(share_id: str, user_id: str) -> None:
    """
    Revoke an accepted sharing relationship.
    Either the owner or the viewer can revoke.
    """
    share = await sharing_repository.find_by_id(share_id)
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")

    if share["ownerId"] != user_id and share["viewerId"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if share["status"] != "accepted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Share is not active")

    await sharing_repository.update_status(share_id, "revoked")

    # §11 Record consent revocation
    await consent_repository.create_consent(
        owner_id=share["ownerId"],
        viewer_id=share["viewerId"],
        action="revoked",
        sharing_id=share_id,
    )

    # §2 Stop location tracking sessions for this share
    await session_location_repository.stop_all_for_sharing(share_id)

    # §12 Audit log
    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="SHARING_REVOKED",
        resource_type="share",
        resource_id=share_id,
    )

    # Notify the other party
    other_id = share["viewerId"] if share["ownerId"] == user_id else share["ownerId"]
    revoker = await user_repository.find_by_id(user_id)
    revoker_name = revoker["name"] if revoker else "Someone"

    await notification_service.send_notification(
        user_id=other_id,
        notification_type="LOCATION_STOPPED",
        title="Location Sharing Revoked",
        message=f"{revoker_name} revoked location sharing access.",
        data={"shareId": share_id},
    )

    # Publish revocation event for WebSocket (via Redis)
    try:
        redis = get_redis()
        await redis.publish(
            f"sharing:{other_id}",
            json.dumps({"event": "SHARING_REVOKED", "shareId": share_id}),
        )
    except Exception:
        pass

    logger.info("Sharing revoked: %s by %s", share_id, user_id)


async def stop_sharing(share_id: str, user_id: str) -> None:
    """
    Owner stops sharing their location.
    """
    await revoke_access(share_id, user_id)


async def get_pending_requests(user_id: str) -> List[Dict[str, Any]]:
    """Get all pending incoming requests for a user."""
    shares = await sharing_repository.find_pending_for_user(user_id)
    enriched = []
    for share in shares:
        viewer = await user_repository.find_by_id(share["viewerId"])
        s = _serialize_share(share)
        s["viewer_name"] = viewer["name"] if viewer else None
        enriched.append(s)
    return enriched


async def get_active_shares(user_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Get all shares (incoming & outgoing) for a user."""
    data = await sharing_repository.find_all_for_user(user_id)
    incoming = []
    for share in data["incoming"]:
        owner = await user_repository.find_by_id(share["ownerId"])
        s = _serialize_share(share)
        s["owner_name"] = owner["name"] if owner else None
        incoming.append(s)

    outgoing = []
    for share in data["outgoing"]:
        viewer = await user_repository.find_by_id(share["viewerId"])
        s = _serialize_share(share)
        s["viewer_name"] = viewer["name"] if viewer else None
        outgoing.append(s)

    return {"incoming": incoming, "outgoing": outgoing}


def _serialize_share(share: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a MongoDB share doc to a JSON-safe dict."""
    return {
        "id": str(share["_id"]),
        "owner_id": share["ownerId"],
        "viewer_id": share["viewerId"],
        "status": share["status"],
        "permissions": {
            "live_location": share.get("permissions", {}).get("liveLocation", True),
            "location_history": share.get("permissions", {}).get("locationHistory", False),
        },
        "started_at": share.get("startedAt"),
        "expires_at": share.get("expiresAt"),
        "stopped_at": share.get("stoppedAt"),
        "created_at": share.get("createdAt"),
    }
