import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from scripts.seed_database import seed

class TestWebSocketsStep8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)

    def test_01_websocket_connection_and_disconnect(self):
        """Verify client can connect to /ws/monitoring endpoint and disconnect cleanly."""
        with self.client.websocket_connect("/ws/monitoring") as websocket:
            websocket.send_text("ping")
            # Verify connection is active without errors

    def test_02_edge_event_websocket_broadcast_propagation(self):
        """
        Verify end-to-end event propagation:
        Edge Event -> Backend Ingestion API (POST /api/edge/events) -> WebSocket Broadcast -> Connected Client receive_json()
        """
        with self.client.websocket_connect("/ws/monitoring") as websocket:
            payload = {
                "patient_id": "P001",
                "timestamp": "2026-08-12T17:24:54Z",
                "vitals": {
                    "heart_rate": 142.0,
                    "spo2": 88.0,
                    "temperature": 38.8,
                    "respiratory_rate": 24.0,
                    "systolic_bp": 145.0,
                    "diastolic_bp": 92.0,
                    "activity_level": "MODERATE_ACTIVITY"
                },
                "prediction": {
                    "label": "LOW_SPO2",
                    "risk_score": 0.92,
                    "confidence": 0.95
                },
                "inference_latency": 2.1
            }

            # Post edge event to backend API
            res = self.client.post("/api/edge/events", json=payload)
            self.assertEqual(res.status_code, 201)

            # Receive JSON broadcast on connected WebSocket
            ws_data = websocket.receive_json()
            
            self.assertEqual(ws_data["patient_id"], "P001")
            self.assertEqual(ws_data["vitals"]["heart_rate"], 142)
            self.assertEqual(ws_data["vitals"]["spo2"], 88)
            self.assertEqual(ws_data["prediction"]["label"], "LOW_SPO2")
            self.assertEqual(ws_data["prediction"]["risk_score"], 0.92)
            self.assertEqual(ws_data["status"], "CRITICAL")

if __name__ == "__main__":
    unittest.main()
