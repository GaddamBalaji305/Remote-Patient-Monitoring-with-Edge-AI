import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from scripts.seed_database import seed

class TestPatientPageStep10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)

        # Authenticate as Doctor
        login_res = cls.client.post("/api/auth/login", json={"email": "doctor@example.com", "password": "Doctor123!"})
        cls.headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    def test_01_patient_profile_and_status_detail(self):
        """Verify GET /api/patients/{id} returns profile info, room, emergency contact, and status."""
        response = self.client.get("/api/patients/1", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["id"], 1)
        self.assertIn("name", data)
        self.assertIn("patient_code", data)
        self.assertIn("age", data)
        self.assertIn("gender", data)
        self.assertIn("room", data)
        self.assertIn("emergency_contact", data)
        self.assertIn("status", data)
        self.assertIn("latest_vitals", data)
        self.assertIn("latest_prediction", data)

    def test_02_patient_vitals_history_charting_endpoint(self):
        """Verify GET /api/patients/{id}/vitals returns time-series vitals history for Recharts."""
        response = self.client.get("/api/patients/1/vitals?limit=100", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        vitals = response.json()
        
        self.assertIsInstance(vitals, list)
        if len(vitals) > 0:
            first = vitals[0]
            self.assertIn("heart_rate", first)
            self.assertIn("spo2", first)
            self.assertIn("temperature", first)
            self.assertIn("respiratory_rate", first)
            self.assertIn("systolic_bp", first)
            self.assertIn("diastolic_bp", first)

    def test_03_patient_predictions_history_endpoint(self):
        """Verify GET /api/patients/{id}/predictions returns AI diagnostic panel data."""
        response = self.client.get("/api/patients/1/predictions", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        preds = response.json()
        
        self.assertIsInstance(preds, list)
        if len(preds) > 0:
            p = preds[0]
            self.assertIn("prediction", p)
            self.assertIn("risk_score", p)
            self.assertIn("confidence", p)
            self.assertIn("inference_latency", p)

if __name__ == "__main__":
    unittest.main()
