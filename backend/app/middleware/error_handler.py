"""
GeoPulse — Standardized Error Handler (§31)

Catches all unhandled exceptions and formats them into a
consistent error response with error codes and request IDs.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.middleware.request_id import get_request_id

logger = logging.getLogger("geopulse.error_handler")

# Map HTTP detail strings to error codes
ERROR_CODE_MAP = {
    "You are not authorized to view this user's location": "LOCATION_ACCESS_DENIED",
    "You are not authorized to view this user's location history": "HISTORY_ACCESS_DENIED",
    "Token has expired": "TOKEN_EXPIRED",
    "Invalid token": "TOKEN_INVALID",
    "Invalid or expired OTP": "OTP_INVALID",
    "Too many OTP requests": "OTP_RATE_LIMITED",
    "User not found": "USER_NOT_FOUND",
    "Token has been revoked": "TOKEN_REVOKED",
}


def setup_error_handlers(app: FastAPI) -> None:
    """Register global error handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        error_code = ERROR_CODE_MAP.get(exc.detail, "ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": error_code,
                    "message": exc.detail,
                    "requestId": get_request_id(),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                    "requestId": get_request_id(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        req_id = get_request_id()
        logger.error("Unhandled exception [%s]: %s", req_id, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "requestId": req_id,
                }
            },
        )
