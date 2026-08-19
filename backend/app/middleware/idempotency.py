"""
GeoPulse — Idempotency Middleware (§33)

Redis-backed idempotency key support for non-GET requests.
Clients send X-Idempotency-Key header to prevent duplicate operations.
"""

from __future__ import annotations

import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.config.redis import get_redis

logger = logging.getLogger("geopulse.idempotency")

# Only apply to mutation endpoints
IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# TTL for idempotency keys (10 minutes)
IDEMPOTENCY_TTL = 600


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    If a request includes X-Idempotency-Key, cache the response
    and return the cached version on subsequent identical requests.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in IDEMPOTENT_METHODS:
            return await call_next(request)

        idem_key = request.headers.get("X-Idempotency-Key")
        if not idem_key:
            return await call_next(request)

        redis_key = f"idempotency:{idem_key}"

        try:
            redis = get_redis()
            cached = await redis.get(redis_key)
            if cached:
                data = json.loads(cached)
                return JSONResponse(
                    status_code=data["status_code"],
                    content=data["body"],
                    headers={"X-Idempotent-Replayed": "true"},
                )
        except Exception:
            # If Redis is down, proceed normally
            pass

        response: Response = await call_next(request)

        # Cache successful responses
        if 200 <= response.status_code < 300:
            try:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk if isinstance(chunk, bytes) else chunk.encode()

                cache_data = json.dumps({
                    "status_code": response.status_code,
                    "body": json.loads(body),
                })
                await redis.set(redis_key, cache_data, ex=IDEMPOTENCY_TTL)

                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception:
                pass

        return response
