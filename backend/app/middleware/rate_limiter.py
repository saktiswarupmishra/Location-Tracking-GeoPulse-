"""
GeoPulse — Rate Limiting Middleware

Uses SlowAPI for leaky-bucket rate limiting with
route-specific limits.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance (uses client IP by default)
limiter = Limiter(key_func=get_remote_address)
