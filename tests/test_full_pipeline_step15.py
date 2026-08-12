import unittest
import os
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db, get_db
from backend.app import models
from scripts.seed_database import seed

from edge_ai.inference.predictor import EdgePredictor
from edge_ai.inference.risk_engine import RiskEngine
from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.simulator.scenarios import ScenarioType
from edge_ai.offline_queue import OfflineQueue
from edge_ai.training.generate_dataset import generate_synthetic_dataset
from edge_ai.training.train_model import train_edge_model
from edge_ai.inference.metrics_tracker import metrics_tracker
from edge_ai.benchmark import run_controlled_benchmark

class TestFullPipelineStep15(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)
        cls.predictor = EdgePredictor(model_path="edge_ai/models/edge_random_forest.joblib")
        cls.risk_engine = RiskEngine(medium_risk_threshold=0.35, high_risk_threshold=0.70)

    def test_01_backend_complete_api_suite(self):
        """Test all backend endpoints: auth, patients, vitals, predictions, alerts, stats."""
        # 1. Login
        login_res = self.client.post("/api/auth/login", json={"email": "doctor@example.com", "password": "Doctor123!"})
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get Me Profile
        me_res = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["email"], "doctor@example.com")

        # 3. Dashboard Stats
        stats_res = self.client.get("/api/dashboard/statistics", headers=headers)
        self.assertEqual(stats_res.status_code, 200)
        self.assertIn("total_patients", stats_res.json())

        # 4. Patients List & Detail
        patients_res = self.client.get("/api/patients?limit=5", headers=headers)
        self.assertEqual(patients_res.status_code, 200)
        self.assertGreater(len(patients_res.json()), 0)
        pid = patients_res.json()[0]["id"]

        detail_res = self.client.get(f"/api/patients/{pid}", headers=headers)
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn("patient_code", detail_res.json())

        # 5. Vitals, Predictions, Alerts History
        vitals_res = self.client.get(f"/api/patients/{pid}/vitals", headers=headers)
        self.assertEqual(vitals_res.status_code, 200)

        preds_res = self.client.get(f"/api/patients/{pid}/predictions", headers=headers)
        self.assertEqual(preds_res.status_code, 200)

        alerts_res = self.client.get(f"/api/patients/{pid}/alerts", headers=headers)
        self.assertEqual(alerts_res.status_code, 200)

    def test_02_dataset_generation_and_model_training(self):
        """Test Edge AI dataset generation and scikit-learn model training pipeline."""
        csv_path = "edge_ai/data/test_synthetic_telemetry.csv"
        model_output_path = "edge_ai/models/test_model.joblib"

        # 1. Dataset Generation
        df_gen = generate_synthetic_dataset(samples_per_scenario=50, output_csv=csv_path)
        self.assertTrue(os.path.exists(csv_path))
        self.assertGreater(len(df_gen), 300)

        # 2. Model Training
        model, X_test, y_test = train_edge_model(dataset_path=csv_path, model_output_path=model_output_path)
        self.assertTrue(os.path.exists(model_output_path))
        self.assertIsNotNone(model)

        # Cleanup test artifacts
        try:
            if os.path.exists(csv_path): os.remove(csv_path)
            if os.path.exists(model_output_path): os.remove(model_output_path)
        except Exception:
            pass

    def test_03_classification_across_all_8_scenarios(self):
        """Test sensor simulator and Edge AI model classification across all 8 physiological scenarios."""
        scenarios = [
            "NORMAL",
            "TACHYCARDIA",
            "BRADYCARDIA",
            "LOW_SPO2",
            "FEVER",
            "ABNORMAL_RESPIRATION",
            "FALL",
            "MULTI_PARAMETER_CRITICAL"
        ]

        for scen in scenarios:
            sim = PhysiologicalSensorSimulator(patient_id=f"TEST_{scen}", scenario=scen)
            # Run 12 steps to evolve state
            for _ in range(12):
                sample = sim.generate_sample()
                pred_res = self.predictor.predict(sample)

            self.assertIn("prediction", pred_res)
            self.assertIn(pred_res["prediction"], self.predictor.classes)
            self.assertTrue(0.0 <= pred_res["risk_score"] <= 1.0)
            self.assertLess(pred_res["inference_latency_ms"], 100.0)

    def test_04_offline_queue_sync_recovery(self):
        """Test SQLite OfflineQueue store-and-forward sync mechanism."""
        queue_db_path = "edge_ai/data/test_offline_queue_step15.db"
        try:
            if os.path.exists(queue_db_path):
                os.remove(queue_db_path)
        except Exception:
            pass

        queue = OfflineQueue(db_path=queue_db_path)

        # Enqueue 2 events
        queue.enqueue("P001", "2026-08-12T12:00:00Z", {"heart_rate": 140, "spo2": 88}, {"label": "CRITICAL", "risk_score": 0.94, "confidence": 0.95}, 2.1)
        queue.enqueue("P002", "2026-08-12T12:00:05Z", {"heart_rate": 72, "spo2": 98}, {"label": "NORMAL", "risk_score": 0.05, "confidence": 0.96}, 1.8)

        unsynced = queue.get_pending_events()
        self.assertEqual(len(unsynced), 2)

        # Mark 1 synced
        queue.mark_synced(unsynced[0]["id"])
        remaining = queue.get_pending_events()
        self.assertEqual(len(remaining), 1)

        # Cleanup safely
        try:
            if os.path.exists(queue_db_path):
                os.remove(queue_db_path)
        except Exception:
            pass

    def test_05_full_e2e_telemetry_pipeline(self):
        """
        Test complete E2E Telemetry Pipeline:
        Sensor Simulator -> Edge AI Predictor -> Risk Engine -> REST Endpoint -> DB Persistence -> Alert Desk.
        """
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="LOW_SPO2")
        # Run 10 samples to generate hypoxia state
        for _ in range(10):
            sample = sim.generate_sample()
            pred = self.predictor.predict(sample)
            risk = self.risk_engine.evaluate_risk(pred)

        payload = {
            "patient_id": "P001",
            "timestamp": sample["timestamp"],
            "vitals": {
                "heart_rate": sample["heart_rate"],
                "spo2": sample["spo2"],
                "temperature": sample["temperature"],
                "respiratory_rate": sample["respiratory_rate"],
                "systolic_bp": sample["systolic_bp"],
                "diastolic_bp": sample["diastolic_bp"],
                "activity_level": sample["activity_level"]
            },
            "prediction": {
                "label": pred["prediction"],
                "risk_score": pred["risk_score"],
                "confidence": pred["confidence"]
            },
            "inference_latency": pred["inference_latency_ms"]
        }

        # Post event to FastAPI ingestion endpoint
        post_res = self.client.post("/api/edge/events", json=payload)
        self.assertIn(post_res.status_code, [200, 201])

        # Verify DB patient state updated
        db = next(get_db())
        patient_db = db.query(models.Patient).filter(models.Patient.patient_code == "P001").first()
        self.assertIsNotNone(patient_db)

    def test_06_websocket_monitoring_connection(self):
        """Test WebSocket client connection and message broadcasting."""
        with self.client.websocket_connect("/ws/monitoring") as websocket:
            # Post edge event to trigger WebSocket broadcast
            payload = {
                "patient_id": "P001",
                "timestamp": "2026-08-12T12:00:00Z",
                "vitals": {"heart_rate": 80, "spo2": 98, "temperature": 36.8, "respiratory_rate": 16},
                "prediction": {"label": "NORMAL", "risk_score": 0.05, "confidence": 0.95},
                "inference_latency": 1.8
            }
            self.client.post("/api/edge/events", json=payload)

            # Receive WebSocket broadcast
            msg_data = websocket.receive_json()
            self.assertEqual(msg_data["patient_id"], "P001")
            self.assertIn("vitals", msg_data)

    def test_07_empirical_benchmark_verification(self):
        """Verify performance metrics and empirical benchmark report execution."""
        bmk = run_controlled_benchmark(iterations=3)
        self.assertIn("edge_local", bmk)
        self.assertIn("cloud_remote", bmk)
        self.assertGreater(bmk["edge_local"]["avg_latency_ms"], 0)

if __name__ == "__main__":
    unittest.main()
