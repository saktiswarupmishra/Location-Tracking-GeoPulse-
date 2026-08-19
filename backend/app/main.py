"""
GeoPulse — FastAPI Application Entry Point (v1.1 Hardened)

Assembles all routers, middleware stack, lifecycle hooks, and error handlers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config.database import close_db, connect_db
from app.config.redis import close_redis, connect_redis
from app.config.settings import get_settings
from app.middleware.rate_limiter import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.error_handler import setup_error_handlers

# --- Route imports ---
from app.api import auth, geofences, locations, sharing, sos, users
from app.api import sessions, device_tokens, privacy
from app.websocket.handlers import websocket_endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("geopulse")


# ------------------------------------------------------------------
# Lifespan — startup & shutdown hooks
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: connect/disconnect DB & Redis."""
    logger.info("🚀 GeoPulse v1.1 starting up...")
    await connect_db()
    await connect_redis()
    logger.info("✅ GeoPulse ready.")
    yield
    logger.info("🛑 GeoPulse shutting down...")
    await close_redis()
    await close_db()
    logger.info("👋 GeoPulse stopped.")


# ------------------------------------------------------------------
# FastAPI Application
# ------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title="GeoPulse API",
    description=(
        "Privacy-first real-time location sharing platform. "
        "Phone numbers are used for identity discovery; GPS access "
        "is granted only through explicit user authorization."
    ),
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# --- Middleware Stack (order matters: first added = outermost) ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)

# Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# --- Error Handlers (§31) ---
setup_error_handlers(app)

# --- REST API Routers ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(sharing.router)
app.include_router(locations.router)
app.include_router(geofences.router)
app.include_router(sos.router)
app.include_router(sessions.router)
app.include_router(device_tokens.router)
app.include_router(privacy.router)


# --- WebSocket ---
@app.websocket("/ws/location")
async def ws_location(websocket):
    """WebSocket endpoint for real-time location sharing."""
    await websocket_endpoint(websocket)


# --- Health Check (enhanced §43) ---
@app.get("/health", tags=["System"])
async def health_check():
    """Health check with component-level status reporting."""
    import time
    from app.config.database import database
    from app.config.redis import redis_manager

    result = {
        "status": "healthy",
        "version": "1.1.0",
        "components": {},
    }

    # MongoDB check
    try:
        start = time.monotonic()
        if database.client:
            await database.client.admin.command("ping")
        latency = round((time.monotonic() - start) * 1000, 2)
        result["components"]["mongodb"] = {
            "status": "connected",
            "latency_ms": latency,
        }
    except Exception as e:
        result["components"]["mongodb"] = {"status": "error", "detail": str(e)}
        result["status"] = "degraded"

    # Redis check
    try:
        start = time.monotonic()
        if redis_manager.client:
            await redis_manager.client.ping()
        latency = round((time.monotonic() - start) * 1000, 2)
        result["components"]["redis"] = {
            "status": "connected",
            "latency_ms": latency,
        }
    except Exception as e:
        result["components"]["redis"] = {"status": "error", "detail": str(e)}
        result["status"] = "degraded"

    # WebSocket stats
    from app.websocket.manager import manager
    result["components"]["websocket"] = {
        "active_connections": manager.active_count,
        "active_users": manager.active_users,
    }

    return result
