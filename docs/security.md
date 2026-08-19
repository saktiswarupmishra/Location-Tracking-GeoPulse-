# GeoPulse Security Architecture

## Core Security Controls

### 1. Privacy & Authorization (§58)
- Zero secret tracking: GPS coordinates are never accessible without an active, explicit sharing record in MongoDB.
- Request validation: Coordinates, speeds, timestamps, and sequence numbers are sanitized and validated before acceptance.

### 2. Token Security (§13, §14)
- **Short-Lived Access Tokens**: 15-minute validity with HMAC-SHA256 signature.
- **Refresh Token Rotation**: New refresh token issued on every refresh. Reuse of an old refresh token instantly invalidates the entire token family.
- **Hashed Token Storage**: Refresh tokens are never stored in plaintext in the database (SHA-256 hashes only).

### 3. Attack Surface Defense (§1, §32, §33)
- **Security Headers Middleware**: HSTS, X-Content-Type-Options, X-Frame-Options, CSP, and Referrer-Policy headers on all HTTP responses.
- **Request ID Tracking**: Unique ULID generated for every request and propagated through context and response headers.
- **Idempotency Support**: Redis-backed cache for `X-Idempotency-Key` headers on mutating requests.
- **Production Guardrails**: Server aborts startup if `OTP_DEV_MODE=True` or default secrets are detected in `APP_ENV=production`.
