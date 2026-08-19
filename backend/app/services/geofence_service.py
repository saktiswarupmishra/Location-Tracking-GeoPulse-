"""
GeoPulse — Geofence Service (v1.1 Hardened)

§19 — Persistent state (MongoDB, not in-memory).
§20 — Event deduplication (only emit on state transitions).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.config.redis import get_redis
from app.repositories import geofence_repository, geofence_state_repository
from app.services import notification_service
from app.utils.geo import haversine_distance

logger = logging.getLogger("geopulse.geofence")


async def create_geofence(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new geofence zone."""
    gf = await geofence_repository.create_geofence(user_id, data)
    return _format_geofence(gf)


async def get_geofences(user_id: str) -> List[Dict[str, Any]]:
    """List all active geofences for a user."""
    geofences = await geofence_repository.get_user_geofences(user_id)
    return [_format_geofence(gf) for gf in geofences]


async def delete_geofence(user_id: str, geofence_id: str) -> bool:
    """Delete a geofence and its state records."""
    deleted = await geofence_repository.delete_geofence(geofence_id, user_id)
    if deleted:
        await geofence_state_repository.delete_for_geofence(geofence_id)
    return deleted


async def check_geofences(
    user_id: str,
    longitude: float,
    latitude: float,
) -> None:
    """
    §19/§20 — Check geofences with persistent state and deduplication.
    Only emits events on actual state transitions (entered → exited or vice versa).
    """
    geofences = await geofence_repository.get_user_geofences(user_id)
    if not geofences:
        return

    for gf in geofences:
        gf_id = str(gf["_id"])
        center_coords = gf["center"]["coordinates"]  # [lon, lat]
        radius = gf["radiusMeters"]

        distance = haversine_distance(
            latitude, longitude,
            center_coords[1], center_coords[0],
        )

        currently_inside = distance <= radius

        # §19 — Get persistent state
        state = await geofence_state_repository.get_state(user_id, gf_id)
        was_inside = state.get("isInside", False) if state else False

        # §20 — Only emit on state transitions
        if currently_inside and not was_inside:
            await _emit_geofence_event(user_id, gf, "entered")
            await geofence_state_repository.update_state(user_id, gf_id, True)
        elif not currently_inside and was_inside:
            await _emit_geofence_event(user_id, gf, "exited")
            await geofence_state_repository.update_state(user_id, gf_id, False)
        elif state is None:
            # First time — initialize state without emitting
            await geofence_state_repository.update_state(user_id, gf_id, currently_inside)


async def _emit_geofence_event(
    user_id: str,
    geofence: Dict[str, Any],
    event_type: str,
) -> None:
    """Send geofence notification and publish Redis event."""
    gf_name = geofence.get("name", "Zone")
    gf_id = str(geofence["_id"])
    now = datetime.now(timezone.utc)

    action = "entered" if event_type == "entered" else "left"
    notif_type = "GEOFENCE_ENTER" if event_type == "entered" else "GEOFENCE_EXIT"

    logger.info("Geofence %s: user %s %s %s", event_type, user_id, action, gf_name)

    await notification_service.send_notification(
        user_id=user_id,
        notification_type=notif_type,
        title="Geofence Alert",
        message=f"You {action} {gf_name}.",
        data={"geofenceId": gf_id, "geofenceName": gf_name, "eventType": event_type},
    )

    try:
        redis = get_redis()
        ws_event = f"GEOFENCE_{'ENTERED' if event_type == 'entered' else 'EXITED'}"
        await redis.publish(
            f"geofence:{user_id}",
            json.dumps({
                "event": ws_event,
                "geofenceId": gf_id,
                "geofenceName": gf_name,
                "userId": user_id,
                "timestamp": now.isoformat(),
            }),
        )
    except Exception as e:
        logger.warning("Failed to publish geofence event: %s", e)


def _format_geofence(gf: Dict[str, Any]) -> Dict[str, Any]:
    """Format a geofence document for API response."""
    coords = gf.get("center", {}).get("coordinates", [0, 0])
    return {
        "id": str(gf["_id"]),
        "user_id": gf["userId"],
        "name": gf["name"],
        "latitude": coords[1] if len(coords) > 1 else 0,
        "longitude": coords[0] if len(coords) > 0 else 0,
        "radius_meters": gf["radiusMeters"],
        "is_active": gf.get("isActive", True),
        "created_at": gf.get("createdAt"),
    }
