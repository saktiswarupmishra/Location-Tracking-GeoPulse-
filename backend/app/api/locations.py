"""
GeoPulse — Location API Routes

GET    /api/v1/location/me
GET    /api/v1/location/{user_id}
GET    /api/v1/location/{user_id}/history
DELETE /api/v1/location/history

Every location endpoint performs authorization checks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.config.security import get_current_user_id
from app.schemas.auth import MessageResponse
from app.schemas.location import LocationResponse
from app.services import location_service

router = APIRouter(prefix="/api/v1/location", tags=["Location"])


@router.get("/me", response_model=LocationResponse)
async def get_my_location(user_id: str = Depends(get_current_user_id)):
    """Get the authenticated user's current location."""
    data = await location_service.get_my_location(user_id)
    return LocationResponse(**data)


@router.get("/{target_user_id}", response_model=LocationResponse)
async def get_user_location(
    target_user_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Get another user's live location.

    Requires an active, accepted sharing relationship with
    live-location permission. Returns 403 Forbidden if
    the requester is not authorized.
    """
    data = await location_service.get_live_location(user_id, target_user_id)
    return LocationResponse(**data)


@router.get("/{target_user_id}/history", response_model=dict)
async def get_location_history(
    target_user_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(default=1000, le=5000),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get a user's location history.

    For another user's history, requires history permission
    in the sharing relationship.
    """
    return await location_service.get_history(
        requester_id=user_id,
        target_user_id=target_user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.delete("/history", response_model=MessageResponse)
async def delete_my_history(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: str = Depends(get_current_user_id),
):
    """Delete the authenticated user's own location history."""
    deleted = await location_service.delete_history(user_id, start_date, end_date)
    return MessageResponse(message=f"Deleted {deleted} history points")
