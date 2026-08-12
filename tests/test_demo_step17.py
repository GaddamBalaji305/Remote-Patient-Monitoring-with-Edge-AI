import unittest
import time
import os
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from scripts.seed_database import seed

class TestDemoStep17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)

    def test_01_demo_controller_lifecycle(self):
        """Test POST /api/demo/start, GET /api/demo/status, and POST /api/demo/stop."""
        # 1. Start Demo Simulation
        start_payload = {
            "patient_id": "P001",
            "scenario": "LOW_SPO2",
            "interval_seconds": 0.5,
            "max_steps": 5
        }
        start_res = self.client.post("/api/demo/start", json=start_payload)
        self.assertEqual(start_res.status_code, 200)
        self.assertEqual(start_res.json()["status"], "success")

        # 2. Check Demo Status
        time.sleep(0.2)
        status_res = self.client.get("/api/demo/status")
        self.assertEqual(status_res.status_code, 200)
        st = status_res.json()
        self.assertEqual(st["patient_id"], "P001")
        self.assertEqual(st["scenario"], "LOW_SPO2")

        # Wait for loop to generate at least 1 sample
        time.sleep(1.0)

        # 3. Stop Demo Simulation
        stop_res = self.client.post("/api/demo/stop")
        self.assertEqual(stop_res.status_code, 200)
        self.assertEqual(stop_res.json()["status"], "success")

        time.sleep(0.2)
        final_status = self.client.get("/api/demo/status").json()
        self.assertFalse(final_status["active"])

    def test_03_all_scenarios_supported(self):
        """Test starting simulation for all 7 required scenarios: NORMAL, TACHYCARDIA, BRADYCARDIA, LOW_SPO2, FEVER, FALL, CRITICAL."""
        scenarios = ["NORMAL", "TACHYCARDIA", "BRADYCARDIA", "LOW_SPO2", "FEVER", "FALL", "CRITICAL"]
        for sc in scenarios:
            payload = {
                "patient_id": "P002",
                "scenario": sc,
                "interval_seconds": 0.5,
                "duration_seconds": 10.0
            }
            res = self.client.post("/api/demo/start", json=payload)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["status"], "success")
            
            st = self.client.get("/api/demo/status").json()
            self.assertEqual(st["scenario"], sc)
            self.assertEqual(st["duration_seconds"], 10.0)
            
            stop_res = self.client.post("/api/demo/stop")
            self.assertEqual(stop_res.status_code, 200)
            time.sleep(0.2)

if __name__ == "__main__":
    unittest.main()
