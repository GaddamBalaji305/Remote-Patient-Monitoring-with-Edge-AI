from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import datetime
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[schemas.AlertResponse])
def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, CRITICAL)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (ACTIVE, ACKNOWLEDGED)"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    limit: int = Query(50, ge=1, le=200, description="Max alerts limit"),
    db: Session = Depends(get_db)
):
    """Retrieve list of clinical alerts with optional severity, status, and patient filtering."""
    query = db.query(models.Alert)

    if severity:
        query = query.filter(models.Alert.severity == severity.strip().upper())
    if status_filter:
        query = query.filter(models.Alert.status == status_filter.strip().upper())
    if patient_id:
        query = query.filter(models.Alert.patient_id == patient_id)

    alerts = query.order_by(models.Alert.timestamp.desc()).limit(limit).all()
    return alerts


@router.post("", response_model=schemas.AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(alert_in: schemas.AlertCreate, db: Session = Depends(get_db)):
    """Create a new clinical alert."""
    patient = db.query(models.Patient).filter(models.Patient.id == alert_in.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient ID {alert_in.patient_id} does not exist."
        )

    alert_data = alert_in.model_dump()
    if not alert_data.get("timestamp"):
        alert_data["timestamp"] = datetime.datetime.now(datetime.timezone.utc)

    alert = models.Alert(**alert_data)
    db.add(alert)
    
    # Sync patient status if alert is Critical/Warning
    if alert_in.severity == models.AlertSeverity.CRITICAL.value:
        patient.status = models.PatientStatus.CRITICAL.value
    elif alert_in.severity == models.AlertSeverity.WARNING.value and patient.status == models.PatientStatus.NORMAL.value:
        patient.status = models.PatientStatus.WARNING.value

    db.commit()
    db.refresh(alert)
    return alert


@router.put("/{alert_id}/acknowledge", response_model=schemas.AlertResponse)
def acknowledge_alert(alert_id: int, ack_in: schemas.AlertAcknowledge = schemas.AlertAcknowledge(), db: Session = Depends(get_db)):
    """Acknowledge an active alert."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = models.AlertStatus.ACKNOWLEDGED.value
    alert.acknowledged_by = ack_in.acknowledged_by or "Dr. On-Duty"
    alert.acknowledged_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    db.refresh(alert)
    return alert
