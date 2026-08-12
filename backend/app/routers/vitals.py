from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import datetime
from backend.app.database import get_db
from backend.app import models, schemas

router = APIRouter(prefix="/vitals", tags=["Vitals"])

@router.post("", response_model=schemas.VitalReadingResponse, status_code=status.HTTP_201_CREATED)
def create_vital_reading(vital_in: schemas.VitalReadingCreate, db: Session = Depends(get_db)):
    """Log a new vital sign reading for a patient."""
    patient = db.query(models.Patient).filter(models.Patient.id == vital_in.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient ID {vital_in.patient_id} does not exist."
        )

    reading_data = vital_in.model_dump()
    if not reading_data.get("timestamp"):
        reading_data["timestamp"] = datetime.datetime.now(datetime.timezone.utc)

    vital_reading = models.VitalReading(**reading_data)
    db.add(vital_reading)
    
    # Auto-update patient status based on vital parameters
    if vital_in.spo2 < 90.0 or vital_in.heart_rate > 130.0 or vital_in.systolic_bp > 170.0:
        patient.status = models.PatientStatus.CRITICAL.value
    elif vital_in.spo2 < 94.0 or vital_in.heart_rate > 105.0 or vital_in.systolic_bp > 140.0:
        if patient.status != models.PatientStatus.CRITICAL.value:
            patient.status = models.PatientStatus.WARNING.value
            
    db.commit()
    db.refresh(vital_reading)
    return vital_reading
