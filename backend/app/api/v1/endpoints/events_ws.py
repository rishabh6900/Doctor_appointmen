"""Real-Time WebSocket Endpoint for Dashboard Event Streaming."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket_manager import ws_manager

logger = logging.getLogger("appointment_system.ws_endpoint")
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard events.
    Streams:
    - appointment_booked
    - appointment_cancelled
    - availability_updated
    - voice_call_started
    - voice_call_ended
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial connection handshake
        await websocket.send_json({
            "event": "connected",
            "data": {"message": "CarePoint Real-Time Event Stream connected."},
        })

        while True:
            # Keep connection open; receive client pings/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning(f"WebSocket client error: {exc}")
        await ws_manager.disconnect(websocket)
