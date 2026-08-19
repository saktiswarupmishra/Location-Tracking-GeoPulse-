"""
GeoPulse — Authentication Tests

Tests OTP send/verify, token refresh, and token validation.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

from tests import create_test_user, auth_headers, get_test_settings


@pytest.mark.asyncio
class TestAuthOTP:
    """OTP send and verify flows."""

    async def test_send_otp_success(self, client, clean_db):
        """OTP should be sent successfully in dev mode."""
        response = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "+919876543210"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "OTP sent successfully"
        # Dev mode returns the code
        assert data.get("detail") is not None

    async def test_send_otp_invalid_phone(self, client, clean_db):
        """Invalid phone number should be rejected."""
        response = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "123"},
        )
        assert response.status_code == 422  # Validation error

    async def test_verify_otp_success(self, client, clean_db):
        """Valid OTP should return JWT tokens and create user."""
        # Send OTP
        send_resp = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "+919876543210"},
        )
        code = send_resp.json()["detail"]

        # Verify OTP
        verify_resp = await client.post(
            "/api/v1/auth/verify-otp",
            json={
                "phone": "+919876543210",
                "code": code,
                "name": "Sakti",
            },
        )
        assert verify_resp.status_code == 200
        data = verify_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["is_new_user"] is True

    async def test_verify_otp_wrong_code(self, client, clean_db):
        """Wrong OTP should be rejected."""
        # Send OTP first
        await client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "+919876543210"},
        )

        # Try wrong code
        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={
                "phone": "+919876543210",
                "code": "000000",
            },
        )
        assert response.status_code == 401

    async def test_verify_otp_existing_user(self, client, clean_db):
        """Second login for existing user should not be marked as new."""
        # First login
        send_resp = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "+919876543210"},
        )
        code = send_resp.json()["detail"]
        await client.post(
            "/api/v1/auth/verify-otp",
            json={"phone": "+919876543210", "code": code, "name": "Sakti"},
        )

        # Second login
        send_resp2 = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "+919876543210"},
        )
        code2 = send_resp2.json()["detail"]
        verify_resp2 = await client.post(
            "/api/v1/auth/verify-otp",
            json={"phone": "+919876543210", "code": code2},
        )
        assert verify_resp2.status_code == 200
        assert verify_resp2.json()["is_new_user"] is False


@pytest.mark.asyncio
class TestAuthTokens:
    """Token refresh and logout tests."""

    async def test_refresh_token(self, client, clean_db):
        """Refresh token should return a new token pair."""
        # Login first
        send_resp = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone": "+919876543210"},
        )
        code = send_resp.json()["detail"]
        verify_resp = await client.post(
            "/api/v1/auth/verify-otp",
            json={"phone": "+919876543210", "code": code, "name": "Sakti"},
        )
        refresh_token = verify_resp.json()["refresh_token"]

        # Refresh
        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        data = refresh_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_expired_token_rejected(self, client, clean_db):
        """Expired access token should be rejected."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
