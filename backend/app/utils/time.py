"""
GeoPulse — Time Utilities
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current time in UTC with timezone info."""
    return datetime.now(timezone.utc)


def is_expired(dt: datetime | None) -> bool:
    """Check if a datetime is in the past."""
    if dt is None:
        return False
    return dt < utc_now()
