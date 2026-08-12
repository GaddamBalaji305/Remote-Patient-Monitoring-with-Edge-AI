"""
Database Seed Script for Remote Patient Monitoring with Edge AI
Populates synthetic demo accounts, patients, vital readings, AI predictions, and clinical alerts.
"""
import sys
import os
import datetime
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import init_db, SessionLocal
from backend.app.models import User, Patient, VitalReading, AIPrediction, Alert, UserRole, PatientStatus, AlertSeverity, AlertStatus
from backend.app.security.password import hash_password

def seed():
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Demo Seed Accounts (Admin, Doctor, Caregiver)
        print("Seeding demo user accounts...")
        users_data = [
            {
                "name": "System Administrator",
                "email": "admin@example.com",
                "password_hash": hash_password("Admin123!"),
                "role": UserRole.ADMIN.value
            },
            {
                "name": "Dr. Sarah Connor",
                "email": "doctor@example.com",
                "password_hash": hash_password("Doctor123!"),
                "role": UserRole.DOCTOR.value
            },
            {
                "name": "Elena Rostova, RN",
                "email": "caregiver@example.com",
                "password_hash": hash_password("Caregiver123!"),
                "role": UserRole.CAREGIVER.value
            }
        ]
        
        users = []
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user_obj = User(**u)
                db.add(user_obj)
                users.append(user_obj)
            else:
                existing.password_hash = u["password_hash"]
                users.append(existing)
        db.commit()

        # 2. Synthetic Patients (5 required)
        print("Seeding 5 synthetic patients...")
        patients_data = [
            {"patient_code": "PAT-001", "name": "Eleanor Vance", "age": 68, "gender": "Female", "phone": "+1-555-0192", "emergency_contact": "+1-555-9988", "room": "ICU Bed 01", "status": PatientStatus.NORMAL.value},
            {"patient_code": "PAT-002", "name": "Marcus Holloway", "age": 54, "gender": "Male", "phone": "+1-555-0184", "emergency_contact": "+1-555-9977", "room": "Telemetry 204", "status": PatientStatus.WARNING.value},
            {"patient_code": "PAT-003", "name": "Sophia Rodriguez", "age": 72, "gender": "Female", "phone": "+1-555-0176", "emergency_contact": "+1-555-9966", "room": "CCU Bed 04", "status": PatientStatus.NORMAL.value},
            {"patient_code": "PAT-004", "name": "Dr. Arthur Pendelton", "age": 81, "gender": "Male", "phone": "+1-555-0168", "emergency_contact": "+1-555-9955", "room": "Step-Down 108", "status": PatientStatus.CRITICAL.value},
            {"patient_code": "PAT-005", "name": "Clara Oswald", "age": 42, "gender": "Female", "phone": "+1-555-0150", "emergency_contact": "+1-555-9944", "room": "Ward 302", "status": PatientStatus.OFFLINE.value}
        ]

        patients = []
        for p in patients_data:
            existing = db.query(Patient).filter(Patient.patient_code == p["patient_code"]).first()
            if not existing:
                p_obj = Patient(**p)
                db.add(p_obj)
                patients.append(p_obj)
            else:
                patients.append(existing)
        db.commit()

        # Re-query patients to ensure IDs are loaded
        patients = db.query(Patient).all()

        # 3. Sample Vital Readings
        print("Seeding sample vital readings...")
        now = datetime.datetime.now(datetime.timezone.utc)
        for p in patients:
            if db.query(VitalReading).filter(VitalReading.patient_id == p.id).count() == 0:
                for i in range(5):
                    time_offset = now - datetime.timedelta(minutes=(5 - i) * 15)
                    
                    if p.status == PatientStatus.CRITICAL.value:
                        hr = round(random.uniform(115.0, 140.0), 1)
                        spo2 = round(random.uniform(85.0, 89.0), 1)
                        sys_bp = round(random.uniform(160.0, 180.0), 1)
                    elif p.status == PatientStatus.WARNING.value:
                        hr = round(random.uniform(95.0, 110.0), 1)
                        spo2 = round(random.uniform(92.0, 94.0), 1)
                        sys_bp = round(random.uniform(135.0, 148.0), 1)
                    else:
                        hr = round(random.uniform(68.0, 82.0), 1)
                        spo2 = round(random.uniform(96.0, 99.0), 1)
                        sys_bp = round(random.uniform(115.0, 128.0), 1)

                    db.add(VitalReading(
                        patient_id=p.id,
                        timestamp=time_offset,
                        heart_rate=hr,
                        spo2=spo2,
                        temperature=round(random.uniform(36.5, 37.4), 1),
                        respiratory_rate=round(random.uniform(14.0, 22.0), 1),
                        systolic_bp=sys_bp,
                        diastolic_bp=round(sys_bp * 0.65, 1),
                        activity_level="Resting" if i % 2 == 0 else "Light Movement"
                    ))

        # 4. Sample AI Predictions
        print("Seeding sample AI predictions...")
        for p in patients:
            if db.query(AIPrediction).filter(AIPrediction.patient_id == p.id).count() == 0:
                is_anomaly = p.status in [PatientStatus.WARNING.value, PatientStatus.CRITICAL.value]
                pred_label = "Ventricular Arrhythmia / Hypoxia Risk" if is_anomaly else "Normal Sinus Rhythm"
                risk = round(random.uniform(0.75, 0.95), 2) if is_anomaly else round(random.uniform(0.02, 0.12), 2)
                
                db.add(AIPrediction(
                    patient_id=p.id,
                    timestamp=now - datetime.timedelta(minutes=10),
                    prediction=pred_label,
                    risk_score=risk,
                    confidence=round(random.uniform(0.88, 0.98), 2),
                    model_version="1.2.0-edge",
                    inference_latency=round(random.uniform(3.5, 5.2), 2)
                ))

        # 5. Sample Alerts
        print("Seeding sample alerts...")
        alerts_sample = [
            {
                "patient_id": patients[3].id if len(patients) > 3 else patients[0].id,
                "severity": AlertSeverity.CRITICAL.value,
                "alert_type": "Acute Hypoxia & Tachycardia",
                "message": "Critical SpO2 drop to 86% detected alongside elevated heart rate of 128 bpm.",
                "status": AlertStatus.ACTIVE.value,
                "timestamp": now - datetime.timedelta(minutes=5)
            },
            {
                "patient_id": patients[1].id if len(patients) > 1 else patients[0].id,
                "severity": AlertSeverity.WARNING.value,
                "alert_type": "Elevated Blood Pressure",
                "message": "Borderline Hypertensive trend detected (142/90 mmHg).",
                "status": AlertStatus.ACKNOWLEDGED.value,
                "acknowledged_by": "Dr. Sarah Connor",
                "acknowledged_at": now - datetime.timedelta(minutes=20),
                "timestamp": now - datetime.timedelta(minutes=45)
            }
        ]

        for alt in alerts_sample:
            existing = db.query(Alert).filter(Alert.patient_id == alt["patient_id"], Alert.message == alt["message"]).first()
            if not existing:
                db.add(Alert(**alt))

        db.commit()
        print("Database successfully seeded with demo accounts (admin, doctor, caregiver), patients, vitals, AI predictions, and alerts.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
