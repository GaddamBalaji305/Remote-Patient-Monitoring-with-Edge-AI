# Remote Patient Monitoring with Edge AI (`rpm-edge-ai`)

[![Edge AI Model](https://img.shields.io/badge/Edge%20AI-Random%20Forest%20%7C%2099.28%25%20Acc-06b6d4)](#-edge-ai-machine-learning-model)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20WebSockets-10b981)](https://fastapi.tiangolo.com/)
[![JWT Auth](https://img.shields.io/badge/Security-JWT%20%7C%20Bcrypt%20%7C%20RBAC-6366f1)](#-authentication--demo-accounts)
[![React SPA](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Canvas%20Oscilloscope-3b82f6)](https://react.dev/)
[![Tests](https://img.shields.io/badge/Tests-82%20Passing%20Tests-10b981)](#-running-tests)

A production-grade **Remote Patient Monitoring (RPM)** platform powered by **Edge AI**. The platform processes continuous multi-lead vital signs (ECG waveforms, PPG pulse streams, SpO₂, Heart Rate, Blood Pressure, Respiratory Rate, Temperature, and Motion Activity) directly on edge hardware nodes for ultra-low latency anomaly detection (<2ms edge processing), syncing summarized telemetry and critical alerts to a high-performance FastAPI backend with secure JWT authentication and Role-Based Access Control (RBAC).

---

## 🤖 Edge AI Machine Learning Model

The platform includes an optimized, lightweight **Random Forest Classifier** trained on 8,000 synthetic physiological time-series samples across **8 target classes**.

### Target Classes Classified:
1. **`NORMAL`**: Baseline healthy physiological state.
2. **`TACHYCARDIA`**: Elevated heart rate (>125 bpm).
3. **`BRADYCARDIA`**: Abnormally low heart rate (<50 bpm).
4. **`LOW_SPO2`**: Hypoxia desaturation (<90%).
5. **`FEVER`**: Pyrexia / elevated body temperature (>38.5°C).
6. **`ABNORMAL_RESPIRATION`**: Tachypnea / respiratory distress.
7. **`FALL`**: Sudden acceleration spike (`SUDDEN_FALL`) followed by immobility (`INACTIVE`).
8. **`CRITICAL`**: Multi-vital collapse (simultaneous SpO₂ drop, HR surge, BP elevation).

### Engineered Features (12 Total):
- `heart_rate`, `spo2`, `temperature`, `respiratory_rate`, `systolic_bp`, `diastolic_bp`, `activity_level` (categorical integer 0-4)
- `heart_rate_change` ($\Delta \text{HR}$), `spo2_change` ($\Delta \text{SpO2}$), `temperature_change` ($\Delta \text{Temp}$)
- `rolling_heart_rate` (5-sample moving average), `rolling_spo2` (5-sample moving average)

### Measured Evaluation Performance Metrics:
- **Overall Accuracy**: **99.28%**
- **Macro Precision**: **99.30%**
- **Macro Recall**: **99.28%**
- **Macro F1-Score**: **99.28%**
- **Inference Latency**: **<2.0 ms** per sample (~1.85 ms average).
- **Latency Advantage**: **~17.5x faster** than Cloud REST round-trip (~1.85 ms vs ~32.50 ms).

---

## 🔐 Authentication & Demo Accounts

The backend enforces **HTTP Bearer JWT Authentication** and **Role-Based Access Control (RBAC)** across all protected API routes.

| Role | Email | Password (Development Only) | Permissions |
| :--- | :--- | :--- | :--- |
| **`ADMIN`** | `admin@example.com` | `Admin123!` | Full System Access, Delete Patients, Manage Users |
| **`DOCTOR`** | `doctor@example.com` | `Doctor123!` | View/Create/Update Patients, View Vitals & Predictions, Acknowledge Alerts, Control Demo |
| **`CAREGIVER`** | `caregiver@example.com` | `Caregiver123!` | View Assigned Patients, View Vitals & Alerts, Acknowledge Alerts |

---

## 🚀 Quick Commands Guide

### 1. Installation & Setup
```bash
# Clone the repository
git clone https://github.com/user/rpm-edge-ai.git
cd rpm-edge-ai

# Create & activate Python virtual environment
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Database Seeding & Setup
```bash
# Initialize database tables and seed demo accounts, patients, & sample vitals
python scripts/seed_database.py
```

### 3. Running Backend Server
```bash
# Launch FastAPI server with Uvicorn (reloads on code changes)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000/api`
- OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 4. Accessing Frontend Dashboard
Open your browser and navigate to:
```text
http://127.0.0.1:8000
```
- Includes 60 FPS HTML5 Canvas ECG Oscilloscope, dynamic risk score meter, Recharts telemetry trend charts, and real-time WebSocket subscriber (`/ws/monitoring`).

### 5. Running Edge AI Pipeline & Benchmark
```bash
# Generate synthetic dataset (8,000 samples)
python edge_ai/training/generate_dataset.py

# Train Random Forest classifier
python edge_ai/training/train_model.py

# Evaluate model accuracy & metrics
python edge_ai/training/evaluate_model.py

# Run standalone sensor simulator with live inference
python edge_ai/simulator/main.py --scenario LOW_SPO2

# Run empirical latency benchmark (Edge vs Cloud REST)
python edge_ai/benchmark.py
```

### 6. Running Complete Test Suite (82 Tests)
```bash
# Run all unit, integration, security, and API tests
python tests/run_tests.py
```

### 7. Docker & Docker Compose Deployment
```bash
# Build and launch multi-container architecture (Backend, Frontend, Edge AI Node)
docker-compose up --build -d

# View running container status
docker-compose ps

# View container logs
docker-compose logs -f backend

# Stop docker containers
docker-compose down
```

### 8. Academic Presentation & Clinical Demo
To launch the 13-step Doctor Demo mode:
1. Start backend server: `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload`
2. Open browser at `http://127.0.0.1:8000`
3. Click **Doctor Quick Login** (`doctor@example.com` / `Doctor123!`) and click **Sign In**.
4. In the top controller bar, select Patient `P001 - John Doe`, Scenario `LOW_SPO2 (Hypoxia)`, Duration `60s`, and click **`▶ Start Simulation`**.
5. See full presentation guide at [docs/demo_guide.md](docs/demo_guide.md) and full project report at [docs/project-report.md](docs/project-report.md).

---

## 📁 Repository Structure

```
rpm-edge-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # API Routes, WebSockets, & SPA Entrypoint
│   │   ├── database.py              # SQLite / SQLAlchemy Engine & init_db()
│   │   ├── models.py                # User, Patient, VitalReading, AIPrediction, Alert, EdgeNode
│   │   ├── schemas.py               # Pydantic Request/Response Validators
│   │   ├── security/                # Auth, JWT, Password Hashing, RBAC Dependencies
│   │   ├── services/                # Alert Service Engine & Audit Logger
│   │   └── routers/                 # Modular API & WebSocket Routers
├── edge_ai/                         # Edge AI Subsystem
│   ├── simulator/                   # Sensor Simulator & 8 Scenario Generators
│   ├── training/                    # Dataset & Model Training Pipeline
│   ├── inference/                   # Real Model Inference & Clinical Risk Engine
│   └── models/                      # Saved Model Artifacts (.joblib)
├── frontend/                        # Frontend Web SPA Subsystem
│   ├── index.html                   # Production React SPA & HTML5 Canvas Oscilloscope
│   └── nginx.conf                   # Nginx web server config for Docker
├── docs/                            # Project Documentation
│   ├── project-report.md            # Complete 32-Section Academic Project Report
│   └── demo_guide.md                # Professor Presentation & Clinical Demo Guide
├── scripts/
│   └── seed_database.py             # Seed generator for demo users & patients
├── tests/                           # Master Integration Test Suite (82 test cases)
│   └── run_tests.py                 # Master Test Runner
├── docker-compose.yml
└── README.md
```
