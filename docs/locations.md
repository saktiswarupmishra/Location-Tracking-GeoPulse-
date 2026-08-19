# GeoPulse Location Processing Pipeline

## Ingestion Pipeline (§4 – §10, §35)

Every incoming location update passes through an 8-stage pipeline:

```text
[Incoming Location Update]
           │
           ▼
1. Validate Coordinates (bounds: lat [-90,90], lon [-180,180], reject (0,0))
           │
           ▼
2. Classify Accuracy (High <=10m, Moderate <=100m, Low >100m)
           │
           ▼
3. Anomaly Detection (Teleportation check vs. max plausible speed 150 m/s)
           │
           ▼
4. Server Timestamp Injection (Authoritative UTC timestamp)
           │
           ▼
5. Sequence Ordering (Drop out-of-order/replayed packets)
           │
           ▼
6. Rate Limit / Throttling (Enforce min interval via Redis)
           │
           ▼
7. Critical Path: Upsert Live Location + Publish to Redis Pub/Sub
           │
           ▼
8. Best Effort: Save Location History + Evaluate Geofence Transitions
```

---

## Freshness Status (§8)
- **Live**: Age $\le$ 30 seconds
- **Delayed**: 30 seconds $<$ Age $\le$ 120 seconds
- **Stale**: Age $>$ 120 seconds
- **Unavailable**: No valid location recorded

---

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/locations/me` | Current authenticated user's location |
| `GET` | `/api/v1/locations/{user_id}` | Authorized user's live location |
| `GET` | `/api/v1/locations/{user_id}/history` | Historical path (requires history permission) |
| `DELETE` | `/api/v1/locations/history` | Delete personal location history |
