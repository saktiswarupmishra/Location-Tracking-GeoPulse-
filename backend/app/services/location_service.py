"""
GeoPulse — Location Service (v1.1 Hardened)

Validates, throttles, sequences, and stores location updates.
Computes freshness status for responses.
Publishes to Redis for real-time WebSocket delivery.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.config.redis import get_redis
from app.config.settings import get_settings
from app.repositories import location_repository, sharing_repository
from app.repositories import session_location_repository
from app.services import geofence_service
from app.utils.location_validator import validate_location_data, ValidationResult

logger = logging.getLogger("geopulse.location")


# ──────────────────────────────────────────
# Location Update Pipeline (§4-§10, §35)
# ──────────────────────────────────────────

async def update_location(user_id: str, data: Dict[str, Any]) -> None:
    """
    Process an incoming location update:
    1. Validate (§4, §9, §10)
    2. Server timestamp injection (§5)
    3. Sequence check (§6)
    4. Throttle check (§7)
    5. Upsert live_locations (critical path)
    6. Publish to Redis (critical path)
    7. Save to location_history (async, best-effort)
    8. Check geofences (async, best-effort)
    """
    settings = get_settings()
    redis = get_redis()

    # ── 1. Validate ──
    prev_loc = await _get_previous_location(user_id, redis)
    prev_ts = prev_loc.get("timestamp") if prev_loc else None

    validation = validate_location_data(data, prev_loc, prev_ts)
    if not validation.is_valid:
        logger.warning("Location rejected for %s: %s", user_id, validation.errors)
        return  # silently drop invalid updates

    # ── 2. Server timestamp (§5) ──
    data["server_timestamp"] = validation.server_timestamp
    data["integrity_status"] = validation.integrity_status
    data["accuracy_level"] = validation.accuracy_level

    # ── 3. Sequence check (§6) ──
    client_seq = data.get("sequence", 0)
    seq_key = f"loc_seq:{user_id}"
    last_seq = await redis.get(seq_key)
    if last_seq and int(last_seq) >= client_seq and client_seq > 0:
        logger.debug("Dropping out-of-order packet seq=%d for %s", client_seq, user_id)
        return
    if client_seq > 0:
        await redis.set(seq_key, str(client_seq), ex=3600)
    data["sequence"] = client_seq

    # ── 4. Throttle (§7) ──
    throttle_key = f"loc_throttle:{user_id}"
    last_update = await redis.get(throttle_key)
    if last_update:
        # Too fast — drop
        return
    await redis.set(
        throttle_key, "1",
        ex=settings.LOCATION_UPDATE_MIN_INTERVAL_SECONDS,
    )

    # ── 5. Upsert live location (critical path) ──
    if not data.get("timestamp"):
        data["timestamp"] = validation.server_timestamp

    session = await session_location_repository.find_active_session(user_id)
    if session:
        data["session_id"] = session.get("sessionId")
        await session_location_repository.update_session_location(
            user_id, client_seq,
        )

    await location_repository.upsert_live_location(user_id, data)

    # Cache for next validation
    await _cache_location(user_id, data, redis)

    # ── 6. Publish to Redis (critical path) ──
    try:
        viewer_ids = await sharing_repository.get_authorized_viewer_ids(user_id)
        if viewer_ids:
            event_payload = json.dumps({
                "event": "LOCATION_UPDATE",
                "userId": user_id,
                "location": {
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                },
                "accuracy": data.get("accuracy"),
                "accuracyLevel": validation.accuracy_level,
                "speed": data.get("speed"),
                "heading": data.get("heading"),
                "sequence": client_seq,
                "integrityStatus": validation.integrity_status,
                "timestamp": validation.server_timestamp.isoformat(),
            })
            await redis.publish(f"location:{user_id}", event_payload)
    except Exception as e:
        logger.warning("Failed to publish location to Redis: %s", e)

    # ── 7. Save to history (best-effort) ──
    try:
        await location_repository.save_history_point(user_id, data)
    except Exception as e:
        logger.warning("Failed to save location history: %s", e)

    # ── 8. Check geofences (best-effort) ──
    try:
        await geofence_service.check_geofences(
            user_id,
            data["longitude"],
            data["latitude"],
        )
    except Exception as e:
        logger.warning("Geofence check failed: %s", e)


# ──────────────────────────────────────────
# Location Retrieval (§8 — freshness status)
# ──────────────────────────────────────────

async def get_live_location(
    requester_id: str,
    target_user_id: str,
) -> Dict[str, Any]:
    """
    Get another user's live location.
    AUTHORIZATION CHECK: active sharing with liveLocation permission.
    Returns freshness status (§8).
    """
    if requester_id == target_user_id:
        return await get_my_location(requester_id)

    authorized = await sharing_repository.is_authorized(
        owner_id=target_user_id,
        viewer_id=requester_id,
    )
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user's location",
        )

    loc = await location_repository.get_live_location(target_user_id)
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not available for this user",
        )

    return _format_location(target_user_id, loc)


async def get_my_location(user_id: str) -> Dict[str, Any]:
    """Get the authenticated user's own current location."""
    loc = await location_repository.get_live_location(user_id)
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No location data available. Start sharing to record your location.",
        )
    return _format_location(user_id, loc)


async def get_history(
    requester_id: str,
    target_user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    """Get location history. Authorization required for other users."""
    if requester_id != target_user_id:
        has_perm = await sharing_repository.has_history_permission(
            owner_id=target_user_id,
            viewer_id=requester_id,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this user's location history",
            )

    points = await location_repository.get_history(
        target_user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    formatted_points = []
    for p in points:
        coords = p.get("location", {}).get("coordinates", [0, 0])
        formatted_points.append({
            "latitude": coords[1] if len(coords) > 1 else 0,
            "longitude": coords[0] if len(coords) > 0 else 0,
            "accuracy": p.get("accuracy"),
            "accuracy_level": p.get("accuracyLevel", "unknown"),
            "speed": p.get("speed"),
            "heading": p.get("heading"),
            "timestamp": p.get("serverTimestamp"),
            "integrity_status": p.get("integrityStatus", "clean"),
        })

    return {
        "user_id": target_user_id,
        "points": formatted_points,
        "total_points": len(formatted_points),
        "start_date": start_date,
        "end_date": end_date,
    }


async def delete_history(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> int:
    """Delete the authenticated user's own location history."""
    if start_date or end_date:
        return await location_repository.delete_history(user_id, start_date, end_date)
    return await location_repository.delete_all_history(user_id)


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────

def _compute_freshness(loc: Dict[str, Any]) -> str:
    """§8 — Compute freshness status from server timestamp."""
    settings = get_settings()
    server_ts = loc.get("serverTimestamp") or loc.get("updatedAt")
    if not server_ts:
        return "unavailable"

    if isinstance(server_ts, str):
        try:
            server_ts = datetime.fromisoformat(server_ts)
        except ValueError:
            return "unavailable"

    age = (datetime.now(timezone.utc) - server_ts).total_seconds()
    if age <= settings.LOCATION_DELAYED_THRESHOLD_SECONDS:
        return "live"
    if age <= settings.LOCATION_STALE_THRESHOLD_SECONDS:
        return "delayed"
    return "stale"


def _format_location(user_id: str, loc: Dict[str, Any]) -> Dict[str, Any]:
    """Format a live_locations document for API response."""
    coords = loc.get("location", {}).get("coordinates", [0, 0])
    return {
        "user_id": user_id,
        "latitude": coords[1] if len(coords) > 1 else 0,
        "longitude": coords[0] if len(coords) > 0 else 0,
        "accuracy": loc.get("accuracy"),
        "accuracy_level": loc.get("accuracyLevel", "unknown"),
        "speed": loc.get("speed"),
        "heading": loc.get("heading"),
        "altitude": loc.get("altitude"),
        "timestamp": loc.get("serverTimestamp") or loc.get("clientTimestamp"),
        "sequence": loc.get("sequence", 0),
        "integrity_status": loc.get("integrityStatus", "clean"),
        "freshness_status": _compute_freshness(loc),
        "session_id": loc.get("sessionId"),
        "is_live": _compute_freshness(loc) in ("live", "delayed"),
        "updated_at": loc.get("updatedAt"),
    }


async def _get_previous_location(user_id: str, redis) -> Optional[Dict[str, Any]]:
    """Retrieve cached previous location for validation."""
    try:
        cached = await redis.get(f"prev_loc:{user_id}")
        if cached:
            import json as _json
            return _json.loads(cached)
    except Exception:
        pass
    return None


async def _cache_location(user_id: str, data: Dict[str, Any], redis) -> None:
    """Cache current location for next validation cycle."""
    try:
        import json as _json
        cache_data = {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "timestamp": data.get("server_timestamp", datetime.now(timezone.utc)).isoformat(),
        }
        await redis.set(f"prev_loc:{user_id}", _json.dumps(cache_data), ex=300)
    except Exception:
        pass
