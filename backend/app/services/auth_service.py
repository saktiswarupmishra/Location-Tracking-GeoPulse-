"""
GeoPulse — Authentication Service (v1.1 Hardened)

OTP send/verify via Twilio (or dev-mode bypass),
JWT token management with refresh token rotation (§13),
device session tracking (§14), and audit logging (§12).
"""

from __future__ import annotations

import logging
import random
import string
from typing import Any, Dict, Tuple

from fastapi import HTTPException, status

from app.config.redis import get_redis
from app.config.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.config.settings import get_settings
from app.repositories import audit_repository, session_repository, user_repository
from app.utils.phone import normalize_phone

logger = logging.getLogger("geopulse.auth")


# ──────────────────────────────────────────
# OTP (§39 — production safety guarded)
# ──────────────────────────────────────────

async def send_otp(phone: str) -> Dict[str, Any]:
    """
    Send an OTP to the given phone number.

    Dev mode: random code stored in Redis (logged).
    Production: Twilio Verify API.
    """
    phone = normalize_phone(phone)
    settings = get_settings()

    # Rate limit check via Redis
    redis = get_redis()
    rate_key = f"otp_rate:{phone}"
    attempts = await redis.get(rate_key)
    if attempts and int(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please try again later.",
        )
    await redis.incr(rate_key)
    await redis.expire(rate_key, 300)

    if settings.OTP_DEV_MODE:
        code = "".join(random.choices(string.digits, k=6))
        otp_key = f"otp:{phone}"
        await redis.set(otp_key, code, ex=300)
        logger.info("📱 DEV OTP for %s: %s", phone, code)
        return {"message": "OTP sent successfully", "dev_code": code}
    else:
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.verify.v2.services(
                settings.TWILIO_VERIFY_SERVICE_SID
            ).verifications.create(to=phone, channel="sms")
            return {"message": "OTP sent successfully"}
        except Exception as e:
            logger.error("Twilio OTP send failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP. Please try again.",
            )


# ──────────────────────────────────────────
# Verify OTP & Issue Tokens (§13 + §14)
# ──────────────────────────────────────────

async def verify_otp(
    phone: str,
    code: str,
    name: str | None = None,
    device_id: str | None = None,
    platform: str | None = None,
) -> Tuple[Dict[str, Any], bool]:
    """
    Verify OTP and return JWT tokens with token family tracking.

    Creates a new user if first login.
    Creates a user_session (device session) record.

    Returns: (token_dict, is_new_user)
    """
    phone = normalize_phone(phone)
    settings = get_settings()

    # Verify the code
    if settings.OTP_DEV_MODE:
        redis = get_redis()
        otp_key = f"otp:{phone}"
        stored_code = await redis.get(otp_key)
        if not stored_code or stored_code != code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP",
            )
        await redis.delete(otp_key)
    else:
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            verification_check = client.verify.v2.services(
                settings.TWILIO_VERIFY_SERVICE_SID
            ).verification_checks.create(to=phone, code=code)
            if verification_check.status != "approved":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired OTP",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Twilio OTP verify failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OTP verification failed",
            )

    # Find or create user
    is_new_user = False
    user = await user_repository.find_by_phone(phone)
    if not user:
        if not name:
            name = "User"
        user = await user_repository.create_user(phone=phone, name=name)
        is_new_user = True

    user_id = str(user["_id"])

    # Generate tokens — new family per login
    from ulid import ULID
    family_id = str(ULID())
    access_token = create_access_token(user_id, device_id=device_id)
    refresh_token = create_refresh_token(
        user_id, family_id=family_id, device_id=device_id,
    )

    # §14 — Create device session
    await session_repository.create_session(
        user_id=user_id,
        refresh_token=refresh_token,
        family_id=family_id,
        device_id=device_id,
        platform=platform,
    )

    # §12 — Audit log
    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="LOGIN",
        resource_type="user",
        resource_id=user_id,
        metadata={"device_id": device_id, "platform": platform, "is_new_user": is_new_user},
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "is_new_user": is_new_user,
    }, is_new_user


# ──────────────────────────────────────────
# Token Refresh (§13 — Rotation with theft detection)
# ──────────────────────────────────────────

async def refresh_tokens(
    refresh_token: str,
) -> Dict[str, str]:
    """
    Validate a refresh token and issue a new pair.

    §13 — Refresh Token Rotation:
    1. Decode token, extract family_id
    2. Look up session by hashed token
    3. If session not found → token was already rotated → THEFT DETECTED
       → Revoke entire family (force re-login)
    4. If found → rotate: update hash to new token, return new pair
    """
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh token",
        )

    user_id = payload.get("sub")
    family_id = payload.get("fid")
    if not user_id or not family_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify user still exists
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # §13 — Look up session by hashed token
    token_hash = hash_token(refresh_token)
    session = await session_repository.find_by_token_hash(token_hash)

    if not session:
        # THEFT DETECTED — token was already used/rotated
        # Revoke the entire family
        logger.warning(
            "🚨 Refresh token reuse detected! Revoking family %s for user %s",
            family_id, user_id,
        )
        await session_repository.revoke_family(family_id)
        await audit_repository.create_audit_log(
            actor_id=user_id,
            action="TOKEN_FAMILY_REVOKED",
            resource_type="token_family",
            resource_id=family_id,
            metadata={"reason": "token_reuse_detected"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked — please log in again",
        )

    if session.get("revokedAt"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked",
        )

    # Issue new pair (same family)
    device_id = payload.get("did")
    new_access = create_access_token(user_id, device_id=device_id)
    new_refresh = create_refresh_token(
        user_id, family_id=family_id, device_id=device_id,
    )

    # Rotate — update the stored hash
    await session_repository.rotate_token(
        old_token_hash=token_hash,
        new_refresh_token=new_refresh,
        family_id=family_id,
    )

    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="TOKEN_REFRESHED",
        resource_type="token_family",
        resource_id=family_id,
    )

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


# ──────────────────────────────────────────
# Logout
# ──────────────────────────────────────────

async def logout(
    user_id: str,
    refresh_token: str | None = None,
) -> None:
    """Logout: set user offline, revoke session if token provided."""
    await user_repository.set_online_status(user_id, False)

    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            family_id = payload.get("fid")
            if family_id:
                # Revoke the specific session
                token_hash = hash_token(refresh_token)
                session = await session_repository.find_by_token_hash(token_hash)
                if session:
                    await session_repository.revoke_session(
                        str(session["_id"]), user_id,
                    )
        except Exception:
            pass

    await audit_repository.create_audit_log(
        actor_id=user_id,
        action="LOGOUT",
        resource_type="user",
        resource_id=user_id,
    )
