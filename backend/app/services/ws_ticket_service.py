"""
GeoPulse — WebSocket Ticket Service (§15)

Issues and consumes short-lived one-time tickets for WebSocket auth.
Keeps long-lived JWTs out of WebSocket URLs.
"""

from __future__ import annotations

import secrets
from typing import Optional

from app.config.redis import get_redis
from app.config.settings import get_settings


async def create_ticket(user_id: str, device_id: str | None = None) -> str:
    """
    Issue a short-lived one-time WebSocket ticket.

    The ticket is stored in Redis with a short TTL.
    It is consumed (deleted) on first use.

    Returns the ticket string.
    """
    settings = get_settings()
    redis = get_redis()

    ticket = secrets.token_urlsafe(48)
    key = f"ws_ticket:{ticket}"

    # Store user_id (and optionally device_id) in Redis
    value = user_id
    if device_id:
        value = f"{user_id}:{device_id}"

    await redis.set(key, value, ex=settings.WS_TICKET_TTL_SECONDS)
    return ticket


async def consume_ticket(ticket: str) -> Optional[dict]:
    """
    Validate and consume a WebSocket ticket atomically.

    Returns {"user_id": ..., "device_id": ...} if valid.
    Returns None if ticket is invalid, expired, or already used.
    """
    redis = get_redis()
    key = f"ws_ticket:{ticket}"

    # GET + DELETE atomically via pipeline
    pipe = redis.pipeline()
    pipe.get(key)
    pipe.delete(key)
    results = await pipe.execute()

    value = results[0]
    if not value:
        return None

    # Parse value
    parts = value.split(":", 1) if isinstance(value, str) else value.decode().split(":", 1)
    user_id = parts[0]
    device_id = parts[1] if len(parts) > 1 else None

    return {"user_id": user_id, "device_id": device_id}
