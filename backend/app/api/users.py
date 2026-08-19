"""
GeoPulse — User API Routes

GET  /api/v1/users/me
PUT  /api/v1/users/me
GET  /api/v1/users/search?phone=
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config.security import get_current_user_id
from app.repositories import user_repository
from app.schemas.user import UserProfile, UserSearchResult, UserUpdate
from app.utils.phone import normalize_phone

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=UserProfile)
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    """Get the authenticated user's profile."""
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    privacy = user.get("privacySettings", {})
    return UserProfile(
        id=str(user["_id"]),
        phone=user["phone"],
        name=user["name"],
        profile_image=user.get("profileImage"),
        email=user.get("email"),
        is_online=user.get("isOnline", False),
        last_active=user.get("lastActive"),
        privacy_settings={
            "discoverability": privacy.get("discoverability", "everyone"),
            "location_sharing_enabled": privacy.get("locationSharingEnabled", True),
        },
        emergency_contacts=user.get("emergencyContacts", []),
        created_at=user.get("createdAt"),
    )


@router.put("/me", response_model=UserProfile)
async def update_my_profile(
    update: UserUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update the authenticated user's profile."""
    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.email is not None:
        update_data["email"] = update.email
    if update.profile_image is not None:
        update_data["profileImage"] = update.profile_image
    if update.privacy_settings is not None:
        update_data["privacySettings"] = {
            "discoverability": update.privacy_settings.discoverability.value,
            "locationSharingEnabled": update.privacy_settings.location_sharing_enabled,
        }

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    user = await user_repository.update_user(user_id, update_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    privacy = user.get("privacySettings", {})
    return UserProfile(
        id=str(user["_id"]),
        phone=user["phone"],
        name=user["name"],
        profile_image=user.get("profileImage"),
        email=user.get("email"),
        is_online=user.get("isOnline", False),
        last_active=user.get("lastActive"),
        privacy_settings={
            "discoverability": privacy.get("discoverability", "everyone"),
            "location_sharing_enabled": privacy.get("locationSharingEnabled", True),
        },
        emergency_contacts=user.get("emergencyContacts", []),
        created_at=user.get("createdAt"),
    )


@router.get("/search", response_model=UserSearchResult | None)
async def search_user(
    phone: str = Query(..., min_length=10, max_length=15),
    user_id: str = Depends(get_current_user_id),
):
    """
    Search for a registered user by phone number.

    Returns ONLY identity information — never location,
    GPS coordinates, address, or movement data.
    """
    phone = normalize_phone(phone)
    user = await user_repository.find_by_phone(phone)
    if not user:
        return None

    # Check discoverability settings
    privacy = user.get("privacySettings", {})
    discoverability = privacy.get("discoverability", "everyone")

    if discoverability == "nobody":
        return None

    # TODO: For "contacts" discoverability, check if searcher is in contacts
    # For now, "contacts" behaves like "everyone"

    return UserSearchResult(
        id=str(user["_id"]),
        name=user["name"],
        profile_image=user.get("profileImage"),
        is_online=user.get("isOnline", False),
    )
