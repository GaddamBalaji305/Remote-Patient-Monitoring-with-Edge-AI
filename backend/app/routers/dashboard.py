from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas
from backend.app.security.dependencies import require_roles
from backend.app.models import UserRole, PatientStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/statistics", response_model=schemas.DashboardStatisticsResponse)
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles([UserRole.ADMIN.value, UserRole.DOCTOR.value, UserRole.CAREGIVER.value]))
):
    """
    Retrieve dynamic dashboard statistics calculated directly from the database.
    Returns count of total_patients, active_monitoring, warning, critical, and offline.
    """
    total_patients = db.query(models.Patient).count()
    warning_count = db.query(models.Patient).filter(models.Patient.status == PatientStatus.WARNING.value).count()
    critical_count = db.query(models.Patient).filter(models.Patient.status == PatientStatus.CRITICAL.value).count()
    offline_count = db.query(models.Patient).filter(models.Patient.status == PatientStatus.OFFLINE.value).count()

    # Active monitoring = patients being monitored (all patients except OFFLINE)
    active_monitoring = db.query(models.Patient).filter(models.Patient.status != PatientStatus.OFFLINE.value).count()

    return {
        "total_patients": total_patients,
        "active_monitoring": active_monitoring,
        "warning": warning_count,
        "critical": critical_count,
        "offline": offline_count
    }
