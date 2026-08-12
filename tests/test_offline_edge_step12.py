import unittest
import os
import tempfile
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db, get_db
from backend.app import models
from scripts.seed_database import seed
from edge_ai.offline_queue import OfflineQueue
from edge_ai.run import post_event_to_backend, flush_offline_queue

class TestOfflineEdgeStep12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)
        cls.backend_url = "http://testserver/api/edge/events"

    def setUp(self):
        # Create a temporary SQLite database for offline queue testing
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_queue.db")
        self.queue = OfflineQueue(db_path=self.db_path)
        self.queue.clear_queue()

    def test_01_offline_queue_enqueue_and_pending(self):
        """Verify OfflineQueue enqueues events and retrieves pending items in order."""
        vitals = {"heart_rate": 82.0, "spo2": 97.0, "temperature": 36.8, "respiratory_rate": 16.0}
        prediction = {"label": "NORMAL", "risk_score": 0.05, "confidence": 0.95}

        id1 = self.queue.enqueue("P001", "2026-08-12T12:00:00Z", vitals, prediction, 1.8)
        id2 = self.queue.enqueue("P002", "2026-08-12T12:01:00Z", vitals, prediction, 2.1)

        self.assertEqual(self.queue.get_queue_count(), 2)

        pending = self.queue.get_pending_events()
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]["id"], id1)
        self.assertEqual(pending[0]["patient_id"], "P001")
        self.assertEqual(pending[1]["id"], id2)
        self.assertEqual(pending[1]["patient_id"], "P002")

    def test_02_offline_queue_mark_synced(self):
        """Verify mark_synced purges processed events from local SQLite database."""
        vitals = {"heart_rate": 90.0, "spo2": 98.0, "temperature": 37.0, "respiratory_rate": 18.0}
        prediction = {"label": "NORMAL", "risk_score": 0.08, "confidence": 0.94}

        ev_id = self.queue.enqueue("P003", "2026-08-12T12:02:00Z", vitals, prediction, 1.5)
        self.assertEqual(self.queue.get_queue_count(), 1)

        self.queue.mark_synced(ev_id)
        self.assertEqual(self.queue.get_queue_count(), 0)

    def test_03_store_and_forward_sync_flow(self):
        """
        Simulate full Offline-First lifecycle:
        1. Backend online -> Direct ingestion.
        2. Backend outage -> Edge AI stores events in SQLite OfflineQueue.
        3. Backend restored -> Reconnection flushes and synchronizes queue without data loss.
        """
        # 1. Enqueue 3 events locally (simulating offline backend outage)
        for i in range(3):
            self.queue.enqueue(
                patient_id=f"P10{i}",
                timestamp=f"2026-08-12T12:10:0{i}Z",
                vitals={"heart_rate": 75.0 + i, "spo2": 98.0, "temperature": 36.8, "respiratory_rate": 16.0},
                prediction={"label": "NORMAL", "risk_score": 0.05, "confidence": 0.95},
                inference_latency=1.75
            )

        self.assertEqual(self.queue.get_queue_count(), 3)

        # 2. Simulate Backend Restored -> Synchronize offline queue via TestClient
        pending = self.queue.get_pending_events()
        synced_count = 0
        for ev in pending:
            payload = {
                "patient_id": ev["patient_id"],
                "timestamp": ev["timestamp"],
                "vitals": ev["vitals"],
                "prediction": ev["prediction"],
                "inference_latency": ev["inference_latency"]
            }
            res = self.client.post("/api/edge/events", json=payload)
            self.assertEqual(res.status_code, 201)
            self.queue.mark_synced(ev["id"])
            synced_count += 1

        self.assertEqual(synced_count, 3)
        self.assertEqual(self.queue.get_queue_count(), 0)

        # 3. Verify synchronized events exist in backend database
        db = next(get_db())
        p0 = db.query(models.Patient).filter(models.Patient.patient_code == "P100").first()
        self.assertIsNotNone(p0)

if __name__ == "__main__":
    unittest.main()
