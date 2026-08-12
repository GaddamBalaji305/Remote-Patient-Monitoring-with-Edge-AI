import time
import threading
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app import models
from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.inference.predictor import EdgePredictor
from edge_ai.inference.risk_engine import RiskEngine
from backend.app.services.alert_service import alert_service
from backend.app.routers.websocket_router import ws_manager
from edge_ai.inference.metrics_tracker import metrics_tracker

router = APIRouter(prefix="/demo", tags=["Demo Simulation Controller"])

# Singleton Demo Runner State
class DemoState:
    def __init__(self):
        self.active: bool = False
        self.patient_id: str = "P001"
        self.scenario: str = "LOW_SPO2"
        self.interval_seconds: float = 2.0
        self.duration_seconds: float = 60.0
        self.max_steps: int = 30
        self.current_step: int = 0
        self.thread: Optional[threading.Thread] = None
        self.stop_event: threading.Event = threading.Event()
        self.predictor: Optional[EdgePredictor] = None
        self.risk_engine: Optional[RiskEngine] = None

    def get_status(self) -> Dict[str, Any]:
        return {
            "active": self.active,
            "patient_id": self.patient_id,
            "scenario": self.scenario,
            "interval_seconds": self.interval_seconds,
            "duration_seconds": self.duration_seconds,
            "current_step": self.current_step,
            "max_steps": self.max_steps
        }

demo_state = DemoState()

class DemoStartRequest(BaseModel):
    patient_id: str = Field("P001", description="Target patient code (P001 - P005)")
    scenario: str = Field("LOW_SPO2", description="Scenario (NORMAL, TACHYCARDIA, BRADYCARDIA, LOW_SPO2, FEVER, FALL, CRITICAL)")
    interval_seconds: float = Field(2.0, ge=0.5, le=10.0, description="Step speed interval in seconds")
    duration_seconds: Optional[float] = Field(60.0, ge=5.0, le=600.0, description="Total simulation duration in seconds")
    max_steps: Optional[int] = Field(None, ge=5, le=500, description="Maximum simulation steps (calculated if duration_seconds provided)")

def run_demo_loop():
    """Background thread executing the actual system pipeline sample by sample."""
    demo_state.active = True
    demo_state.stop_event.clear()
    demo_state.current_step = 0

    if demo_state.predictor is None:
        demo_state.predictor = EdgePredictor(model_path="edge_ai/models/edge_random_forest.joblib")
    if demo_state.risk_engine is None:
        demo_state.risk_engine = RiskEngine()

    simulator = PhysiologicalSensorSimulator(
        patient_id=demo_state.patient_id,
        scenario=demo_state.scenario
    )

    print(f"\n[DEMO RUNNER] Starting live simulation for Patient {demo_state.patient_id} with scenario {demo_state.scenario}...")

    try:
        while not demo_state.stop_event.is_set() and demo_state.current_step < demo_state.max_steps:
            demo_state.current_step += 1

            # 1. Sensor Simulator Step
            t0 = time.perf_counter()
            sample = simulator.generate_sample()

            # 2. Edge AI Model Inference
            pred_res = demo_state.predictor.predict(sample)

            # 3. Clinical Risk Engine Evaluation
            risk_res = demo_state.risk_engine.evaluate_risk(pred_res)
            t1 = time.perf_counter()
            latency_ms = round((t1 - t0) * 1000.0, 2)

            metrics_tracker.record_inference(latency_ms)

            # 4. Database Persistence & Alert Engine Evaluation
            db = SessionLocal()
            try:
                patient_db = db.query(models.Patient).filter(
                    (models.Patient.patient_code == demo_state.patient_id) | 
                    (models.Patient.id == (int(demo_state.patient_id.replace('P', '')) if demo_state.patient_id.startswith('P') and demo_state.patient_id[1:].isdigit() else 1))
                ).first()

                if patient_db:
                    patient_db.status = risk_res["patient_status"]
                    patient_db.updated_at = datetime.datetime.now(datetime.timezone.utc)

                    # Save Vital Reading
                    vital_rec = models.VitalReading(
                        patient_id=patient_db.id,
                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                        heart_rate=sample["heart_rate"],
                        spo2=sample["spo2"],
                        temperature=sample["temperature"],
                        respiratory_rate=sample["respiratory_rate"],
                        systolic_bp=sample["systolic_bp"],
                        diastolic_bp=sample["diastolic_bp"],
                        activity_level=sample["activity_level"]
                    )
                    db.add(vital_rec)

                    # Save AI Prediction
                    pred_rec = models.AIPrediction(
                        patient_id=patient_db.id,
                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                        prediction=pred_res["prediction"],
                        risk_score=pred_res["risk_score"],
                        confidence=pred_res["confidence"],
                        inference_latency=latency_ms,
                        model_version="1.2.0-rf-edge"
                    )
                    db.add(pred_rec)
                    db.commit()

                    # Evaluate Alert Engine
                    alert_obj = alert_service.evaluate_telemetry(
                        db=db,
                        patient=patient_db,
                        vitals=sample,
                        prediction=pred_res
                    )

                    # 5. Broadcast Payload to Connected WebSockets Clients
                    ws_payload = {
                        "patient_id": patient_db.patient_code,
                        "timestamp": sample["timestamp"],
                        "vitals": sample,
                        "prediction": {
                            "label": pred_res["prediction"],
                            "risk_score": pred_res["risk_score"],
                            "confidence": pred_res["confidence"]
                        },
                        "status": risk_res["patient_status"],
                        "alert": {
                            "id": alert_obj.id,
                            "severity": alert_obj.severity,
                            "alert_type": alert_obj.alert_type,
                            "message": alert_obj.message
                        } if alert_obj else None
                    }

                    ws_manager.broadcast_sync(ws_payload)

            finally:
                db.close()

            # Wait interval before next step
            time.sleep(demo_state.interval_seconds)

    except Exception as e:
        print(f"[DEMO RUNNER ERROR] {e}")
    finally:
        demo_state.active = False
        print(f"[DEMO RUNNER] Completed live simulation for Patient {demo_state.patient_id}.\n")

@router.post("/start")
def start_demo_simulation(req: DemoStartRequest):
    """
    Starts a background thread executing real-time telemetry simulation through the actual pipeline.
    """
    if demo_state.active:
        demo_state.stop_event.set()
        if demo_state.thread and demo_state.thread.is_alive():
            demo_state.thread.join(timeout=2.0)

    demo_state.patient_id = req.patient_id
    demo_state.scenario = req.scenario
    demo_state.interval_seconds = req.interval_seconds
    
    if req.duration_seconds:
        demo_state.duration_seconds = req.duration_seconds
        demo_state.max_steps = int(req.duration_seconds / req.interval_seconds)
    elif req.max_steps:
        demo_state.max_steps = req.max_steps
        demo_state.duration_seconds = req.max_steps * req.interval_seconds
    else:
        demo_state.duration_seconds = 60.0
        demo_state.max_steps = int(60.0 / req.interval_seconds)

    demo_state.thread = threading.Thread(target=run_demo_loop, daemon=True)
    demo_state.thread.start()


    return {
        "status": "success",
        "message": f"Demo simulation started for Patient {req.patient_id} with scenario {req.scenario}",
        "config": demo_state.get_status()
    }

@router.post("/stop")
def stop_demo_simulation():
    """Stops any active background demo simulation."""
    if demo_state.active:
        demo_state.stop_event.set()
        demo_state.active = False
    return {"status": "success", "message": "Demo simulation stopped."}

@router.get("/status")
def get_demo_status():
    """Returns current active simulation state and parameters."""
    return demo_state.get_status()
