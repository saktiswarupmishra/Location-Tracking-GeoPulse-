"""
GeoPulse — Phone Number Utilities

Validates and normalises phone numbers to E.164 format.
"""

from __future__ import annotations

import re

from fastapi import HTTPException, status

# Regex for E.164: optional +, 7–15 digits
_E164_PATTERN = re.compile(r"^\+?[1-9]\d{6,14}$")


def normalize_phone(phone: str) -> str:
    """
    Normalise a phone number to E.164 format.

    - Strips spaces, dashes, parentheses
    - Ensures it starts with '+'
    - Validates length (7–15 digits)

    Raises HTTPException 400 if invalid.
    """
    # Strip common formatting characters
    cleaned = re.sub(r"[\s\-\(\).]", "", phone.strip())

    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required",
        )

    # Ensure leading '+'
    if not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"

    # Validate
    digits_only = cleaned.lstrip("+")
    if not _E164_PATTERN.match(digits_only):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phone number format: {phone}. Use E.164 format (e.g., +919876543210).",
        )

    return cleaned
