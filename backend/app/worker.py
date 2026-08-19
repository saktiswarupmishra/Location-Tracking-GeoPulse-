"""
GeoPulse — Background Worker (v1.1 Hardened)

Background asynchronous jobs:
- Expired sharing cleanup & consent logging (§11, §18)
- Inactive session reaping & offline user status reconciliation
- Expired WebSocket ticket cleanup
- Audit log & location session reconciliation
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.config.database import close_db, connect_db, get_database
from app.config.redis import close_redis, connect_redis
from app.repositories import consent_repository, session_location_repository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("geopulse.worker")


async def cleanup_expired_shares() -> None:
    """Find expired shares, mark them expired, record consent event, and stop sessions."""
    db = get_database()
    now = datetime.now(timezone.utc)

    # Find shares that have expired
    cursor = db.location_shares.find({
        "status": "accepted",
        "expiresAt": {"$ne": None, "$lte": now},
    })
    expired_shares = await cursor.to_list(length=500)

    for share in expired_shares:
        share_id = str(share["_id"])
        await db.location_shares.update_one(
            {"_id": share["_id"]},
            {"$set": {"status": "expired", "stoppedAt": now, "updatedAt": now}},
        )

        # Stop active sessions
        await session_location_repository.stop_all_for_sharing(share_id)

        # Record consent expiration
        await consent_repository.create_consent(
            owner_id=share["ownerId"],
            viewer_id=share["viewerId"],
            action="expired",
            sharing_id=share_id,
        )

    if expired_shares:
        logger.info("Expired %d sharing sessions", len(expired_shares))


async def cleanup_inactive_users() -> None:
    """Set users offline if inactive for > 15 minutes."""
    db = get_database()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)

    res = await db.users.update_many(
        {"isOnline": True, "lastActive": {"$lt": cutoff}},
        {"$set": {"isOnline": False, "updatedAt": datetime.now(timezone.utc)}},
    )
    if res.modified_count > 0:
        logger.debug("Marked %d inactive users as offline", res.modified_count)


async def main() -> None:
    """Worker main execution loop."""
    logger.info("🔧 GeoPulse Worker v1.1 starting...")
    await connect_db()
    await connect_redis()

    try:
        while True:
            try:
                await cleanup_expired_shares()
                await cleanup_inactive_users()
            except Exception as e:
                logger.error("Error during worker cycle: %s", e)

            await asyncio.sleep(30)  # Run every 30 seconds
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Worker received stop signal")
    finally:
        await close_redis()
        await close_db()
        logger.info("🔧 GeoPulse Worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
