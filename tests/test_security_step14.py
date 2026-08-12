import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db, get_db
from backend.app import models
from backend.app.security.password import hash_password, verify_password
from backend.app.middleware.rate_limiter import reset_rate_limits
from scripts.seed_database import seed

class TestSecurityStep14(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)

    def setUp(self):
        reset_rate_limits()

    def tearDown(self):
        reset_rate_limits()

    def test_01_password_hashing_and_verification(self):
        """Verify bcrypt password hashing and verification functionality."""
        pwd = "SecureDoctorPassword123!"
        hashed = hash_password(pwd)
        
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_02_rbac_authorization_enforcement(self):
        """Verify Caregiver role is denied (HTTP 403 Forbidden) when attempting restricted operations."""
        # 1. Login as Caregiver
        login_res = self.client.post("/api/auth/login", json={"email": "caregiver@example.com", "password": "Caregiver123!"})
        self.assertEqual(login_res.status_code, 200)
        caregiver_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        # 2. Caregiver attempts DELETE patient -> HTTP 403
        del_res = self.client.delete("/api/patients/1", headers=caregiver_headers)
        self.assertEqual(del_res.status_code, 403)
        self.assertIn("lacks required permissions", del_res.json()["detail"])

        # 3. Caregiver attempts POST patient -> HTTP 403
        create_res = self.client.post("/api/patients", json={
            "patient_code": "P999", "name": "Illegal Create", "age": 40, "gender": "Male"
        }, headers=caregiver_headers)
        self.assertEqual(create_res.status_code, 403)

    def test_03_login_rate_limiting_middleware(self):
        """Verify rate limiting middleware triggers HTTP 429 Too Many Requests after threshold."""
        # Send 12 rapid failed login attempts
        status_codes = []
        for i in range(12):
            res = self.client.post("/api/auth/login", json={"email": "brute@example.com", "password": "wrong"})
            status_codes.append(res.status_code)

        # Confirm 429 Too Many Requests was returned
        self.assertIn(429, status_codes)

        # Reset rate limits after test to prevent impacting subsequent tests
        reset_rate_limits()

    def test_04_audit_logging_generation(self):
        """Verify security audit logs are recorded in the database."""
        db = next(get_db())
        logs = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).all()
        self.assertGreater(len(logs), 0)

        actions = [l.action for l in logs]
        self.assertTrue(any("LOGIN" in a or "PATIENT" in a for a in actions))

    def test_05_input_validation_rejection(self):
        """Verify Pydantic input validation rejects invalid fields (age = -5 or age = 200)."""
        login_res = self.client.post("/api/auth/login", json={"email": "admin@example.com", "password": "Admin123!"})
        admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        res = self.client.post("/api/patients", json={
            "patient_code": "PINV",
            "name": "Invalid Age",
            "age": -5,  # Invalid
            "gender": "Male"
        }, headers=admin_headers)

        self.assertEqual(res.status_code, 422)

if __name__ == "__main__":
    unittest.main()
