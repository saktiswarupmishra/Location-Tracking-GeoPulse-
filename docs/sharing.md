# GeoPulse Location Sharing & Consent Protocol

## Fundamental Principle
> **Phone Number $\neq$ Location Access**
> Searching for a user by phone number ONLY retrieves public identity (name, avatar, online status). GPS coordinates are NEVER exposed without explicit bilateral consent.

---

## 1. Consent Lifecycle (§11)

```text
Requester                       Target / Sharer                   MongoDB / Audit
    |                                  |                                 |
    |-- POST /sharing/request -------->|                                 |
    |   (status=pending)               |-- Notification received         |
    |                                  |                                 |
    |                                  |-- POST /sharing/{id}/accept --->|-- Record consent (granted)
    |                                  |                                 |-- Start Location Session
    |<-- WebSocket: SHARING_ACCEPTED --|                                 |-- Audit: SHARING_ACCEPTED
```

---

## 2. Revocation & Blocking (§28)
- Either party can revoke access at any time via `POST /sharing/{id}/stop`.
- Blocking a user immediately:
  - Revokes all active sharing relationships in both directions.
  - Rejects incoming location requests.
  - Emits `SHARING_REVOKED` WebSocket events to terminate active tracking.

---

## 3. Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/sharing/request` | Request location sharing with target |
| `POST` | `/api/v1/sharing/{id}/accept` | Accept request & record consent |
| `POST` | `/api/v1/sharing/{id}/reject` | Decline request & record consent |
| `POST` | `/api/v1/sharing/{id}/stop` | Stop sharing location & stop session |
| `GET` | `/api/v1/sharing` | List active incoming & outgoing shares |
| `GET` | `/api/v1/sharing/pending` | List pending requests requiring response |
