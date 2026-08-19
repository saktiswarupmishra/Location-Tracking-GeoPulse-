"""
GeoPulse — Audit Service (§12)

Thin wrapper over audit_repository with action validation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.repositories import audit_repository

logger = logging.getLogger("geopulse.audit")


async def log(
    actor_id: str,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: Dict[str, Any] | None = None,
    request_id: str | None = None,
) -> None:
    """Create an audit log entry (fire-and-forget)."""
    try:
        await audit_repository.create_audit_log(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
            request_id=request_id,
        )
    except Exception as e:
        logger.warning("Failed to create audit log: %s", e)
