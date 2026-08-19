"""
GeoPulse — Geospatial Utilities

Pure-Python geographic calculations.
"""

from __future__ import annotations

import math
from typing import Dict

# Earth's mean radius in meters
EARTH_RADIUS_M = 6_371_000


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Args:
        lat1, lon1: First point (decimal degrees).
        lat2, lon2: Second point (decimal degrees).

    Returns:
        Distance in meters.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_M * c


def is_within_radius(
    lat: float, lon: float,
    center_lat: float, center_lon: float,
    radius_meters: float,
) -> bool:
    """Check if a point is within a given radius of a center point."""
    return haversine_distance(lat, lon, center_lat, center_lon) <= radius_meters


def to_geojson_point(latitude: float, longitude: float) -> Dict:
    """
    Convert lat/lng to a MongoDB GeoJSON Point.

    IMPORTANT: GeoJSON uses [longitude, latitude] order.
    """
    return {
        "type": "Point",
        "coordinates": [longitude, latitude],
    }
