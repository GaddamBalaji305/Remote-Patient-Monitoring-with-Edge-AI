from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models
from edge_ai.inference.metrics_tracker import metrics_tracker
from edge_ai.benchmark import run_controlled_benchmark

router = APIRouter(prefix="/monitoring", tags=["Performance Monitoring"])

@router.get("/metrics")
def get_system_metrics(db: Session = Depends(get_db)):
    """
    Returns real-time Edge AI system performance metrics including inference latency,
    CPU usage %, memory footprint MB, model file size, and sample throughput.
    """
    summary = metrics_tracker.get_metrics_summary()
    
    # Query database sample counts for total historical records
    total_db_vitals = db.query(models.VitalReading).count()
    total_db_predictions = db.query(models.AIPrediction).count()
    
    summary["db_vitals_count"] = total_db_vitals
    summary["db_predictions_count"] = total_db_predictions
    summary["processed_samples_count"] = max(summary["processed_samples_count"], total_db_vitals)
    summary["connection_status"] = "ONLINE"
    
    return summary

@router.get("/benchmark")
def get_edge_vs_cloud_benchmark(
    iterations: int = Query(5, ge=1, le=50, description="Benchmark sample count")
):
    """
    Executes controlled empirical performance benchmark comparing local Edge AI inference
    against HTTP round-trip Cloud REST API inference.
    """
    return run_controlled_benchmark(iterations=iterations)
