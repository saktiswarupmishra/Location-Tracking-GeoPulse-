"""
GeoPulse — JWT Security Utilities (v1.1 Hardened)

Handles token creation with family IDs for rotation detection,
validation, and the FastAPI dependency for current user extraction.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ulid import ULID

from app.config.settings import Settings, get_settings

_bearer_scheme = HTTPBearer(auto_error=True)


# ------------------------------------------------------------------
# Token creation (§13 — token family for rotation)
# ------------------------------------------------------------------

def create_access_token(
    user_id: str,
    device_id: str | None = None,
    settings: Settings | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    s = settings or get_settings()
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=s.JWT_ACCESS_EXPIRE_MINUTES),
    }
    if device_id:
        payload["did"] = device_id
    return jwt.encode(payload, s.JWT_SECRET, algorithm=s.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    family_id: str | None = None,
    device_id: str | None = None,
    settings: Settings | None = None,
) -> str:
    """
    Create a long-lived JWT refresh token with a family ID.

    §13 — Token family enables rotation detection:
    - Each login starts a new family (ULID)
    - Each refresh inherits the family
    - If an old token is reused, the entire family is revoked
    """
    s = settings or get_settings()
    now = datetime.now(timezone.utc)
    if not family_id:
        family_id = str(ULID())
    payload: Dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "fid": family_id,  # token family ID
        "iat": now,
        "exp": now + timedelta(days=s.JWT_REFRESH_EXPIRE_DAYS),
        "jti": str(ULID()),  # unique token ID
    }
    if device_id:
        payload["did"] = device_id
    return jwt.encode(payload, s.JWT_SECRET, algorithm=s.JWT_ALGORITHM)


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for storage (never store raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


# ------------------------------------------------------------------
# Token decoding
# ------------------------------------------------------------------

def decode_token(
    token: str,
    settings: Settings | None = None,
) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    s = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            s.JWT_SECRET,
            algorithms=[s.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ------------------------------------------------------------------
# FastAPI dependency — extract current user_id from header
# ------------------------------------------------------------------

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """Extract and validate the JWT, returning the user_id."""
    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected access token",
        )

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    return user_id
