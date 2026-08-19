# GeoPulse Authentication Architecture

## Overview
GeoPulse uses a privacy-first, phone-number-based authentication flow with JWT tokens, refresh token rotation (§13), device session tracking (§14), and ticket-based WebSocket authentication (§15).

---

## 1. Authentication Flow

```text
Client                          Server                           Twilio / Redis
  |                                |                                   |
  |-- POST /auth/send-otp -------->|-- Send verification code -------->|
  |                                |                                   |
  |-- POST /auth/verify-otp ------>|-- Verify code ------------------->|
  |<-- { access, refresh } --------|
  |                                |
  |-- POST /auth/ws-ticket ------->|-- Generate one-time ticket -------> Redis
  |<-- { ticket } -----------------|
  |                                |
  |-- ws://host/ws/location?ticket=|-- Consume ticket & connect
```

---

## 2. Refresh Token Rotation (§13)
1. Refresh tokens include a unique `family_id` (ULID) and `jti`.
2. Stored in MongoDB as SHA-256 hashes (`user_sessions`).
3. If an old, already-rotated refresh token is used, **token theft is detected**:
   - The entire token family is immediately revoked.
   - All associated device sessions are terminated.
   - An audit log event (`TOKEN_FAMILY_REVOKED`) is emitted.

---

## 3. Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/send-otp` | Send 6-digit OTP code | No |
| `POST` | `/api/v1/auth/verify-otp` | Verify OTP, create session & issue tokens | No |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token & issue new pair | Refresh Token |
| `POST` | `/api/v1/auth/logout` | Invalidate current device session | Bearer JWT |
| `POST` | `/api/v1/auth/ws-ticket` | Issue 30s one-time WebSocket ticket | Bearer JWT |
