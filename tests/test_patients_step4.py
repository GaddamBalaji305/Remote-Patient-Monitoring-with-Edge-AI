import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from scripts.seed_database import seed

class TestPatientsStep4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)

        # Login as Doctor to obtain Authorization Bearer header
        login_res = cls.client.post("/api/auth/login", json={"email": "doctor@example.com", "password": "Doctor123!"})
        assert login_res.status_code == 200
        cls.headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    def test_01_search_patients(self):
        """Verify GET /api/patients?search=... performs case-insensitive name/code/room search."""
        response = self.client.get("/api/patients?search=eleanor", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        items = response.json()
        self.assertGreaterEqual(len(items), 1)
        self.assertIn("Eleanor", items[0]["name"])

        # Search by patient_code
        res_code = self.client.get("/api/patients?search=PAT-002", headers=self.headers)
        self.assertEqual(res_code.status_code, 200)
        self.assertEqual(res_code.json()[0]["patient_code"], "PAT-002")

    def test_02_status_filter_patients(self):
        """Verify GET /api/patients?status=CRITICAL filters patients by status."""
        response = self.client.get("/api/patients?status=CRITICAL", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        items = response.json()
        for p in items:
            self.assertEqual(p["status"], "CRITICAL")

    def test_03_pagination(self):
        """Verify GET /api/patients?skip=0&limit=2 respects pagination limits."""
        response = self.client.get("/api/patients?skip=0&limit=2", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        items = response.json()
        self.assertEqual(len(items), 2)

    def test_04_patient_detail_telemetry_summary(self):
        """Verify GET /api/patients/{id} returns profile, status, latest_vitals, latest_prediction, latest_alert, and last_updated."""
        response = self.client.get("/api/patients/1", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("status", data)
        self.assertIn("latest_vitals", data)
        self.assertIn("latest_prediction", data)
        self.assertIn("latest_alert", data)
        self.assertIn("last_updated", data)

    def test_05_dashboard_statistics(self):
        """Verify GET /api/dashboard/statistics returns exact dynamic database counts."""
        response = self.client.get("/api/dashboard/statistics", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertIn("total_patients", stats)
        self.assertIn("active_monitoring", stats)
        self.assertIn("warning", stats)
        self.assertIn("critical", stats)
        self.assertIn("offline", stats)
        self.assertGreaterEqual(stats["total_patients"], 5)
        self.assertEqual(stats["active_monitoring"], stats["total_patients"] - stats["offline"])

    def test_06_validation_invalid_age(self):
        """Verify patient creation fails with HTTP 422 when age is outside 0..150."""
        payload = {
            "patient_code": "VAL-AGE-01",
            "name": "Invalid Age Patient",
            "age": 200, # Invalid
            "gender": "Male",
            "status": "NORMAL"
        }
        response = self.client.post("/api/patients", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)

    def test_07_validation_invalid_gender(self):
        """Verify patient creation fails with HTTP 422 when gender is not Male/Female/Other."""
        payload = {
            "patient_code": "VAL-GEND-01",
            "name": "Invalid Gender Patient",
            "age": 30,
            "gender": "Alien", # Invalid
            "status": "NORMAL"
        }
        response = self.client.post("/api/patients", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)

    def test_08_duplicate_patient_code_error(self):
        """Verify patient creation fails with HTTP 400 on duplicate patient code."""
        payload = {
            "patient_code": "PAT-001", # Existing code from seed
            "name": "Duplicate Code Test",
            "age": 40,
            "gender": "Male",
            "status": "NORMAL"
        }
        response = self.client.post("/api/patients", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("already exists", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
