"""
GeoPulse — Test Configuration & Fixtures

Provides shared fixtures for all test modules:
- Test MongoDB client (separate test database)
- Test Redis client
- FastAPI TestClient
- Authenticated user helpers
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Tuple
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config.database import Database, connect_db, close_db, database
from app.config.redis import connect_redis, close_redis, redis_manager
from app.config.security import create_access_token
from app.config.settings import Settings


# ------------------------------------------------------------------
# Override settings for testing
# ------------------------------------------------------------------

def get_test_settings() -> Settings:
    """Return settings configured for testing."""
    return Settings(
        APP_ENV="testing",
        DEBUG=True,
        MONGODB_URI="mongodb://localhost:27017",
        MONGODB_DATABASE="geopulse_test",
        REDIS_URL="redis://localhost:6379/1",  # Use DB 1 for tests
        JWT_SECRET="test-secret-key-at-least-32-chars-long",
        OTP_DEV_MODE=True,
    )


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Connect to test MongoDB and Redis at session start, cleanup after."""
    with patch("app.config.settings.get_settings", return_value=get_test_settings()):
        await connect_db()
        await connect_redis()
        yield
        # Cleanup: drop test database
        if database.client:
            await database.client.drop_database("geopulse_test")
        await close_db()
        # Flush test Redis DB
        if redis_manager.client:
            await redis_manager.client.flushdb()
        await close_redis()


@pytest_asyncio.fixture
async def client(setup_db) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client for the FastAPI app."""
    with patch("app.config.settings.get_settings", return_value=get_test_settings()):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture
async def clean_db(setup_db):
    """Clean all collections before each test."""
    if database.db:
        collections = await database.db.list_collection_names()
        for col_name in collections:
            await database.db[col_name].delete_many({})
    if redis_manager.client:
        await redis_manager.client.flushdb()
    yield


# ------------------------------------------------------------------
# User creation helpers
# ------------------------------------------------------------------

async def create_test_user(
    phone: str = "+919876543210",
    name: str = "Test User",
) -> Tuple[Dict, str]:
    """
    Create a test user directly in the database.
    Returns (user_doc, access_token).
    """
    from app.repositories import user_repository
    user = await user_repository.find_by_phone(phone)
    if not user:
        user = await user_repository.create_user(phone=phone, name=name)
    user_id = str(user["_id"])
    token = create_access_token(user_id, settings=get_test_settings())
    return user, token


def auth_headers(token: str) -> Dict[str, str]:
    """Build Authorization headers."""
    return {"Authorization": f"Bearer {token}"}
