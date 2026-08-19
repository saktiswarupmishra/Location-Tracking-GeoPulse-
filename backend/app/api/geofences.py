"""
GeoPulse — Geofence API Routes

POST   /api/v1/geofences
GET    /api/v1/geofences
DELETE /api/v1/geofences/{id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.security import get_current_user_id
from app.schemas.auth import MessageResponse
from app.schemas.geofence import GeofenceCreate, GeofenceResponse
from app.services import geofence_service

router = APIRouter(prefix="/api/v1/geofences", tags=["Geofences"])


@router.post("", response_model=GeofenceResponse)
async def create_geofence(
    request: GeofenceCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new geofence zone."""
    data = {
        "name": request.name,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "radius_meters": request.radius_meters,
    }
    gf = await geofence_service.create_geofence(user_id, data)
    return GeofenceResponse(**gf)


@router.get("", response_model=list[GeofenceResponse])
async def get_my_geofences(user_id: str = Depends(get_current_user_id)):
    """List all active geofences for the authenticated user."""
    geofences = await geofence_service.get_geofences(user_id)
    return [GeofenceResponse(**gf) for gf in geofences]


@router.delete("/{geofence_id}", response_model=MessageResponse)
async def delete_geofence(
    geofence_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a geofence."""
    success = await geofence_service.delete_geofence(user_id, geofence_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geofence not found or not authorized",
        )
    return MessageResponse(message="Geofence deleted")
