"""
GeoPulse — Geofence Tests

Tests geofence CRUD and enter/exit detection.
"""

from __future__ import annotations

import pytest

from tests import create_test_user, auth_headers
from app.utils.geo import haversine_distance, is_within_radius


@pytest.mark.asyncio
class TestGeofenceCRUD:
    """Geofence creation, listing, and deletion."""

    async def test_create_geofence(self, client, clean_db):
        """User can create a geofence zone."""
        user, token = await create_test_user("+919876543210", "Sakti")

        response = await client.post(
            "/api/v1/geofences",
            json={
                "name": "Home",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "radius_meters": 500,
            },
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Home"
        assert data["radius_meters"] == 500

    async def test_list_geofences(self, client, clean_db):
        """User can list their geofences."""
        user, token = await create_test_user("+919876543210", "Sakti")

        # Create two geofences
        await client.post(
            "/api/v1/geofences",
            json={"name": "Home", "latitude": 28.6139, "longitude": 77.2090, "radius_meters": 500},
            headers=auth_headers(token),
        )
        await client.post(
            "/api/v1/geofences",
            json={"name": "Office", "latitude": 28.6200, "longitude": 77.2100, "radius_meters": 200},
            headers=auth_headers(token),
        )

        response = await client.get(
            "/api/v1/geofences",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_delete_geofence(self, client, clean_db):
        """User can delete their own geofence."""
        user, token = await create_test_user("+919876543210", "Sakti")

        create_resp = await client.post(
            "/api/v1/geofences",
            json={"name": "Home", "latitude": 28.6139, "longitude": 77.2090, "radius_meters": 500},
            headers=auth_headers(token),
        )
        gf_id = create_resp.json()["id"]

        delete_resp = await client.delete(
            f"/api/v1/geofences/{gf_id}",
            headers=auth_headers(token),
        )
        assert delete_resp.status_code == 200


class TestGeoUtils:
    """Test geospatial utility functions (no DB needed)."""

    def test_haversine_same_point(self):
        """Distance between same point should be 0."""
        d = haversine_distance(28.6139, 77.2090, 28.6139, 77.2090)
        assert d == pytest.approx(0, abs=0.1)

    def test_haversine_known_distance(self):
        """Test with a known distance (Delhi to Agra ≈ 200km)."""
        d = haversine_distance(28.6139, 77.2090, 27.1767, 78.0081)
        assert 190_000 < d < 210_000  # ~200km

    def test_is_within_radius_true(self):
        """Point within radius should return True."""
        assert is_within_radius(28.6140, 77.2091, 28.6139, 77.2090, 500) is True

    def test_is_within_radius_false(self):
        """Point outside radius should return False."""
        assert is_within_radius(28.6200, 77.2200, 28.6139, 77.2090, 100) is False
