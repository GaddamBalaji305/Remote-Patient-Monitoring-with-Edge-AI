import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal, init_db
from backend.app import models
from backend.app.services.alert_service import alert_service
from scripts.seed_database import seed
from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.inference.predictor import EdgePredictor
from edge_ai.inference.risk_engine import RiskEngine

class TestIntegrationStep7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)
        cls.predictor = EdgePredictor(model_path="edge_ai/models/edge_random_forest.joblib")
        cls.risk_engine = RiskEngine()

    def setUp(self):
        alert_service.reset_cooldown()

    def test_01_backend_edge_events_endpoint_ingestion(self):
        """Verify POST /api/edge/events ingests normal telemetry, creates DB records, and updates status."""
        payload = {
            "patient_id": "P001",
            "timestamp": "2026-08-12T17:20:43Z",
            "vitals": {
                "heart_rate": 74.0,
                "spo2": 98.0,
                "temperature": 36.8,
                "respiratory_rate": 16.0,
                "systolic_bp": 120.0,
                "diastolic_bp": 80.0,
                "activity_level": "RESTING"
            },
            "prediction": {
                "label": "NORMAL",
                "risk_score": 0.05,
                "confidence": 0.96
            },
            "inference_latency": 2.5
        }

        response = self.client.post("/api/edge/events", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("vital_reading_id", data)
        self.assertIn("prediction_id", data)
        self.assertFalse(data["alert_created"])
        self.assertEqual(data["patient_status"], "NORMAL")

        # Verify DB records
        db = SessionLocal()
        try:
            vital = db.query(models.VitalReading).filter(models.VitalReading.id == data["vital_reading_id"]).first()
            self.assertIsNotNone(vital)
            self.assertEqual(vital.heart_rate, 74.0)

            pred = db.query(models.AIPrediction).filter(models.AIPrediction.id == data["prediction_id"]).first()
            self.assertIsNotNone(pred)
            self.assertEqual(pred.prediction, "NORMAL")
        finally:
            db.close()

    def test_02_backend_edge_events_critical_alert_generation(self):
        """Verify POST /api/edge/events with LOW_SPO2 desaturation generates a CRITICAL alert and updates patient status."""
        payload = {
            "patient_id": "P099",
            "timestamp": "2026-08-12T17:20:43Z",
            "vitals": {
                "heart_rate": 135.0,
                "spo2": 85.0, # Hypoxia
                "temperature": 37.2,
                "respiratory_rate": 26.0,
                "systolic_bp": 145.0,
                "diastolic_bp": 92.0,
                "activity_level": "RESTING"
            },
            "prediction": {
                "label": "LOW_SPO2",
                "risk_score": 0.94,
                "confidence": 0.96
            },
            "inference_latency": 1.8
        }

        response = self.client.post("/api/edge/events", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["alert_created"])
        self.assertIsNotNone(data["alert_id"])
        self.assertEqual(data["patient_status"], "CRITICAL")

        # Verify alert created in DB
        db = SessionLocal()
        try:
            alert = db.query(models.Alert).filter(models.Alert.id == data["alert_id"]).first()
            self.assertIsNotNone(alert)
            self.assertEqual(alert.severity, "CRITICAL")
            self.assertEqual(alert.alert_type, "LOW_SPO2_HYPOXIA")
        finally:
            db.close()

    def test_03_end_to_end_edge_pipeline_execution(self):
        """Verify full pipeline: Sensor Simulator -> Edge Preprocessing -> Edge AI -> Risk Engine -> Backend Ingestion API."""
        sim = PhysiologicalSensorSimulator(patient_id="P002", scenario="LOW_SPO2")
        
        # Run 5 steps of the simulator
        for _ in range(5):
            sensor_event = sim.generate_sample()
            pred_res = self.predictor.predict(sensor_event)
            risk_res = self.risk_engine.evaluate_risk(pred_res)

            payload = {
                "patient_id": "P002",
                "timestamp": sensor_event["timestamp"],
                "vitals": {
                    "heart_rate": sensor_event["heart_rate"],
                    "spo2": sensor_event["spo2"],
                    "temperature": sensor_event["temperature"],
                    "respiratory_rate": sensor_event["respiratory_rate"],
                    "systolic_bp": sensor_event["systolic_bp"],
                    "diastolic_bp": sensor_event["diastolic_bp"],
                    "activity_level": sensor_event["activity_level"]
                },
                "prediction": {
                    "label": pred_res["prediction"],
                    "risk_score": pred_res["risk_score"],
                    "confidence": pred_res["confidence"]
                },
                "inference_latency": pred_res["inference_latency_ms"]
            }

            res = self.client.post("/api/edge/events", json=payload)
            self.assertEqual(res.status_code, 201)
            self.assertEqual(res.json()["status"], "success")

if __name__ == "__main__":
    unittest.main()
