"""
GeoPulse — Application Settings (v1.1 Hardened)

Loads configuration from environment variables / .env file.
Includes production guards, location validation thresholds,
WebSocket ticket config, and consent versioning.
"""

from __future__ import annotations

import json
import sys
import logging
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("geopulse.settings")


class Settings(BaseSettings):
    """Central configuration loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    APP_ENV: str = "development"
    DEBUG: bool = True

    # --- MongoDB ---
    MONGODB_URI: str = "mongodb://localhost:27017/?replicaSet=rs0"
    MONGODB_DATABASE: str = "geopulse"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379"

    # --- JWT ---
    JWT_SECRET: str = "CHANGE_ME_TO_A_RANDOM_SECRET_KEY_AT_LEAST_32_CHARS"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    # --- Twilio ---
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_VERIFY_SERVICE_SID: str = ""
    OTP_DEV_MODE: bool = True

    # --- External ---
    GOOGLE_MAPS_API_KEY: str = ""
    FCM_SERVER_KEY: str = ""

    # --- CORS ---
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:8081"]'

    # --- Rate Limiting ---
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # --- Location History (§25) ---
    LOCATION_HISTORY_RETENTION_DAYS: int = 7

    # --- Location Update Throttling (§7) ---
    LOCATION_UPDATE_MIN_INTERVAL_SECONDS: int = 2

    # --- Stale Location Detection (§8) ---
    LOCATION_STALE_THRESHOLD_SECONDS: int = 60
    LOCATION_DELAYED_THRESHOLD_SECONDS: int = 10

    # --- Live Location TTL (§26) ---
    LIVE_LOCATION_TTL_SECONDS: int = 3600

    # --- WebSocket Ticket (§15) ---
    WS_TICKET_TTL_SECONDS: int = 60

    # --- Privacy Defaults (§27) ---
    DEFAULT_SHARE_DURATION: str = "until_stopped"

    # --- Consent (§11) ---
    CONSENT_VERSION: str = "1.0"

    # --- Location Integrity (§10) ---
    MAX_PLAUSIBLE_SPEED_MPS: float = 340.0  # ~1224 km/h (speed of sound)
    MAX_ACCURACY_METERS: float = 5000.0

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse CORS_ORIGINS JSON string into a list."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["*"]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV in ("development", "testing")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    def validate_production_safety(self) -> None:
        """
        §39 — Fail-fast if production is misconfigured.
        OTP_DEV_MODE must NEVER be true in production.
        """
        if self.is_production and self.OTP_DEV_MODE:
            logger.critical(
                "🚨 FATAL: OTP_DEV_MODE=true in production! "
                "This would bypass phone verification. Shutting down."
            )
            sys.exit(1)
        if self.is_production and "CHANGE_ME" in self.JWT_SECRET:
            logger.critical(
                "🚨 FATAL: Default JWT_SECRET in production! "
                "Set a strong, random secret. Shutting down."
            )
            sys.exit(1)


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    s = Settings()
    s.validate_production_safety()
    return s
