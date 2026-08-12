from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security.dependencies import require_roles
from backend.app.models import UserRole
from backend.app.services.audit_logger import audit_logger

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=List[schemas.PatientResponse])
def get_patients(
    search: Optional[str] = Query(None, description="Search by name, patient code, or room"),
    status: Optional[str] = Query(None, description="Filter by status (NORMAL, WARNING, CRITICAL, OFFLINE)"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(10, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value, UserRole.DOCTOR.value, UserRole.CAREGIVER.value]))
):
    """
    Retrieve patients with optional search, status filtering, and pagination.
    """
    query = db.query(models.Patient)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Patient.name.ilike(search_pattern),
                models.Patient.patient_code.ilike(search_pattern),
                models.Patient.room.ilike(search_pattern)
            )
        )

    if status:
        query = query.filter(models.Patient.status == status.strip().upper())

    patients = query.order_by(models.Patient.id.asc()).offset(skip).limit(limit).all()
    return patients


@router.post("", response_model=schemas.PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient_in: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value, UserRole.DOCTOR.value]))
):
    """Create a new patient (Admin, Doctor). Verifies unique patient code."""
    existing = db.query(models.Patient).filter(models.Patient.patient_code == patient_in.patient_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with code '{patient_in.patient_code}' already exists."
        )
    
    patient = models.Patient(**patient_in.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Record Security Audit Log
    audit_logger.log_event(
        db=db,
        user_id=current_user.id,
        action="PATIENT_CREATED",
        details=f"Created patient record ID {patient.id} ({patient.patient_code})"
    )

    return patient


@router.get("/{patient_id}", response_model=schemas.PatientDetailResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value, UserRole.DOCTOR.value, UserRole.CAREGIVER.value]))
):
    """
    Retrieve comprehensive patient details including profile, current status,
    latest vitals, latest AI prediction, latest alert, and last update timestamp.
    """
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Fetch latest vitals, AI prediction, and alert
    latest_vitals = db.query(models.VitalReading).filter(models.VitalReading.patient_id == patient_id).order_by(models.VitalReading.timestamp.desc()).first()
    latest_prediction = db.query(models.AIPrediction).filter(models.AIPrediction.patient_id == patient_id).order_by(models.AIPrediction.timestamp.desc()).first()
    latest_alert = db.query(models.Alert).filter(models.Alert.patient_id == patient_id).order_by(models.Alert.timestamp.desc()).first()

    return {
        **patient.__dict__,
        "latest_vitals": latest_vitals,
        "latest_prediction": latest_prediction,
        "latest_alert": latest_alert,
        "last_updated": patient.updated_at
    }


@router.put("/{patient_id}", response_model=schemas.PatientResponse)
def update_patient(
    patient_id: int,
    patient_in: schemas.PatientUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value, UserRole.DOCTOR.value]))
):
    """Update existing patient details (Admin, Doctor)."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    update_data = patient_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    # Record Security Audit Log
    audit_logger.log_event(
        db=db,
        user_id=current_user.id,
        action="PATIENT_UPDATED",
        details=f"Updated patient ID {patient.id} fields: {list(update_data.keys())}"
    )

    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_200_OK)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value]))
):
    """Delete patient by ID (Admin only)."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    patient_code = patient.patient_code
    db.delete(patient)
    db.commit()

    # Record Security Audit Log
    audit_logger.log_event(
        db=db,
        user_id=current_user.id,
        action="PATIENT_DELETED",
        details=f"Deleted patient ID {patient_id} ({patient_code})"
    )

    return {"status": "success", "message": f"Patient ID {patient_id} deleted successfully"}


@router.get("/{patient_id}/vitals", response_model=List[schemas.VitalReadingResponse])
def get_patient_vitals(
    patient_id: int,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value, UserRole.DOCTOR.value, UserRole.CAREGIVER.value]))
):
    """Get vital reading time-series history for charting (ordered chronologically)."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    vitals = db.query(models.VitalReading).filter(models.VitalReading.patient_id == patient_id).order_by(models.VitalReading.timestamp.asc()).limit(limit).all()
    return vitals


@router.get("/{patient_id}/predictions", response_model=List[schemas.AIPredictionResponse])
def get_patient_predictions(
    patient_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value, UserRole.DOCTOR.value]))
):
    """Get AI prediction history for a specific patient."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    predictions = db.query(models.AIPrediction).filter(models.AIPrediction.patient_id == patient_id).order_by(models.AIPrediction.timestamp.desc()).limit(limit).all()
    return predictions


@router.get("/{patient_id}/alerts", response_model=List[schemas.AlertResponse])
def get_patient_alerts(
    patient_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value, UserRole.DOCTOR.value, UserRole.CAREGIVER.value]))
):
    """Get alert history for a specific patient."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    alerts = db.query(models.Alert).filter(models.Alert.patient_id == patient_id).order_by(models.Alert.timestamp.desc()).limit(limit).all()
    return alerts
