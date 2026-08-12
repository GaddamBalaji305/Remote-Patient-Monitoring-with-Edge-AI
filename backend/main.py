from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
import logging
import time
from typing import List, Dict, Any

from backend.config import BackendConfig
from backend.database import engine, Base, get_db
from backend.models import PatientDB, AlertDB, VitalReadingDB, EdgeNodeDB
from backend import crud, schemas
from backend.websocket_manager import ws_manager

logging.basicConfig(level=logging.INFO)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=BackendConfig.PROJECT_NAME,
    openapi_url=f"{BackendConfig.API_V1_STR}/openapi.json"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=BackendConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory storage for active anomaly simulation overrides
active_simulation_overrides: Dict[str, str] = {}

# Seed initial patients if DB is empty
def seed_patients_if_needed():
    db = next(get_db())
    if db.query(PatientDB).count() == 0:
        initial_patients = [
            PatientDB(id="PAT-101", name="Eleanor Vance", age=68, gender="Female", room="ICU Bed 01", condition="Post-MI Monitoring", baseline_hr=74.0, baseline_spo2=97.0, baseline_sys_bp=124.0, baseline_dia_bp=82.0, baseline_temp=36.8, baseline_rr=16.0, edge_node_id="EDGE-NODE-01", status="Normal"),
            PatientDB(id="PAT-102", name="Marcus Holloway", age=54, gender="Male", room="Telemetry 204", condition="COPD Exacerbation", baseline_hr=82.0, baseline_spo2=94.0, baseline_sys_bp=138.0, baseline_dia_bp=88.0, baseline_temp=37.1, baseline_rr=20.0, edge_node_id="EDGE-NODE-02", status="Warning"),
            PatientDB(id="PAT-103", name="Sophia Rodriguez", age=72, gender="Female", room="CCU Bed 04", condition="Congestive Heart Failure", baseline_hr=68.0, baseline_spo2=98.0, baseline_sys_bp=118.0, baseline_dia_bp=76.0, baseline_temp=36.6, baseline_rr=15.0, edge_node_id="EDGE-NODE-03", status="Normal"),
            PatientDB(id="PAT-104", name="Dr. Arthur Pendelton", age=81, gender="Male", room="Step-Down 108", condition="Post-Op Cardiac Bypass", baseline_hr=92.0, baseline_spo2=95.0, baseline_sys_bp=145.0, baseline_dia_bp=92.0, baseline_temp=37.4, baseline_rr=18.0, edge_node_id="EDGE-NODE-04", status="Warning")
        ]
        db.add_all(initial_patients)
        db.commit()
        logging.info("Database seeded with default patient profiles.")

seed_patients_if_needed()

# --- REST ENDPOINTS ---

@app.get("/")
def root():
    return {
        "system": "Remote Patient Monitoring with Edge AI API",
        "status": "Online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get(f"{BackendConfig.API_V1_STR}/patients", response_model=List[schemas.PatientBase])
def get_patients(db: Session = Depends(get_db)):
    return crud.get_all_patients(db)

@app.get(f"{BackendConfig.API_V1_STR}/patients/{{patient_id}}", response_model=schemas.PatientBase)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.get(f"{BackendConfig.API_V1_STR}/alerts", response_model=List[schemas.AlertSchema])
def get_alerts(db: Session = Depends(get_db)):
    return crud.get_active_alerts(db)

@app.post(f"{BackendConfig.API_V1_STR}/alerts/{{alert_id}}/acknowledge")
def acknowledge_alert(alert_id: int, clinician_name: str = "Dr. On-Duty", db: Session = Depends(get_db)):
    alert = crud.acknowledge_alert(db, alert_id, clinician_name)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "alert_id": alert_id, "acknowledged_by": clinician_name}

@app.get(f"{BackendConfig.API_V1_STR}/edge/metrics")
def get_edge_metrics(db: Session = Depends(get_db)):
    node = db.query(EdgeNodeDB).first()
    if not node:
        return {
            "node_id": "NVIDIA Jetson Orin Nano / ARM Cortex-M55",
            "battery_pct": 98.5,
            "cpu_usage_pct": 14.8,
            "ram_usage_mb": 142.8,
            "inference_latency_ms": 4.2,
            "packets_processed": 1280,
            "status": "Healthy"
        }
    return {
        "node_id": node.device_name or node.node_id,
        "battery_pct": node.battery_pct,
        "cpu_usage_pct": node.cpu_usage_pct,
        "ram_usage_mb": node.ram_usage_mb,
        "inference_latency_ms": node.inference_latency_ms,
        "packets_processed": node.packets_processed,
        "status": node.status
    }

@app.post(f"{BackendConfig.API_V1_STR}/telemetry/ingest")
async def ingest_telemetry(data: schemas.TelemetryIngestSchema, db: Session = Depends(get_db)):
    """
    Ingestion route called by Edge AI Node.
    Saves new critical alerts to SQLite and broadcasts high-frequency telemetry via WebSockets.
    """
    # 1. Update Edge hardware stats
    crud.update_edge_node(db, data.edge_hardware)
    
    # 2. Process any incoming alerts
    for alert_data in data.alerts:
        # Check if identical unacknowledged alert already logged in last 10 seconds
        recent_cutoff = time.time() - 10.0
        existing = db.query(AlertDB).filter(
            AlertDB.patient_id == alert_data["patient_id"],
            AlertDB.title == alert_data["title"],
            AlertDB.acknowledged == False,
            AlertDB.timestamp > recent_cutoff
        ).first()
        
        if not existing:
            new_alert = AlertDB(
                patient_id=alert_data["patient_id"],
                patient_name=alert_data["patient_name"],
                edge_node_id=alert_data["edge_node_id"],
                severity=alert_data["severity"],
                title=alert_data["title"],
                description=alert_data["description"],
                timestamp=alert_data["timestamp"],
                acknowledged=False
            )
            db.add(new_alert)
            
            # Update patient status badge
            patient = db.query(PatientDB).filter(PatientDB.id == alert_data["patient_id"]).first()
            if patient:
                patient.status = alert_data["severity"]
            db.commit()
            
    # 3. Broadcast real-time packet to WebSocket dashboard clients
    broadcast_payload = {
        "type": "TELEMETRY_UPDATE",
        "timestamp": time.time(),
        "patients_telemetry": data.telemetry,
        "edge_hardware": data.edge_hardware,
        "active_overrides": active_simulation_overrides
    }
    await ws_manager.broadcast(broadcast_payload)
    
    return {"status": "accepted", "overrides": active_simulation_overrides}

@app.post(f"{BackendConfig.API_V1_STR}/simulate/anomaly")
async def simulate_anomaly(payload: schemas.AnomalySimulateSchema):
    """
    Allows clinical evaluator to manually inject medical events (Arrhythmia, Hypoxia, Hypertension, SensorDisconnect).
    """
    active_simulation_overrides[payload.patient_id] = payload.anomaly_type
    logging.info(f"Simulation override updated: Patient {payload.patient_id} -> {payload.anomaly_type}")
    
    # Notify WebSocket subscribers immediately
    await ws_manager.broadcast({
        "type": "SIMULATION_OVERRIDE",
        "patient_id": payload.patient_id,
        "anomaly_type": payload.anomaly_type
    })
    
    return {"status": "success", "patient_id": payload.patient_id, "active_anomaly": payload.anomaly_type}

# --- WEBSOCKET ENDPOINT ---

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open & handle incoming client messages
            client_msg = await websocket.receive_text()
            try:
                msg_data = json.loads(client_msg)
                if msg_data.get("action") == "SET_ANOMALY":
                    pid = msg_data.get("patient_id")
                    atype = msg_data.get("anomaly_type")
                    if pid and atype:
                        active_simulation_overrides[pid] = atype
                        await ws_manager.broadcast({
                            "type": "SIMULATION_OVERRIDE",
                            "patient_id": pid,
                            "anomaly_type": atype
                        })
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
