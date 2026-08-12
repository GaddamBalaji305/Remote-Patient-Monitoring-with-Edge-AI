from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import datetime
from backend.app.database import get_db
from backend.app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    """
    Health check endpoint returning system status and database connectivity.
    """
    db_status = "Healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"Unhealthy: {str(e)}"

    return {
        "status": "Online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
