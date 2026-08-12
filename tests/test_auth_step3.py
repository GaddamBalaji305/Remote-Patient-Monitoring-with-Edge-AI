import unittest
import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from backend.app.security.auth import create_access_token
from scripts.seed_database import seed

class TestAuthStep3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)

    def test_01_successful_login(self):
        """Verify successful login returns a JWT access token and user info."""
        payload = {
            "email": "doctor@example.com",
            "password": "Doctor123!"
        }
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], "doctor@example.com")
        self.assertEqual(data["user"]["role"], "DOCTOR")
        TestAuthStep3.doctor_token = data["access_token"]

    def test_02_login_invalid_password(self):
        """Verify login fails with HTTP 401 for incorrect password."""
        payload = {
            "email": "doctor@example.com",
            "password": "WrongPassword999!"
        }
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("detail", data)

    def test_03_login_unknown_user(self):
        """Verify login fails with HTTP 401 for non-existent user."""
        payload = {
            "email": "nonexistent.user@example.com",
            "password": "Password123!"
        }
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 401)

    def test_04_expired_token_access(self):
        """Verify API rejects requests with an expired JWT access token."""
        expired_token = create_access_token(
            data={"sub": "doctor@example.com", "role": "DOCTOR"},
            expires_delta=datetime.timedelta(seconds=-10) # Expired 10 seconds ago
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_05_protected_endpoint_without_token(self):
        """Verify protected endpoint rejects requests lacking Bearer authorization header with HTTP 401."""
        response = self.client.get("/api/patients")
        self.assertIn(response.status_code, [401, 403])

    def test_06_role_authorization_permissions(self):
        """Verify RBAC permissions for Admin, Doctor, and Caregiver roles."""
        # 1. Obtain tokens for Admin & Caregiver
        admin_login = self.client.post("/api/auth/login", json={"email": "admin@example.com", "password": "Admin123!"})
        self.assertEqual(admin_login.status_code, 200)
        admin_token = admin_login.json()["access_token"]

        caregiver_login = self.client.post("/api/auth/login", json={"email": "caregiver@example.com", "password": "Caregiver123!"})
        self.assertEqual(caregiver_login.status_code, 200)
        caregiver_token = caregiver_login.json()["access_token"]

        doctor_token = getattr(TestAuthStep3, "doctor_token")

        # 2. Caregiver attempts to create patient -> HTTP 403 Forbidden
        patient_payload = {
            "patient_code": "AUTH-PAT-01",
            "name": "Auth Patient Test",
            "age": 50,
            "gender": "Male",
            "status": "NORMAL"
        }
        res_caregiver_create = self.client.post("/api/patients", json=patient_payload, headers={"Authorization": f"Bearer {caregiver_token}"})
        self.assertEqual(res_caregiver_create.status_code, 403)

        # 3. Doctor creates patient -> HTTP 201 Created
        res_doctor_create = self.client.post("/api/patients", json=patient_payload, headers={"Authorization": f"Bearer {doctor_token}"})
        self.assertEqual(res_doctor_create.status_code, 201)
        created_pid = res_doctor_create.json()["id"]

        # 4. Doctor attempts to delete patient -> HTTP 403 Forbidden (Admin only)
        res_doctor_delete = self.client.delete(f"/api/patients/{created_pid}", headers={"Authorization": f"Bearer {doctor_token}"})
        self.assertEqual(res_doctor_delete.status_code, 403)

        # 5. Admin deletes patient -> HTTP 200 OK
        res_admin_delete = self.client.delete(f"/api/patients/{created_pid}", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_admin_delete.status_code, 200)

if __name__ == "__main__":
    unittest.main()
