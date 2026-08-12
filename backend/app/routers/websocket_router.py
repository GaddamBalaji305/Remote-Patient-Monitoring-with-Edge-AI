import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.websocket_manager import ws_manager

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/monitoring")
@router.websocket("/api/ws/monitoring")
async def websocket_monitoring_endpoint(websocket: WebSocket):
    """
    Real-Time Clinical Telemetry & Edge AI WebSocket Endpoint (/ws/monitoring).
    Broadcasts live patient vitals, Edge AI predictions, risk scores, and status updates.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive ping / control messages from connected dashboard client
            data = await websocket.receive_text()
            logger.debug(f"[WEBSOCKET RECV] {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"[WEBSOCKET ERROR] Unexpected connection error: {e}")
        ws_manager.disconnect(websocket)
