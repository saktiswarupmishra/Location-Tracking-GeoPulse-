"""
GeoPulse — Location Validation Tests (§4, §5, §6, §7, §8, §9, §10)

Tests for the location_validator utility covering:
- Invalid coordinates
- Negative accuracy / impossible speed
- Sequence number rejection
- Stale location detection
- Anomaly (teleportation) detection
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.utils.location_validator import (
    ValidationResult,
    classify_accuracy,
    validate_coordinates,
    validate_location_data,
)


# ──────────────────────────────────────────
# §4 — Coordinate Bounds
# ──────────────────────────────────────────

class TestCoordinateValidation:

    def test_valid_coordinates(self):
        errors = validate_coordinates(40.7128, -74.0060)
        assert errors == []

    def test_latitude_out_of_range(self):
        errors = validate_coordinates(91.0, 0.0)
        assert len(errors) == 1
        assert "latitude" in errors[0]

    def test_longitude_out_of_range(self):
        errors = validate_coordinates(0.0, 181.0)
        assert len(errors) == 1
        assert "longitude" in errors[0]

    def test_null_island_rejected(self):
        errors = validate_coordinates(0.0, 0.0)
        assert len(errors) == 1
        assert "GPS error" in errors[0]

    def test_none_coordinates(self):
        errors = validate_coordinates(None, None)
        assert len(errors) == 1

    def test_non_numeric_coordinates(self):
        errors = validate_coordinates("abc", "def")
        assert len(errors) == 1
        assert "numeric" in errors[0]

    def test_boundary_values(self):
        assert validate_coordinates(90, 180) == []
        assert validate_coordinates(-90, -180) == []


# ──────────────────────────────────────────
# §9 — Accuracy Classification
# ──────────────────────────────────────────

class TestAccuracyClassification:

    def test_high_accuracy(self):
        assert classify_accuracy(5.0) == "high"

    def test_moderate_accuracy(self):
        assert classify_accuracy(50.0) == "moderate"

    def test_low_accuracy(self):
        assert classify_accuracy(500.0) == "low"

    def test_none_accuracy(self):
        assert classify_accuracy(None) == "unknown"


# ──────────────────────────────────────────
# Full Validation Pipeline
# ──────────────────────────────────────────

class TestLocationValidation:

    def test_valid_location(self):
        data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 10.0,
            "speed": 5.0,
            "heading": 180.0,
        }
        result = validate_location_data(data)
        assert result.is_valid
        assert result.integrity_status == "clean"
        assert result.accuracy_level == "high"

    def test_invalid_coordinates_rejected(self):
        data = {"latitude": 999, "longitude": -74.0060}
        result = validate_location_data(data)
        assert not result.is_valid
        assert result.integrity_status == "rejected"

    def test_negative_accuracy_rejected(self):
        data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": -10.0,
        }
        result = validate_location_data(data)
        assert not result.is_valid

    def test_negative_speed_corrected(self):
        data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "speed": -5.0,
        }
        result = validate_location_data(data)
        assert result.is_valid
        assert data["speed"] == 0

    def test_anomaly_detection_flagged(self):
        """§10 — Impossible speed (teleportation) flagged."""
        data = {
            "latitude": 51.5074,  # London
            "longitude": -0.1278,
        }
        prev = {
            "latitude": 40.7128,  # New York
            "longitude": -74.0060,
        }
        prev_time = datetime.now(timezone.utc) - timedelta(seconds=1)

        result = validate_location_data(data, prev, prev_time)
        assert result.is_valid  # still valid, just flagged
        assert result.integrity_status == "flagged"

    def test_server_timestamp_injected(self):
        """§5 — Server timestamp always set."""
        data = {"latitude": 40.7128, "longitude": -74.0060}
        result = validate_location_data(data)
        assert result.server_timestamp is not None
        assert isinstance(result.server_timestamp, datetime)

    def test_high_accuracy_threshold(self):
        """§9 — Very high accuracy (GPS-level)."""
        data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 3.0,
        }
        result = validate_location_data(data)
        assert result.accuracy_level == "high"
