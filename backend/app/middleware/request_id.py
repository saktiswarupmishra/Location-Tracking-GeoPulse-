"""
GeoPulse — Request ID Middleware (§32)

Generates a unique request ID (ULID) for every incoming request.
Injects it into the response headers and logging context.
"""

from __future__ import annotations

import contextvars
from ulid import ULID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context var for access in any async handler
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request/response."""

    async def dispatch(self, request: Request, call_next):
        # Accept client-provided ID or generate
        req_id = request.headers.get("X-Request-ID") or f"req_{ULID()}"
        request_id_ctx.set(req_id)
        request.state.request_id = req_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_ctx.get("")
