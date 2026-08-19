"""
GeoPulse — Report Repository (§29)

User reporting with reason categorization and admin review status.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from bson import ObjectId

from app.config.database import get_database


REPORT_REASONS = {
    "harassment", "spam", "fake_location",
    "unwanted_tracking", "impersonation", "other",
}


async def create_report(
    reporter_id: str,
    reported_user_id: str,
    reason: str,
    description: str = "",
) -> Dict[str, Any]:
    """Create a user report."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "reporterId": reporter_id,
        "reportedUserId": reported_user_id,
        "reason": reason if reason in REPORT_REASONS else "other",
        "description": description[:1000],  # cap length
        "status": "pending",  # pending | reviewed | resolved | dismissed
        "createdAt": now,
        "reviewedAt": None,
    }
    result = await db.reports.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_reports_for_user(user_id: str) -> List[Dict[str, Any]]:
    """Get reports filed by a user."""
    db = get_database()
    cursor = db.reports.find({"reporterId": user_id}).sort("createdAt", -1)
    return await cursor.to_list(length=50)


async def delete_all_for_user(user_id: str) -> int:
    """Delete all reports for a user (account deletion)."""
    db = get_database()
    result = await db.reports.delete_many({
        "$or": [{"reporterId": user_id}, {"reportedUserId": user_id}]
    })
    return result.deleted_count
