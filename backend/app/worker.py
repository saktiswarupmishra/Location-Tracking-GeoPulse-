"""
GeoPulse — Background Worker

Placeholder for background jobs such as:
- Expired sharing cleanup
- Location history TTL enforcement (beyond MongoDB TTL)
- Push notification delivery via FCM
- Abuse detection

For now, this is a simple script that runs periodically.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("geopulse.worker")


async def cleanup_expired_shares() -> None:
    """Mark expired shares as expired."""
    from app.config.database import get_database
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.location_shares.update_many(
        {
            "status": "accepted",
            "expiresAt": {"$ne": None, "$lte": now},
        },
        {
            "$set": {
                "status": "expired",
                "stoppedAt": now,
                "updatedAt": now,
            }
        },
    )
    if result.modified_count > 0:
        logger.info("Expired %d sharing sessions", result.modified_count)


async def main() -> None:
    """Worker main loop."""
    from app.config.database import connect_db, close_db
    from app.config.redis import connect_redis, close_redis

    logger.info("🔧 GeoPulse Worker starting...")
    await connect_db()
    await connect_redis()

    try:
        while True:
            await cleanup_expired_shares()
            await asyncio.sleep(60)  # Run every 60 seconds
    except asyncio.CancelledError:
        pass
    finally:
        await close_redis()
        await close_db()
        logger.info("🔧 GeoPulse Worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
