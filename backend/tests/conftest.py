"""
GeoPulse — Test Fixtures (v1.1 Hardened)

Provides async fixtures for testing with PyMongo Async.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.config.settings import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Override event loop for session-scoped async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Test settings with dev mode enabled."""
    return Settings(
        APP_ENV="testing",
        OTP_DEV_MODE=True,
        JWT_SECRET="test_secret_key_for_testing_only_32chars!",
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="geopulse_test",
        REDIS_URL="redis://localhost:6379/1",
    )


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.incr = AsyncMock()
    redis.expire = AsyncMock()
    redis.publish = AsyncMock()
    redis.ping = AsyncMock()
    pipeline = AsyncMock()
    pipeline.get = AsyncMock()
    pipeline.delete = AsyncMock()
    pipeline.execute = AsyncMock(return_value=[None, 0])
    redis.pipeline = MagicMock(return_value=pipeline)
    return redis


@pytest.fixture
def mock_db():
    """Mock Database for testing."""
    db = MagicMock()
    # Set up all 17 collections as AsyncMock
    collections = [
        "users", "location_shares", "live_locations", "location_history",
        "notifications", "geofences", "sos_events", "location_sessions",
        "location_consents", "geofence_states", "emergency_contacts",
        "device_tokens", "user_sessions", "audit_logs", "blocks",
        "reports", "ws_tickets",
    ]
    for col in collections:
        mock_col = AsyncMock()
        mock_col.find = MagicMock(return_value=AsyncMock())
        mock_col.find.return_value.sort = MagicMock(return_value=AsyncMock())
        mock_col.find.return_value.sort.return_value.limit = MagicMock(return_value=AsyncMock())
        mock_col.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(return_value=[])
        mock_col.find.return_value.sort.return_value.to_list = AsyncMock(return_value=[])
        mock_col.find.return_value.to_list = AsyncMock(return_value=[])
        setattr(db, col, mock_col)
    return db


def make_user(
    user_id: str = "user_1",
    phone: str = "+919876543210",
    name: str = "Test User",
) -> dict:
    """Create a test user document."""
    from bson import ObjectId
    return {
        "_id": ObjectId(user_id.ljust(24, "0")[:24]) if len(user_id) < 24 else ObjectId(user_id),
        "phone": phone,
        "name": name,
        "profileImage": None,
        "email": None,
        "isOnline": False,
        "lastActive": datetime.now(timezone.utc),
        "privacySettings": {
            "discoverability": "everyone",
            "locationSharingEnabled": True,
            "defaultShareDuration": "until_stopped",
            "showLastActive": True,
        },
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }
