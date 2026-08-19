"""
GeoPulse — Redis Connection Manager

Uses redis-py (with hiredis accelerator) for async operations.
Provides a singleton client + Pub/Sub helpers for real-time
location broadcasting across multiple server instances.
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
