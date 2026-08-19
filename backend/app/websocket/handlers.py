"""
GeoPulse — WebSocket Endpoint Handler (v1.1 Hardened)

§15 — Ticket-based auth (no JWT in URL).
§16 — Multi-device connections.
§38 — Session pause/resume.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect

from app.repositories import sharing_repository, user_repository
from app.repositories import session_location_repository
from app.services import location_service, ws_ticket_service
from app.websocket.events import (
    ClientEventType,
    ServerEventType,
    server_event,
)
from app.websocket.manager import manager
from app.websocket.pubsub import start_user_subscriber, stop_user_subscriber

logger = logging.getLogger("geopulse.ws.handler")


async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Main WebSocket endpoint handler.

    §15 — Ticket-based authentication:
    1. Extract ticket from query param (?ticket=...)
    2. Consume ticket (one-time use) — reject with 1008 if invalid
    3. Accept, register in ConnectionManager (multi-device §16)
    4. Start Redis Pub/Sub listener
    5. Enter message loop
    6. On disconnect: cleanup
    """
    # ── Step 1-2: Ticket-based auth ──
    ticket = websocket.query_params.get("ticket")
    if not ticket:
        await websocket.close(code=1008, reason="Missing authentication ticket")
        return

    ticket_data = await ws_ticket_service.consume_ticket(ticket)
    if not ticket_data:
        await websocket.close(code=1008, reason="Invalid or expired ticket")
        return

    user_id = ticket_data["user_id"]
    device_id = ticket_data.get("device_id")

    # ── Step 3: Accept and register (multi-device) ──
    await websocket.accept()
    connection_id = await manager.connect(user_id, websocket, device_id=device_id)
    await user_repository.set_online_status(user_id, True)

    # Notify authorized contacts
    viewer_ids = await sharing_repository.get_authorized_viewer_ids(user_id)
    await manager.send_to_users(
        viewer_ids,
        server_event(ServerEventType.USER_ONLINE, {"userId": user_id}),
    )

    # ── Step 4: Start Redis subscriber ──
    subscriber_task = asyncio.create_task(
        start_user_subscriber(user_id, manager)
    )

    # ── Step 5: Message loop ──
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
                event_type = message.get("event", "").upper()
                data = message.get("data", {})

                await _handle_message(user_id, event_type, data, websocket)

            except json.JSONDecodeError:
                await websocket.send_json(
                    server_event(ServerEventType.ERROR, {"message": "Invalid JSON"})
                )
            except Exception as e:
                logger.error("Error handling message from %s: %s", user_id, e)
                await websocket.send_json(
                    server_event(ServerEventType.ERROR, {"message": str(e)})
                )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s/%s", user_id, connection_id[:8])
    except Exception as e:
        logger.error("WebSocket error for %s: %s", user_id, e)
    finally:
        # ── Step 6: Cleanup ──
        subscriber_task.cancel()
        await stop_user_subscriber(user_id)
        manager.disconnect(user_id, connection_id)

        # Only set offline if no more connections for this user
        if not manager.is_connected(user_id):
            await user_repository.set_online_status(user_id, False)
            await manager.send_to_users(
                viewer_ids,
                server_event(ServerEventType.USER_OFFLINE, {"userId": user_id}),
            )


async def _handle_message(
    user_id: str,
    event_type: str,
    data: dict,
    websocket: WebSocket,
) -> None:
    """Route an incoming WebSocket message to the right handler."""

    if event_type == ClientEventType.PING.value:
        await websocket.send_json(server_event(ServerEventType.PONG))

    elif event_type == ClientEventType.LOCATION_UPDATE.value:
        await _handle_location_update(user_id, data)

    elif event_type == ClientEventType.LOCATION_START.value:
        await websocket.send_json(
            server_event(ServerEventType.LOCATION_STARTED, {"userId": user_id})
        )
        viewer_ids = await sharing_repository.get_authorized_viewer_ids(user_id)
        await manager.send_to_users(
            viewer_ids,
            server_event(ServerEventType.LOCATION_STARTED, {"userId": user_id}),
        )

    elif event_type == ClientEventType.LOCATION_STOP.value:
        await session_location_repository.stop_session(user_id)
        await websocket.send_json(
            server_event(ServerEventType.LOCATION_STOPPED, {"userId": user_id})
        )
        viewer_ids = await sharing_repository.get_authorized_viewer_ids(user_id)
        await manager.send_to_users(
            viewer_ids,
            server_event(ServerEventType.LOCATION_STOPPED, {"userId": user_id}),
        )

    elif event_type == ClientEventType.LOCATION_SESSION_PAUSE.value:
        await session_location_repository.pause_session(user_id)
        await websocket.send_json(
            server_event(ServerEventType.SESSION_PAUSED, {"userId": user_id})
        )

    elif event_type == ClientEventType.LOCATION_SESSION_RESUME.value:
        await session_location_repository.resume_session(user_id)
        await websocket.send_json(
            server_event(ServerEventType.SESSION_RESUMED, {"userId": user_id})
        )

    elif event_type == ClientEventType.SUBSCRIBE_LOCATION.value:
        target_id = data.get("userId")
        if target_id:
            manager.subscribe(user_id, f"location:{target_id}")

    elif event_type == ClientEventType.UNSUBSCRIBE_LOCATION.value:
        target_id = data.get("userId")
        if target_id:
            manager.unsubscribe(user_id, f"location:{target_id}")

    else:
        await websocket.send_json(
            server_event(ServerEventType.ERROR, {"message": f"Unknown event: {event_type}"})
        )


async def _handle_location_update(user_id: str, data: dict) -> None:
    """Process a LOCATION_UPDATE event through the hardened pipeline."""
    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return

    # Parse timestamp
    timestamp = data.get("timestamp")
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            timestamp = datetime.now(timezone.utc)
    elif timestamp is None:
        timestamp = datetime.now(timezone.utc)

    location_data = {
        "latitude": lat,
        "longitude": lon,
        "accuracy": data.get("accuracy"),
        "speed": data.get("speed"),
        "heading": data.get("heading"),
        "altitude": data.get("altitude"),
        "timestamp": timestamp,
        "sequence": data.get("sequence", 0),
        "batteryLevel": data.get("batteryLevel"),
        "isCharging": data.get("isCharging"),
        "provider": data.get("provider"),
        "activityType": data.get("activityType"),
    }

    await location_service.update_location(user_id, location_data)
