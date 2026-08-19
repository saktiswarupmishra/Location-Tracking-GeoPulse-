"""
GeoPulse — MongoDB Connection & Index Management (v1.1 Hardened)

Uses PyMongo AsyncMongoClient (replaces deprecated Motor).
Manages 17 collections with geospatial, TTL, and compound indexes.
"""

from __future__ import annotations

import logging

from pymongo import AsyncMongoClient, ASCENDING, DESCENDING, GEOSPHERE
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection

from app.config.settings import get_settings

logger = logging.getLogger("geopulse.database")


class Database:
    """Singleton wrapper around the PyMongo AsyncMongoClient."""

    client: AsyncMongoClient | None = None
    db: AsyncDatabase | None = None

    # -- Original collections --
    users: AsyncCollection | None = None
    location_shares: AsyncCollection | None = None
    live_locations: AsyncCollection | None = None
    location_history: AsyncCollection | None = None
    notifications: AsyncCollection | None = None
    geofences: AsyncCollection | None = None
    sos_events: AsyncCollection | None = None

    # -- New hardened collections (§48) --
    location_sessions: AsyncCollection | None = None
    location_consents: AsyncCollection | None = None
    geofence_states: AsyncCollection | None = None
    emergency_contacts: AsyncCollection | None = None
    device_tokens: AsyncCollection | None = None
    user_sessions: AsyncCollection | None = None
    audit_logs: AsyncCollection | None = None
    blocks: AsyncCollection | None = None
    reports: AsyncCollection | None = None
    ws_tickets: AsyncCollection | None = None


# Module-level singleton
database = Database()


async def connect_db() -> None:
    """Initialise the PyMongo AsyncMongoClient and create indexes."""
    settings = get_settings()
    logger.info("Connecting to MongoDB at %s ...", settings.MONGODB_URI)

    database.client = AsyncMongoClient(settings.MONGODB_URI)
    database.db = database.client[settings.MONGODB_DATABASE]

    # Bind all 17 collection shortcuts
    db = database.db
    database.users = db["users"]
    database.location_shares = db["location_shares"]
    database.live_locations = db["live_locations"]
    database.location_history = db["location_history"]
    database.notifications = db["notifications"]
    database.geofences = db["geofences"]
    database.sos_events = db["sos_events"]

    database.location_sessions = db["location_sessions"]
    database.location_consents = db["location_consents"]
    database.geofence_states = db["geofence_states"]
    database.emergency_contacts = db["emergency_contacts"]
    database.device_tokens = db["device_tokens"]
    database.user_sessions = db["user_sessions"]
    database.audit_logs = db["audit_logs"]
    database.blocks = db["blocks"]
    database.reports = db["reports"]
    database.ws_tickets = db["ws_tickets"]

    # Create indexes
    await _ensure_indexes()
    logger.info("MongoDB connected — database: %s", settings.MONGODB_DATABASE)


async def close_db() -> None:
    """Gracefully close the PyMongo client."""
    if database.client:
        database.client.close()
        logger.info("MongoDB connection closed.")


async def _ensure_indexes() -> None:
    """Create all required indexes idempotently."""
    db = database
    settings = get_settings()

    # --- users ---
    await db.users.create_index("phone", unique=True)
    await db.users.create_index("createdAt")

    # --- location_shares ---
    await db.location_shares.create_index("ownerId")
    await db.location_shares.create_index("viewerId")
    await db.location_shares.create_index("status")
    await db.location_shares.create_index(
        [("ownerId", ASCENDING), ("viewerId", ASCENDING), ("status", ASCENDING)]
    )
    await db.location_shares.create_index("expiresAt")

    # --- live_locations ---
    await db.live_locations.create_index("userId", unique=True)
    await db.live_locations.create_index([("location", GEOSPHERE)])
    # TTL for stale live locations (§26)
    await db.live_locations.create_index(
        "updatedAt",
        expireAfterSeconds=settings.LIVE_LOCATION_TTL_SECONDS,
        name="ttl_live_locations",
    )

    # --- location_history ---
    await db.location_history.create_index("userId")
    await db.location_history.create_index([("location", GEOSPHERE)])
    await db.location_history.create_index(
        [("userId", ASCENDING), ("serverTimestamp", DESCENDING)]
    )
    # TTL index (§25)
    await db.location_history.create_index(
        "serverTimestamp",
        expireAfterSeconds=settings.LOCATION_HISTORY_RETENTION_DAYS * 86400,
        name="ttl_location_history",
    )

    # --- location_sessions (§2) ---
    await db.location_sessions.create_index("ownerId")
    await db.location_sessions.create_index(
        [("ownerId", ASCENDING), ("status", ASCENDING)]
    )
    await db.location_sessions.create_index("sharingId")

    # --- location_consents (§11) ---
    await db.location_consents.create_index(
        [("ownerId", ASCENDING), ("viewerId", ASCENDING)]
    )
    await db.location_consents.create_index("timestamp")

    # --- notifications ---
    await db.notifications.create_index("userId")
    await db.notifications.create_index("createdAt")

    # --- geofences ---
    await db.geofences.create_index("userId")
    await db.geofences.create_index([("center", GEOSPHERE)])

    # --- geofence_states (§19) ---
    await db.geofence_states.create_index(
        [("userId", ASCENDING), ("geofenceId", ASCENDING)],
        unique=True,
    )

    # --- sos_events (§21) ---
    await db.sos_events.create_index("userId")
    await db.sos_events.create_index("triggeredAt")
    await db.sos_events.create_index("status")

    # --- emergency_contacts (§22) ---
    await db.emergency_contacts.create_index("ownerId")
    await db.emergency_contacts.create_index(
        [("ownerId", ASCENDING), ("contactUserId", ASCENDING)],
        unique=True,
    )

    # --- device_tokens (§23) ---
    await db.device_tokens.create_index(
        [("userId", ASCENDING), ("deviceId", ASCENDING)],
        unique=True,
    )
    await db.device_tokens.create_index("pushToken")

    # --- user_sessions (§14) ---
    await db.user_sessions.create_index("userId")
    await db.user_sessions.create_index("refreshTokenHash", unique=True, sparse=True)
    await db.user_sessions.create_index("tokenFamilyId")

    # --- audit_logs (§12) ---
    await db.audit_logs.create_index("actorId")
    await db.audit_logs.create_index("action")
    await db.audit_logs.create_index("timestamp")
    await db.audit_logs.create_index(
        [("resourceType", ASCENDING), ("resourceId", ASCENDING)]
    )

    # --- blocks (§28) ---
    await db.blocks.create_index(
        [("blockerId", ASCENDING), ("blockedId", ASCENDING)],
        unique=True,
    )

    # --- reports (§29) ---
    await db.reports.create_index("reporterId")
    await db.reports.create_index("reportedUserId")
    await db.reports.create_index("status")

    # --- ws_tickets (§15) ---
    await db.ws_tickets.create_index("ticket", unique=True)
    await db.ws_tickets.create_index(
        "createdAt",
        expireAfterSeconds=120,  # cleanup old tickets
        name="ttl_ws_tickets",
    )

    logger.info("All MongoDB indexes ensured (17 collections).")


def get_database() -> Database:
    """Return the Database singleton for use in dependencies."""
    return database
