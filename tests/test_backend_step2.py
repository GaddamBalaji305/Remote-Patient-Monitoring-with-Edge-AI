import unittest
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.app.main import app
from backend.app.database import SessionLocal, init_db
from scripts.seed_database import seed

class TestBackendStep2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)
        
        # Authenticate as Admin for Step 2 CRUD tests
        login_res = cls.client.post("/api/auth/login", json={"email": "admin@example.com", "password": "Admin123!"})
        cls.headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    def test_01_database_connection(self):
        """Verify database engine connection."""
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1")).scalar()
            self.assertEqual(result, 1)
        finally:
            db.close()

    def test_02_health_endpoint(self):
        """Verify GET /api/health endpoint."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "Online")
        self.assertEqual(data["database"], "Healthy")

    def test_03_patient_creation(self):
        """Verify POST /api/patients (Patient Creation)."""
        payload = {
            "patient_code": "TEST-PAT-99",
            "name": "Test Subject Alpha",
            "age": 45,
            "gender": "Male",
            "phone": "+1-555-9999",
            "emergency_contact": "+1-555-8888",
            "room": "Test Room 101",
            "status": "NORMAL"
        }
        response = self.client.post("/api/patients", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["patient_code"], "TEST-PAT-99")
        self.assertIn("id", data)
        TestBackendStep2.created_patient_id = data["id"]

    def test_04_patient_retrieval(self):
        """Verify GET /api/patients/{id} (Patient Retrieval)."""
        patient_id = getattr(TestBackendStep2, "created_patient_id", 1)
        response = self.client.get(f"/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], patient_id)

    def test_05_patient_update(self):
        """Verify PUT /api/patients/{id} (Patient Update)."""
        patient_id = getattr(TestBackendStep2, "created_patient_id", 1)
        payload = {
            "room": "Updated ICU 99",
            "status": "WARNING"
        }
        response = self.client.put(f"/api/patients/{patient_id}", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["room"], "Updated ICU 99")
        self.assertEqual(data["status"], "WARNING")

    def test_06_vital_reading_creation(self):
        """Verify POST /api/vitals (Vital Reading Creation)."""
        patient_id = getattr(TestBackendStep2, "created_patient_id", 1)
        payload = {
            "patient_id": patient_id,
            "heart_rate": 88.5,
            "spo2": 97.0,
            "temperature": 36.9,
            "respiratory_rate": 18.0,
            "systolic_bp": 125.0,
            "diastolic_bp": 82.0,
            "activity_level": "Resting"
        }
        response = self.client.post("/api/vitals", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["patient_id"], patient_id)
        self.assertEqual(data["heart_rate"], 88.5)

    def test_07_alert_creation(self):
        """Verify POST /api/alerts (Alert Creation)."""
        patient_id = getattr(TestBackendStep2, "created_patient_id", 1)
        payload = {
            "patient_id": patient_id,
            "severity": "WARNING",
            "alert_type": "Elevated Heart Rate",
            "message": "Heart rate exceeded baseline threshold during test run.",
            "status": "ACTIVE"
        }
        response = self.client.post("/api/alerts", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["patient_id"], patient_id)
        self.assertEqual(data["severity"], "WARNING")
        TestBackendStep2.created_alert_id = data["id"]

    def test_08_alert_acknowledgment(self):
        """Verify PUT /api/alerts/{id}/acknowledge (Alert Acknowledgment)."""
        alert_id = getattr(TestBackendStep2, "created_alert_id", 1)
        payload = {"acknowledged_by": "Dr. Tester"}
        response = self.client.put(f"/api/alerts/{alert_id}/acknowledge", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ACKNOWLEDGED")
        self.assertEqual(data["acknowledged_by"], "Dr. Tester")

    def test_09_patient_deletion(self):
        """Verify DELETE /api/patients/{id} (Patient Deletion)."""
        patient_id = getattr(TestBackendStep2, "created_patient_id", 1)
        response = self.client.delete(f"/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # Confirm 404 on subsequent get
        get_res = self.client.get(f"/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(get_res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
