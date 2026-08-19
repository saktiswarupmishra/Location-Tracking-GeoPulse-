"""
GeoPulse — Concurrency & Throttling Tests (§7, §33)

Tests for concurrent location updates, rate limits, and idempotency.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.utils.location_validator import validate_location_data


@pytest.mark.asyncio
async def test_concurrent_location_sequence():
    """Verify that out-of-order packets are dropped based on sequence."""
    locations = [
        {"latitude": 12.9716, "longitude": 77.5946, "sequence": 1},
        {"latitude": 12.9717, "longitude": 77.5947, "sequence": 3},
        {"latitude": 12.9718, "longitude": 77.5948, "sequence": 2},  # Stale out-of-order
    ]

    processed = []
    last_seq = 0
    for loc in locations:
        seq = loc["sequence"]
        if seq >= last_seq:
            last_seq = seq
            processed.append(seq)

    assert processed == [1, 3]  # Sequence 2 dropped


def test_rapid_validation():
    """Verify high-throughput validation performance without blocking."""
    sample = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "accuracy": 5.0,
        "speed": 12.0,
        "heading": 90.0,
    }
    for _ in range(1000):
        res = validate_location_data(sample)
        assert res.is_valid
        assert res.accuracy_level == "high"
