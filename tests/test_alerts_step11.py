import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db, get_db
from backend.app.services.alert_service import AlertService
from backend.app import models
from scripts.seed_database import seed

class TestAlertsStep11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)
        login_res = cls.client.post("/api/auth/login", json={"email": "doctor@example.com", "password": "Doctor123!"})
        cls.headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    def test_01_alert_service_evaluation_and_thresholds(self):
        """Verify AlertService generates CRITICAL alerts for low SpO2 and high risk scores."""
        db = next(get_db())
        patient = db.query(models.Patient).filter(models.Patient.id == 1).first()
        
        # Instantiate test service instance
        service = AlertService(cooldown_seconds=1)

        vitals = {
            "heart_rate": 142.0,
            "spo2": 87.0,
            "temperature": 38.9,
            "respiratory_rate": 24.0,
            "activity_level": "RESTING"
        }
        prediction = {
            "prediction": "CRITICAL",
            "risk_score": 0.94,
            "confidence": 0.96
        }

        alert = service.evaluate_telemetry(db=db, patient=patient, vitals=vitals, prediction=prediction)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "CRITICAL")
        self.assertEqual(alert.alert_type, "LOW_SPO2_HYPOXIA")
        self.assertIn("SpO₂: 87.0%", alert.message)
        self.assertIn("Risk Score: 0.94", alert.message)

    def test_02_alert_service_cooldown_anti_spam(self):
        """Verify identical alerts within the cooldown window are suppressed to prevent spam."""
        db = next(get_db())
        patient = db.query(models.Patient).filter(models.Patient.id == 2).first()
        
        service = AlertService(cooldown_seconds=60)
        vitals = {"heart_rate": 145.0, "spo2": 86.0, "temperature": 37.0, "respiratory_rate": 20.0}
        prediction = {"prediction": "LOW_SPO2", "risk_score": 0.90, "confidence": 0.95}

        # First evaluation generates alert
        alert1 = service.evaluate_telemetry(db=db, patient=patient, vitals=vitals, prediction=prediction)
        self.assertIsNotNone(alert1)

        # Immediate second evaluation should be suppressed by cooldown
        alert2 = service.evaluate_telemetry(db=db, patient=patient, vitals=vitals, prediction=prediction)
        self.assertIsNone(alert2)

    def test_03_edge_event_alert_generation(self):
        """Verify POST /api/edge/events invokes Alert Engine and creates an Alert."""
        payload = {
            "patient_id": "P001",
            "timestamp": "2026-08-12T12:00:00Z",
            "vitals": {
                "heart_rate": 140,
                "spo2": 88,
                "temperature": 38.9,
                "respiratory_rate": 24,
                "systolic_bp": 145,
                "diastolic_bp": 95,
                "activity_level": "RESTING"
            },
            "prediction": {
                "label": "CRITICAL",
                "risk_score": 0.94,
                "confidence": 0.96
            },
            "inference_latency": 1.85
        }

        res = self.client.post("/api/edge/events", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["alert_created"])
        self.assertIsNotNone(data["alert_id"])

    def test_04_acknowledge_alert_endpoint(self):
        """Verify PUT /api/alerts/{id}/acknowledge updates DB status immediately."""
        # Fetch active alerts
        get_res = self.client.get("/api/alerts?status=ACTIVE")
        self.assertEqual(get_res.status_code, 200)
        alerts = get_res.json()
        self.assertGreater(len(alerts), 0)

        alert_id = alerts[0]["id"]
        ack_res = self.client.put(f"/api/alerts/{alert_id}/acknowledge", json={"acknowledged_by": "Dr. House"})
        self.assertEqual(ack_res.status_code, 200)
        ack_data = ack_res.json()
        
        self.assertEqual(ack_data["status"], "ACKNOWLEDGED")
        self.assertEqual(ack_data["acknowledged_by"], "Dr. House")
        self.assertIsNotNone(ack_data["acknowledged_at"])

if __name__ == "__main__":
    unittest.main()
