from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import datetime
from backend.app.database import get_db
from backend.app import models, schemas

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.post("", response_model=schemas.AIPredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(prediction_in: schemas.AIPredictionCreate, db: Session = Depends(get_db)):
    """Log an AI inference prediction result for a patient."""
    patient = db.query(models.Patient).filter(models.Patient.id == prediction_in.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient ID {prediction_in.patient_id} does not exist."
        )

    pred_data = prediction_in.model_dump()
    if not pred_data.get("timestamp"):
        pred_data["timestamp"] = datetime.datetime.now(datetime.timezone.utc)

    ai_prediction = models.AIPrediction(**pred_data)
    db.add(ai_prediction)
    db.commit()
    db.refresh(ai_prediction)
    return ai_prediction
