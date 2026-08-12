import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.models import PatientStatus
from backend.app.services.alert_service import alert_service
from backend.app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/edge", tags=["Edge Ingestion"])

@router.post("/events", response_model=schemas.EdgeEventResponse, status_code=status.HTTP_201_CREATED)
async def receive_edge_event(
    event_in: schemas.EdgeEventCreate,
    db: Session = Depends(get_db)
):
    """
    Ingests compiled Edge AI telemetry event containing vitals, model prediction, risk score, and latency.
    Saves VitalReading, AIPrediction, updates Patient status, generates Alerts via AlertEngine,
    and broadcasts live updates to all connected WebSockets (/ws/monitoring).
    """
    patient_code = str(event_in.patient_id).strip().upper()
    
    # 1. Look up patient or create new patient record
    patient = db.query(models.Patient).filter(
        (models.Patient.patient_code == patient_code) | (models.Patient.id == patient_code)
    ).first()

    if not patient:
        patient = models.Patient(
            patient_code=patient_code,
            name=f"Patient {patient_code}",
            age=60,
            gender="Other",
            room="Edge Monitored Unit",
            status=PatientStatus.NORMAL.value
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

    now = datetime.datetime.now(datetime.timezone.utc)

    # 2. Insert VitalReading record
    vitals_payload = event_in.vitals
    vital_reading = models.VitalReading(
        patient_id=patient.id,
        timestamp=now,
        heart_rate=vitals_payload.heart_rate,
        spo2=vitals_payload.spo2,
        temperature=vitals_payload.temperature,
        respiratory_rate=vitals_payload.respiratory_rate,
        systolic_bp=vitals_payload.systolic_bp or 120.0,
        diastolic_bp=vitals_payload.diastolic_bp or 80.0,
        activity_level=vitals_payload.activity_level or "RESTING"
    )
    db.add(vital_reading)

    # 3. Insert AIPrediction record
    pred_payload = event_in.prediction
    ai_prediction = models.AIPrediction(
        patient_id=patient.id,
        timestamp=now,
        prediction=pred_payload.label,
        risk_score=pred_payload.risk_score,
        confidence=pred_payload.confidence,
        model_version="1.2.0-rf-edge",
        inference_latency=event_in.inference_latency
    )
    db.add(ai_prediction)
    db.commit()
    db.refresh(vital_reading)
    db.refresh(ai_prediction)

    # 4. Evaluate Patient Status & Alert Engine Generation (with anti-spam cooldown)
    vitals_dict = vitals_payload.model_dump()
    prediction_dict = pred_payload.model_dump()

    new_alert = alert_service.evaluate_telemetry(
        db=db,
        patient=patient,
        vitals=vitals_dict,
        prediction=prediction_dict
    )

    alert_created = new_alert is not None
    created_alert_id = new_alert.id if new_alert else None

    # 5. Broadcast to connected WebSocket dashboards (/ws/monitoring)
    timestamp_str = event_in.timestamp or now.strftime("%Y-%m-%dT%H:%M:%SZ")
    broadcast_payload = {
        "patient_id": patient_code,
        "timestamp": timestamp_str,
        "vitals": {
            "heart_rate": int(round(vitals_payload.heart_rate)),
            "spo2": int(round(vitals_payload.spo2)),
            "temperature": round(vitals_payload.temperature, 1),
            "respiratory_rate": int(round(vitals_payload.respiratory_rate)),
            "systolic_bp": int(round(vitals_payload.systolic_bp or 120.0)),
            "diastolic_bp": int(round(vitals_payload.diastolic_bp or 80.0)),
            "activity_level": vitals_payload.activity_level or "RESTING"
        },
        "prediction": {
            "label": pred_payload.label,
            "risk_score": round(pred_payload.risk_score, 2),
            "confidence": round(pred_payload.confidence, 2)
        },
        "status": patient.status,
        "alert": {
            "id": created_alert_id,
            "severity": new_alert.severity,
            "alert_type": new_alert.alert_type,
            "message": new_alert.message
        } if new_alert else None
    }

    await ws_manager.broadcast(broadcast_payload)

    return {
        "status": "success",
        "message": "Edge AI event successfully ingested, evaluated by Alert Engine, stored, and broadcasted.",
        "patient_id": patient.id,
        "vital_reading_id": vital_reading.id,
        "prediction_id": ai_prediction.id,
        "alert_created": alert_created,
        "alert_id": created_alert_id,
        "patient_status": patient.status
    }
