"""
GeoPulse — Location Tests

Includes the CRITICAL SECURITY TEST (Section 58):
User A must NOT be able to access User B's location
without an active authorized sharing relationship.
"""

from __future__ import annotations

import pytest

from tests import create_test_user, auth_headers


@pytest.mark.asyncio
class TestLocationSecurity:
    """
    CRITICAL SECURITY TESTS — Section 58

    These tests verify the core privacy guarantee of GeoPulse:
    location data is NEVER accessible without explicit authorization.
    """

    async def test_unauthorized_location_access_returns_403(self, client, clean_db):
        """
        *** MANDATORY TEST ***

        User A must NOT be able to:
            GET /api/v1/location/{B_id}
        simply because A knows B's user ID.

        Expected: 403 Forbidden
        """
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")
        user_b_id = str(user_b["_id"])

        response = await client.get(
            f"/api/v1/location/{user_b_id}",
            headers=auth_headers(token_a),
        )
        assert response.status_code == 403, (
            "SECURITY VIOLATION: Unauthorized user was able to access "
            "another user's location without an active sharing relationship!"
        )

    async def test_authorized_location_access_works(self, client, clean_db):
        """
        After establishing an accepted sharing relationship,
        the authorized viewer CAN access the owner's location.
        """
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")
        user_b_id = str(user_b["_id"])

        # Send request (A wants to view B's location)
        send_resp = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543211"},
            headers=auth_headers(token_a),
        )
        share_id = send_resp.json()["share_id"]

        # B accepts
        await client.post(
            f"/api/v1/sharing/{share_id}/accept",
            headers=auth_headers(token_b),
        )

        # Now A should be able to access B's location
        # (will return 404 because B hasn't shared location data yet)
        response = await client.get(
            f"/api/v1/location/{user_b_id}",
            headers=auth_headers(token_a),
        )
        # 404 is correct — B has no location data yet (not 403)
        assert response.status_code == 404

    async def test_revoked_access_returns_403(self, client, clean_db):
        """
        After access is revoked, location should no longer be accessible.
        """
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")
        user_b_id = str(user_b["_id"])

        # Setup sharing
        send_resp = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543211"},
            headers=auth_headers(token_a),
        )
        share_id = send_resp.json()["share_id"]
        await client.post(
            f"/api/v1/sharing/{share_id}/accept",
            headers=auth_headers(token_b),
        )

        # Revoke
        await client.post(
            f"/api/v1/sharing/{share_id}/revoke",
            headers=auth_headers(token_b),
        )

        # Now A should get 403 again
        response = await client.get(
            f"/api/v1/location/{user_b_id}",
            headers=auth_headers(token_a),
        )
        assert response.status_code == 403

    async def test_unauthenticated_access_rejected(self, client, clean_db):
        """Unauthenticated requests should be rejected."""
        response = await client.get("/api/v1/location/some_user_id")
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestLocationHistory:
    """Location history tests."""

    async def test_delete_own_history(self, client, clean_db):
        """User can delete their own location history."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")

        response = await client.delete(
            "/api/v1/location/history",
            headers=auth_headers(token_a),
        )
        assert response.status_code == 200

    async def test_history_without_permission_returns_403(self, client, clean_db):
        """
        Accessing another user's history without history
        permission should return 403.
        """
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")
        user_b_id = str(user_b["_id"])

        # Setup sharing with live-only permission (no history)
        send_resp = await client.post(
            "/api/v1/sharing/request",
            json={
                "target_phone": "+919876543211",
                "permissions": {"live_location": True, "location_history": False},
            },
            headers=auth_headers(token_a),
        )
        share_id = send_resp.json()["share_id"]
        await client.post(
            f"/api/v1/sharing/{share_id}/accept",
            headers=auth_headers(token_b),
        )

        # Try to access history — should be 403
        response = await client.get(
            f"/api/v1/location/{user_b_id}/history",
            headers=auth_headers(token_a),
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestUserSearch:
    """User search privacy tests."""

    async def test_search_returns_no_location_data(self, client, clean_db):
        """Phone search result must NOT contain location data."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")

        response = await client.get(
            "/api/v1/users/search?phone=+919876543211",
            headers=auth_headers(token_a),
        )
        assert response.status_code == 200
        data = response.json()
        # Must NOT contain any location-related fields
        assert "latitude" not in data
        assert "longitude" not in data
        assert "location" not in data
        assert "gps" not in data
        assert "coordinates" not in data
        assert "address" not in data
        # Should contain identity only
        assert "name" in data
        assert "id" in data
