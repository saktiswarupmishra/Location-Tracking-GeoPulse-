"""
GeoPulse — WebSocket Connection Manager (v1.1 Hardened)

Multi-device support (§16): Each user can have multiple connections.
Connections are keyed by userId → {connectionId → WebSocket}.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Set
from uuid import uuid4

from fastapi import WebSocket

logger = logging.getLogger("geopulse.ws.manager")


class ConnectionInfo:
    """Metadata for a single WebSocket connection."""
    __slots__ = ("websocket", "connection_id", "device_id", "connected_at")

    def __init__(self, websocket: WebSocket, device_id: str | None = None):
        self.websocket = websocket
        self.connection_id = str(uuid4())
        self.device_id = device_id
        self.connected_at = datetime.now(timezone.utc)


class ConnectionManager:
    """
    §16 — Multi-device WebSocket connection manager.

    Each user can have multiple active WebSocket connections.
    All connections for a user receive the same events.
    """

    def __init__(self) -> None:
        # user_id → {connection_id → ConnectionInfo}
        self._connections: Dict[str, Dict[str, ConnectionInfo]] = {}
        # user_id → set of channels they're subscribed to
        self._subscriptions: Dict[str, Set[str]] = {}

    @property
    def active_count(self) -> int:
        """Total number of active connections across all users."""
        return sum(len(conns) for conns in self._connections.values())

    @property
    def active_users(self) -> int:
        """Number of users with at least one active connection."""
        return len(self._connections)

    def is_connected(self, user_id: str) -> bool:
        """Check if a user has any active connection."""
        return user_id in self._connections and len(self._connections[user_id]) > 0

    async def connect(
        self,
        user_id: str,
        websocket: WebSocket,
        device_id: str | None = None,
    ) -> str:
        """
        Register a new WebSocket connection.
        Returns the connection_id.
        """
        conn = ConnectionInfo(websocket, device_id)

        if user_id not in self._connections:
            self._connections[user_id] = {}
            self._subscriptions[user_id] = set()

        self._connections[user_id][conn.connection_id] = conn
        logger.info(
            "WebSocket connected: %s (conn=%s, device=%s, user_conns=%d, total=%d)",
            user_id, conn.connection_id[:8], device_id,
            len(self._connections[user_id]), self.active_count,
        )
        return conn.connection_id

    def disconnect(self, user_id: str, connection_id: str | None = None) -> None:
        """
        Remove a specific connection, or all connections for a user.
        """
        if user_id not in self._connections:
            return

        if connection_id:
            self._connections[user_id].pop(connection_id, None)
            if not self._connections[user_id]:
                del self._connections[user_id]
                self._subscriptions.pop(user_id, None)
        else:
            del self._connections[user_id]
            self._subscriptions.pop(user_id, None)

        logger.info(
            "WebSocket disconnected: %s (total=%d)", user_id, self.active_count,
        )

    def subscribe(self, user_id: str, channel: str) -> None:
        """Subscribe a user to a channel."""
        if user_id in self._subscriptions:
            self._subscriptions[user_id].add(channel)

    def unsubscribe(self, user_id: str, channel: str) -> None:
        """Unsubscribe from a channel."""
        if user_id in self._subscriptions:
            self._subscriptions[user_id].discard(channel)

    def get_subscribers(self, channel: str) -> Set[str]:
        """Get all user IDs subscribed to a channel."""
        subscribers = set()
        for uid, channels in self._subscriptions.items():
            if channel in channels:
                subscribers.add(uid)
        return subscribers

    async def send_to_user(self, user_id: str, data: Dict[str, Any]) -> int:
        """
        Send a JSON message to ALL connections for a user.
        Returns number of connections sent to.
        """
        conns = self._connections.get(user_id, {})
        if not conns:
            return 0

        sent = 0
        failed = []
        for conn_id, conn in conns.items():
            try:
                await conn.websocket.send_json(data)
                sent += 1
            except Exception as e:
                logger.warning("Failed to send to %s/%s: %s", user_id, conn_id[:8], e)
                failed.append(conn_id)

        # Clean up failed connections
        for conn_id in failed:
            self._connections.get(user_id, {}).pop(conn_id, None)
        if user_id in self._connections and not self._connections[user_id]:
            del self._connections[user_id]
            self._subscriptions.pop(user_id, None)

        return sent

    async def send_to_users(
        self,
        user_ids: list[str],
        data: Dict[str, Any],
    ) -> int:
        """Broadcast a JSON message to multiple users."""
        sent = 0
        for uid in user_ids:
            sent += await self.send_to_user(uid, data)
        return sent

    async def broadcast(self, data: Dict[str, Any]) -> int:
        """Broadcast to ALL connected users. Use sparingly."""
        return await self.send_to_users(list(self._connections.keys()), data)

    def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """List active connections for a user (for debugging/admin)."""
        conns = self._connections.get(user_id, {})
        return [
            {
                "connection_id": conn.connection_id,
                "device_id": conn.device_id,
                "connected_at": conn.connected_at.isoformat(),
            }
            for conn in conns.values()
        ]


# Module-level singleton
manager = ConnectionManager()
