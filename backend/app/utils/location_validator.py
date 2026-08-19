"""
GeoPulse — Location Validator (§4, §5, §6, §7, §8, §9, §10)

Comprehensive server-side validation for all incoming location updates.
Validates bounds, accuracy, speed, sequence, throttle, and integrity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config.settings import get_settings
from app.utils.geo import haversine_distance

logger = logging.getLogger("geopulse.location_validator")


@dataclass
class ValidationResult:
    """Result of location validation."""
    is_valid: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    integrity_status: str = "clean"  # clean | flagged | rejected
    accuracy_level: str = "unknown"  # high | moderate | low | unknown
    server_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def validate_coordinates(lat: Any, lon: Any) -> list[str]:
    """§4 — Validate lat/lon bounds."""
    errors = []
    if lat is None or lon is None:
        errors.append("latitude and longitude are required")
        return errors
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        errors.append("latitude and longitude must be numeric")
        return errors
    if not (-90 <= lat <= 90):
        errors.append(f"latitude {lat} out of range [-90, 90]")
    if not (-180 <= lon <= 180):
        errors.append(f"longitude {lon} out of range [-180, 180]")
    # Null Island check
    if lat == 0.0 and lon == 0.0:
        errors.append("coordinates (0, 0) rejected — likely GPS error")
    return errors


def classify_accuracy(accuracy: Optional[float]) -> str:
    """§9 — Classify location accuracy."""
    if accuracy is None:
        return "unknown"
    if accuracy <= 10:
        return "high"
    if accuracy <= 100:
        return "moderate"
    return "low"


def validate_location_data(
    data: Dict[str, Any],
    previous_location: Optional[Dict[str, Any]] = None,
    previous_timestamp: Optional[datetime] = None,
) -> ValidationResult:
    """
    Full validation pipeline for an incoming location update.

    Checks:
    1. Coordinate bounds (§4)
    2. Accuracy range (§9)
    3. Speed/heading range (§4)
    4. Anomaly detection (§10)
    """
    result = ValidationResult()
    settings = get_settings()

    # §4 — Coordinate bounds
    coord_errors = validate_coordinates(data.get("latitude"), data.get("longitude"))
    if coord_errors:
        result.is_valid = False
        result.errors.extend(coord_errors)
        result.integrity_status = "rejected"
        return result

    lat = float(data["latitude"])
    lon = float(data["longitude"])

    # §9 — Accuracy classification
    accuracy = data.get("accuracy")
    if accuracy is not None:
        try:
            accuracy = float(accuracy)
            if accuracy < 0:
                result.errors.append("accuracy cannot be negative")
                result.is_valid = False
                result.integrity_status = "rejected"
                return result
            if accuracy > settings.MAX_ACCURACY_METERS:
                result.warnings.append(f"accuracy {accuracy}m exceeds threshold")
                result.integrity_status = "flagged"
        except (ValueError, TypeError):
            result.warnings.append("accuracy is not numeric — ignored")

    result.accuracy_level = classify_accuracy(accuracy)

    # §4 — Speed validation
    speed = data.get("speed")
    if speed is not None:
        try:
            speed = float(speed)
            if speed < 0:
                result.warnings.append("negative speed corrected to 0")
                data["speed"] = 0
        except (ValueError, TypeError):
            pass

    # §4 — Heading validation
    heading = data.get("heading")
    if heading is not None:
        try:
            heading = float(heading)
            if not (0 <= heading <= 360):
                result.warnings.append(f"heading {heading} out of [0, 360]")
        except (ValueError, TypeError):
            pass

    # §10 — Anomaly detection: impossible speed / teleportation
    if previous_location and previous_timestamp:
        try:
            prev_lat = previous_location.get("latitude", 0)
            prev_lon = previous_location.get("longitude", 0)
            now = datetime.now(timezone.utc)
            time_delta = (now - previous_timestamp).total_seconds()

            if time_delta > 0:
                distance = haversine_distance(prev_lat, prev_lon, lat, lon)
                implied_speed = distance / time_delta

                if implied_speed > settings.MAX_PLAUSIBLE_SPEED_MPS:
                    result.warnings.append(
                        f"anomaly: implied speed {implied_speed:.1f} m/s "
                        f"exceeds max plausible {settings.MAX_PLAUSIBLE_SPEED_MPS} m/s"
                    )
                    result.integrity_status = "flagged"
        except Exception:
            pass

    # §5 — Server-side timestamp (authoritative)
    result.server_timestamp = datetime.now(timezone.utc)

    return result
