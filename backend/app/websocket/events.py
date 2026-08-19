"""
GeoPulse — WebSocket Event Types (v1.1 Hardened)

Client → Server and Server → Client event definitions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class ClientEventType(str, Enum):
    """Events sent by the client."""
    PING = "PING"
    LOCATION_UPDATE = "LOCATION_UPDATE"
    LOCATION_START = "LOCATION_START"
    LOCATION_STOP = "LOCATION_STOP"
    LOCATION_SESSION_PAUSE = "LOCATION_SESSION_PAUSE"
    LOCATION_SESSION_RESUME = "LOCATION_SESSION_RESUME"
    SUBSCRIBE_LOCATION = "SUBSCRIBE_LOCATION"
    UNSUBSCRIBE_LOCATION = "UNSUBSCRIBE_LOCATION"


class ServerEventType(str, Enum):
    """Events sent by the server."""
    PONG = "PONG"
    ERROR = "ERROR"
    LOCATION_UPDATE = "LOCATION_UPDATE"
    LOCATION_STARTED = "LOCATION_STARTED"
    LOCATION_STOPPED = "LOCATION_STOPPED"
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_STOPPED = "SESSION_STOPPED"
    SESSION_PAUSED = "SESSION_PAUSED"
    SESSION_RESUMED = "SESSION_RESUMED"
    USER_ONLINE = "USER_ONLINE"
    USER_OFFLINE = "USER_OFFLINE"
    SHARING_REQUEST = "SHARING_REQUEST"
    SHARING_ACCEPTED = "SHARING_ACCEPTED"
    SHARING_REVOKED = "SHARING_REVOKED"
    GEOFENCE_ENTERED = "GEOFENCE_ENTERED"
    GEOFENCE_EXITED = "GEOFENCE_EXITED"
    SOS_ALERT = "SOS_ALERT"
    SOS_RESOLVED = "SOS_RESOLVED"
    NOTIFICATION = "NOTIFICATION"


def server_event(
    event_type: ServerEventType,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a server event payload."""
    return {
        "event": event_type.value,
        "data": data or {},
    }
