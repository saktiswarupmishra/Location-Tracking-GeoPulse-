"""
GeoPulse — Consent & Audit Tests (§11, §12)

Verifies immutable consent log creation and audit event emission.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest

from app.repositories import audit_repository, consent_repository


@pytest.mark.asyncio
async def test_create_consent_record(mock_db):
    """§11 — Test creating an immutable consent record."""
    with patch("app.repositories.consent_repository.get_database", return_value=mock_db):
        mock_db.location_consents.insert_one = AsyncMock(
            return_value=type("Result", (), {"inserted_id": "consent_123"})()
        )

        doc = await consent_repository.create_consent(
            owner_id="owner_1",
            viewer_id="viewer_1",
            action="granted",
            sharing_id="share_123",
            permissions={"liveLocation": True, "locationHistory": True},
        )

        assert doc["ownerId"] == "owner_1"
        assert doc["viewerId"] == "viewer_1"
        assert doc["action"] == "granted"
        assert doc["sharingId"] == "share_123"
        assert doc["permissions"]["liveLocation"] is True
        mock_db.location_consents.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_create_audit_log_record(mock_db):
    """§12 — Test audit log entry creation."""
    with patch("app.repositories.audit_repository.get_database", return_value=mock_db):
        mock_db.audit_logs.insert_one = AsyncMock(
            return_value=type("Result", (), {"inserted_id": "audit_123"})()
        )

        doc = await audit_repository.create_audit_log(
            actor_id="user_123",
            action="LOGIN",
            resource_type="user",
            resource_id="user_123",
            metadata={"ip": "127.0.0.1"},
        )

        assert doc["actorId"] == "user_123"
        assert doc["action"] == "LOGIN"
        assert doc["resourceType"] == "user"
        mock_db.audit_logs.insert_one.assert_called_once()
