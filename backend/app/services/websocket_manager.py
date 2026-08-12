import asyncio
import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("uvicorn.error")

class ConnectionManager:
    """
    WebSocket Connection Manager.
    Manages active clinical dashboard client connections and broadcasts
    real-time multi-patient telemetry, Edge AI predictions, and status updates.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
        self.loop = None

    async def connect(self, websocket: WebSocket):
        """Accepts new WebSocket connection and adds to active list."""
        await websocket.accept()
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"[WEBSOCKET] Client connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Removes disconnected WebSocket from active list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"[WEBSOCKET] Client disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Non-blocking broadcast sending JSON messages to all connected clients.
        Prunes dead or broken connections safely without raising exceptions or blocking event loop.
        """
        if not self.active_connections:
            return

        disconnected_sockets = []
        async with self._lock:
            target_connections = list(self.active_connections)

        for connection in target_connections:
            try:
                await connection.send_json(message)
            except (WebSocketDisconnect, RuntimeError, Exception) as e:
                logger.warning(f"[WEBSOCKET] Error sending message to client: {e}. Marking for disconnection.")
                disconnected_sockets.append(connection)

        # Remove disconnected sockets
        if disconnected_sockets:
            async with self._lock:
                for dead_ws in disconnected_sockets:
                    if dead_ws in self.active_connections:
                        self.active_connections.remove(dead_ws)

    def broadcast_sync(self, message: Dict[str, Any]):
        """Thread-safe synchronous wrapper for broadcasting from background threads."""
        if not self.active_connections:
            return
        try:
            loop = self.loop or asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
            else:
                loop.run_until_complete(self.broadcast(message))
        except Exception as e:
            logger.warning(f"[WEBSOCKET SYNC BROADCAST WARNING] {e}")

ws_manager = ConnectionManager()
