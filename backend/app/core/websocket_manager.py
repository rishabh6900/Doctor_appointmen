"""WebSocket Connection Manager for Real-Time Event Broadcasting."""

import asyncio
import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("appointment_system.websocket")


class ConnectionManager:
    """Manages active WebSocket client connections and broadcasts live clinic events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new client WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a disconnected client from the active registry."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event payload to all active connected clients."""
        payload = {
            "event": event_type,
            "data": data,
        }
        message = json.dumps(payload, default=str)

        async with self._lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as exc:
                    logger.warning(f"Failed to send to client: {exc}")
                    disconnected.append(connection)

            for dead in disconnected:
                if dead in self.active_connections:
                    self.active_connections.remove(dead)

    def broadcast_sync(self, event_type: str, data: Dict[str, Any]):
        """Synchronous wrapper for broadcasting from non-async contexts."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(event_type, data))
        except RuntimeError:
            # If no running loop in current thread, run in new thread or loop
            asyncio.run(self.broadcast(event_type, data))


ws_manager = ConnectionManager()
