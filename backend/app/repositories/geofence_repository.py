"""
GeoPulse — Geofence Repository

Data-access layer for the `geofences` collection.
Uses MongoDB geospatial queries to check point-in-radius.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.config.database import get_database


async def create_geofence(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new geofence zone."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "userId": user_id,
        "name": data["name"],
        "center": {
            "type": "Point",
            "coordinates": [data["longitude"], data["latitude"]],
        },
        "radiusMeters": data["radius_meters"],
        "isActive": True,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.geofences.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_user_geofences(user_id: str) -> List[Dict[str, Any]]:
    """Get all geofences for a user."""
    db = get_database()
    cursor = db.geofences.find({"userId": user_id, "isActive": True})
    return await cursor.to_list(length=100)


async def get_geofence_by_id(geofence_id: str) -> Optional[Dict[str, Any]]:
    """Get a single geofence."""
    db = get_database()
    return await db.geofences.find_one({"_id": ObjectId(geofence_id)})


async def delete_geofence(geofence_id: str, user_id: str) -> bool:
    """Delete a geofence (soft-delete by setting isActive=False)."""
    db = get_database()
    result = await db.geofences.update_one(
        {"_id": ObjectId(geofence_id), "userId": user_id},
        {"$set": {"isActive": False, "updatedAt": datetime.now(timezone.utc)}},
    )
    return result.modified_count > 0


async def find_geofences_containing_point(
    user_id: str,
    longitude: float,
    latitude: float,
) -> List[Dict[str, Any]]:
    """
    Find all active geofences for a user where the given point
    is within the geofence radius.

    Uses $geoNear-style logic: we query geofences whose center is
    within radius_meters of the point.
    """
    db = get_database()
    # Get all user's active geofences and check distance manually
    # (MongoDB $geoWithin requires the query shape, not per-doc radius)
    geofences = await get_user_geofences(user_id)
    matching = []
    for gf in geofences:
        center_coords = gf["center"]["coordinates"]
        radius = gf["radiusMeters"]
        # Use $geoWithin with $centerSphere for each geofence
        # But since radius varies per geofence, we check via aggregation
        count = await db.geofences.count_documents({
            "_id": gf["_id"],
            "isActive": True,
            "center": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "$maxDistance": radius,
                },
            },
        })
        if count > 0:
            matching.append(gf)
    return matching
