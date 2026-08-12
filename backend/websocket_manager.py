from fastapi import WebSocket
from typing import List, Dict, Any
import logging
import json

class ConnectionManager:
    """
    WebSocket Pub/Sub Connection Manager.
    Broadcasts live patient vitals, ECG/PPG telemetry streams,
    and low-latency Edge AI alerts to all connected clinical frontend clients.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"WebSocket client connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info(f"WebSocket client disconnected. Total active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Sends JSON message to all active dashboard WebSocket subscribers.
        """
        if not self.active_connections:
            return

        disconnected_clients = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_clients.append(connection)

        for dead_client in disconnected_clients:
            self.disconnect(dead_client)

ws_manager = ConnectionManager()
