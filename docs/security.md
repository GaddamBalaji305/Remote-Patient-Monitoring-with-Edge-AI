# Security Architecture & Hardening Documentation

This document outlines the security controls, authentication architecture, authorization matrix, audit logging mechanisms, and environment safeguards implemented in the **Remote Patient Monitoring with Edge AI** platform.

---

## 1. Synthetic Data & Compliance Notice

> [!IMPORTANT]
> **Synthetic Data Statement**: This repository and platform operate **exclusively on synthetic physiological patient data** generated for development, testing, and clinical demonstration purposes. No actual Protected Health Information (PHI) or real patient medical records are used or stored.

> [!NOTE]
> **Regulatory Readiness Statement**: The architectural design incorporates technical safeguards aligned with **HIPAA Security Rule** and **GDPR** principles (role-based access control, cryptographic password hashing, JWT authentication, audit logging, and local data isolation). Formal regulatory certification requires deployment-specific hardware, network encryption, and independent compliance auditing.

---

## 2. Authentication Architecture

The platform uses a stateless **JSON Web Token (JWT)** Bearer authentication mechanism combined with secure password hashing.

```text
Client Login Request ──► bcrypt Password Check ──► Generate Signed JWT ──► HTTP Bearer Authorization
(POST /api/auth/login)     (bcrypt.checkpw)        (HS256 Signature)      (Authorization: Bearer <token>)
```

### Key Specifications
- **Algorithm**: `HS256` (HMAC with SHA-256)
- **Token Expiration**: Configurable (default 30 minutes)
- **Token Payload Claims**:
  - `sub`: User Email (`doctor@example.com`)
  - `role`: User Role (`ADMIN`, `DOCTOR`, `CAREGIVER`)
  - `id`: User Database ID
- **Password Hashing**: Direct `bcrypt` algorithm (`bcrypt.hashpw` with random salt and work factor 12). Plaintext passwords are never logged, stored, or exposed.

---

## 3. Role-Based Access Control (RBAC) Matrix

Permissions are strictly enforced via FastAPI dependency injection (`require_roles([...])`).

| Feature / API Endpoint | HTTP Method | `ADMIN` | `DOCTOR` | `CAREGIVER` |
| :--- | :--- | :---: | :---: | :---: |
| **Authenticate / Login** | `POST /api/auth/login` | ✅ | ✅ | ✅ |
| **View Current User Profile** | `GET /api/auth/me` | ✅ | ✅ | ✅ |
| **List Patients** | `GET /api/patients` | ✅ | ✅ | ✅ |
| **View Patient Details** | `GET /api/patients/{id}` | ✅ | ✅ | ✅ |
| **Create New Patient** | `POST /api/patients` | ✅ | ✅ | ❌ (403 Forbidden) |
| **Update Patient Profile** | `PUT /api/patients/{id}` | ✅ | ✅ | ❌ (403 Forbidden) |
| **Delete Patient Record** | `DELETE /api/patients/{id}` | ✅ | ❌ (403 Forbidden) | ❌ (403 Forbidden) |
| **View Telemetry Vitals** | `GET /api/patients/{id}/vitals` | ✅ | ✅ | ✅ |
| **View AI Predictions** | `GET /api/patients/{id}/predictions` | ✅ | ✅ | ❌ (403 Forbidden) |
| **View Alerts & Triage** | `GET /api/alerts` | ✅ | ✅ | ✅ |
| **Acknowledge Alert** | `PUT /api/alerts/{id}/acknowledge` | ✅ | ✅ | ✅ |
| **Ingest Edge Event** | `POST /api/edge/events` | ✅ (Edge Node) | ✅ | ✅ |

---

## 4. Security Controls & Defensive Features

### A. Input Validation & Schema Sanitization
- All incoming REST payloads undergo strict **Pydantic v2** validation.
- Field validators enforce ranges:
  - `age`: Must be between `0` and `150`.
  - `gender`: Sanitized to `'Male'`, `'Female'`, or `'Other'`.
  - `patient_code`: Strip whitespace and uppercase formatting (e.g. `'P001'`).
  - Vital parameters: Bounded numeric floating-point inputs.

### B. SQL Injection Defense
- Built entirely on **SQLAlchemy ORM** parameterized queries.
- Raw string concatenation in SQL queries is strictly prohibited.

### C. Login Brute-Force Rate Limiting
- Custom FastAPI middleware (`LoginRateLimitingMiddleware`) protects `POST /api/auth/login`.
- Rate Limit: Default **10 requests per minute** per client IP address.
- Exceeding the limit triggers `HTTP 429 Too Many Requests`.

### D. Security Audit Logging
- Immutable security audit records are saved to the `audit_logs` database table via `AuditLogger`.
- Events Audited:
  - `USER_LOGIN_SUCCESS` / `USER_LOGIN_FAILED`
  - `PATIENT_CREATED` / `PATIENT_UPDATED` / `PATIENT_DELETED`
  - `ALERT_ACKNOWLEDGED`

### E. CORS Configuration
- Configurable Cross-Origin Resource Sharing policy (`CORS_ORIGINS`).
- Production settings can restrict allowed origins to trusted domain names.

---

## 5. Environment Variables & Secret Key Management

Secrets are loaded via `backend/app/config.py` from environment variables:

```env
# .env Configuration Example
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOGIN_RATE_LIMIT_PER_MINUTE=10
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

> [!CAUTION]
> In production deployments, set a unique 256-bit cryptographically random `SECRET_KEY` generated via `openssl rand -hex 32`. Never commit production secrets to Git repositories.
