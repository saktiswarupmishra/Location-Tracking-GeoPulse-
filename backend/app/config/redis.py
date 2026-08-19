"""
GeoPulse — Redis Connection Manager (v1.1 Hardened)

Uses redis-py (with hiredis accelerator) for async operations.
Configured with protocol=2 (RESP2) for universal compatibility
across all Redis versions and Windows ports (avoids unknown command 'HELLO').
"""

from __future__ import annotations

import logging

from redis import asyncio as aioredis

from app.config.settings import get_settings

logger = logging.getLogger("geopulse.redis")


class RedisManager:
    """Singleton wrapper around the async Redis client."""

    client: aioredis.Redis | None = None


redis_manager = RedisManager()


async def connect_redis() -> None:
    """Initialise the Redis connection pool."""
    settings = get_settings()
    logger.info("Connecting to Redis at %s ...", settings.REDIS_URL)
    redis_manager.client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        protocol=2,  # Forces RESP2 protocol (compatible with all Redis/Memurai versions)
    )
    # Verify connection
    await redis_manager.client.ping()
    logger.info("Redis connected.")


async def close_redis() -> None:
    """Gracefully close the Redis connection."""
    if redis_manager.client:
        await redis_manager.client.close()
        logger.info("Redis connection closed.")


def get_redis() -> aioredis.Redis:
    """Return the Redis client for use in dependencies / services."""
    if redis_manager.client is None:
        raise RuntimeError("Redis is not connected. Call connect_redis() first.")
    return redis_manager.client
