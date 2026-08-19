"""
GeoPulse — Security Tests (§46 / Section 58)

CRITICAL security tests that MUST pass:
- Unauthorized location access → 403
- JWT manipulation → 401
- Refresh token reuse detection
- Blocked user access prevention
- Expired share → 403
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.config.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.services import auth_service


class TestTokenSecurity:
    """JWT token security tests."""

    def test_access_token_has_correct_type(self):
        token = create_access_token("user123")
        payload = decode_token(token)
        assert payload["type"] == "access"
        assert payload["sub"] == "user123"

    def test_refresh_token_has_family_id(self):
        """§13 — Refresh tokens must include family ID."""
        token = create_refresh_token("user123", family_id="family_abc")
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["fid"] == "family_abc"

    def test_refresh_token_has_unique_jti(self):
        """Each refresh token gets a unique JTI."""
        t1 = create_refresh_token("user123", family_id="f1")
        t2 = create_refresh_token("user123", family_id="f1")
        p1 = decode_token(t1)
        p2 = decode_token(t2)
        assert p1["jti"] != p2["jti"]

    def test_token_hash_deterministic(self):
        """SHA-256 hash is deterministic."""
        token = "test_token_value"
        assert hash_token(token) == hash_token(token)

    def test_different_tokens_different_hashes(self):
        assert hash_token("token_a") != hash_token("token_b")


class TestRefreshTokenRotation:
    """§13 — Refresh token rotation and theft detection."""

    @pytest.mark.asyncio
    async def test_reuse_detection_revokes_family(self):
        """
        If an old (already-rotated) refresh token is reused,
        the entire token family MUST be revoked.
        """
        user_id = "user_theft_test"
        family_id = "test_family_id"

        token = create_refresh_token(user_id, family_id=family_id)
        token_hash = hash_token(token)

        with patch("app.services.auth_service.session_repository") as mock_sr, \
             patch("app.services.auth_service.user_repository") as mock_ur, \
             patch("app.services.auth_service.audit_repository") as mock_ar:

            mock_ur.find_by_id = AsyncMock(return_value={"_id": "test", "name": "Test"})

            # Session NOT found → token was already used (theft indicator)
            mock_sr.find_by_token_hash = AsyncMock(return_value=None)
            mock_sr.revoke_family = AsyncMock(return_value=1)
            mock_ar.create_audit_log = AsyncMock()

            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await auth_service.refresh_tokens(token)

            assert exc.value.status_code == 401
            # Family should have been revoked
            mock_sr.revoke_family.assert_called_once_with(family_id)
            # Audit log should have been created
            mock_ar.create_audit_log.assert_called_once()


class TestAuthorizationSecurity:
    """Section 58 — Location access authorization tests."""

    @pytest.mark.asyncio
    async def test_unauthorized_location_access_returns_403(self):
        """
        CRITICAL: Phone number alone must NEVER provide location access.
        A user without an accepted sharing relationship MUST get 403.
        """
        with patch("app.services.location_service.sharing_repository") as mock_sr:
            mock_sr.is_authorized = AsyncMock(return_value=False)

            from fastapi import HTTPException
            from app.services.location_service import get_live_location

            with pytest.raises(HTTPException) as exc:
                await get_live_location(
                    requester_id="stranger",
                    target_user_id="target_user",
                )
            assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_self_access_always_allowed(self):
        """A user can always access their own location."""
        with patch("app.services.location_service.location_repository") as mock_lr:
            mock_lr.get_live_location = AsyncMock(return_value={
                "userId": "user_1",
                "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]},
                "accuracy": 10,
                "serverTimestamp": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            })

            from app.services.location_service import get_live_location
            result = await get_live_location("user_1", "user_1")
            assert result["user_id"] == "user_1"
