# GeoPulse WebSocket Protocol

## Connection Setup
- **Endpoint**: `ws://<host>/ws/location?ticket=<one_time_ticket>`
- **Ticket Expiry**: 30 seconds
- **Single Use**: Yes (consumed upon handshake)

---

## Client Events (Client → Server)

| Event | Data Fields | Description |
|---|---|---|
| `PING` | `{}` | Heartbeat check |
| `LOCATION_UPDATE` | `{ latitude, longitude, accuracy, speed, heading, sequence }` | Send live GPS packet |
| `LOCATION_START` | `{}` | Start live tracking broadcast |
| `LOCATION_STOP` | `{}` | Stop live tracking broadcast |
| `LOCATION_SESSION_PAUSE` | `{}` | Pause background session |
| `LOCATION_SESSION_RESUME` | `{}` | Resume background session |
| `SUBSCRIBE_LOCATION` | `{ userId }` | Subscribe to a specific user's updates |
| `UNSUBSCRIBE_LOCATION` | `{ userId }` | Unsubscribe from a user |

---

## Server Events (Server → Client)

| Event | Data Fields | Description |
|---|---|---|
| `PONG` | `{}` | Heartbeat response |
| `LOCATION_UPDATE` | `{ userId, location: { latitude, longitude }, accuracy, speed, timestamp }` | Real-time location packet |
| `USER_ONLINE` | `{ userId }` | Contact joined |
| `USER_OFFLINE` | `{ userId }` | Contact disconnected |
| `GEOFENCE_ENTERED` | `{ geofenceId, geofenceName, userId }` | Geofence arrival alert |
| `GEOFENCE_EXITED` | `{ geofenceId, geofenceName, userId }` | Geofence departure alert |
| `SOS_ALERT` | `{ sosId, userId, userName, latitude, longitude, message }` | Emergency alert |
| `SOS_RESOLVED` | `{ sosId, userId, resolvedAt }` | Emergency resolution |
