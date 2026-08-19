"""
GeoPulse — Sharing Tests

Tests the location-sharing request flow:
send, accept, reject, revoke, and duplicate prevention.
"""

from __future__ import annotations

import pytest

from tests import create_test_user, auth_headers


@pytest.mark.asyncio
class TestSharingRequests:
    """Location sharing request flow."""

    async def test_send_request(self, client, clean_db):
        """User A can send a sharing request to User B."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")

        response = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543211"},
            headers=auth_headers(token_a),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "share_id" in data

    async def test_accept_request(self, client, clean_db):
        """Owner (User B) can accept a sharing request."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")

        # Send request
        send_resp = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543211"},
            headers=auth_headers(token_a),
        )
        share_id = send_resp.json()["share_id"]

        # Accept as User B (owner)
        accept_resp = await client.post(
            f"/api/v1/sharing/{share_id}/accept",
            headers=auth_headers(token_b),
        )
        assert accept_resp.status_code == 200

    async def test_reject_request(self, client, clean_db):
        """Owner can reject a sharing request."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")

        send_resp = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543211"},
            headers=auth_headers(token_a),
        )
        share_id = send_resp.json()["share_id"]

        reject_resp = await client.post(
            f"/api/v1/sharing/{share_id}/reject",
            headers=auth_headers(token_b),
        )
        assert reject_resp.status_code == 200

    async def test_revoke_access(self, client, clean_db):
        """Either party can revoke an accepted share."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")

        send_resp = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543211"},
            headers=auth_headers(token_a),
        )
        share_id = send_resp.json()["share_id"]

        # Accept
        await client.post(
            f"/api/v1/sharing/{share_id}/accept",
            headers=auth_headers(token_b),
        )

        # Revoke
        revoke_resp = await client.post(
            f"/api/v1/sharing/{share_id}/revoke",
            headers=auth_headers(token_b),
        )
        assert revoke_resp.status_code == 200

    async def test_duplicate_request_prevented(self, client, clean_db):
        """Cannot send duplicate sharing request."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")
        user_b, token_b = await create_test_user("+919876543211", "Rahul")

        # First request
        await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543211"},
            headers=auth_headers(token_a),
        )

        # Duplicate
        dup_resp = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543211"},
            headers=auth_headers(token_a),
        )
        assert dup_resp.status_code == 409

    async def test_request_nonexistent_user(self, client, clean_db):
        """Requesting a non-existent user returns 404."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")

        response = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+910000000000"},
            headers=auth_headers(token_a),
        )
        assert response.status_code == 404

    async def test_self_request_rejected(self, client, clean_db):
        """Cannot send a sharing request to yourself."""
        user_a, token_a = await create_test_user("+919876543210", "Sakti")

        response = await client.post(
            "/api/v1/sharing/request",
            json={"target_phone": "+919876543210"},
            headers=auth_headers(token_a),
        )
        assert response.status_code == 400
