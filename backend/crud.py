from sqlalchemy.orm import Session
from backend.models import PatientDB, VitalReadingDB, AlertDB, EdgeNodeDB
import time

def get_all_patients(db: Session):
    return db.query(PatientDB).all()

def get_patient(db: Session, patient_id: str):
    return db.query(PatientDB).filter(PatientDB.id == patient_id).first()

def get_active_alerts(db: Session):
    return db.query(AlertDB).order_by(AlertDB.timestamp.desc()).all()

def acknowledge_alert(db: Session, alert_id: int, clinician_name: str = "Dr. On-Duty"):
    alert = db.query(AlertDB).filter(AlertDB.id == alert_id).first()
    if alert:
        alert.acknowledged = True
        alert.acknowledged_by = clinician_name
        db.commit()
        db.refresh(alert)
    return alert

def update_edge_node(db: Session, hardware_data: dict):
    node_id = hardware_data.get("node_id", "EDGE-NODE-01")
    node = db.query(EdgeNodeDB).filter(EdgeNodeDB.node_id == node_id).first()
    if not node:
        node = EdgeNodeDB(
            node_id=node_id,
            device_name="NVIDIA Jetson Orin Nano",
            battery_pct=hardware_data.get("battery_pct", 98.0),
            cpu_usage_pct=hardware_data.get("cpu_usage_pct", 15.0),
            ram_usage_mb=hardware_data.get("ram_usage_mb", 140.0),
            inference_latency_ms=hardware_data.get("inference_latency_ms", 4.2),
            packets_processed=hardware_data.get("packets_processed", 100),
            status=hardware_data.get("status", "Healthy"),
            last_seen=time.time()
        )
        db.add(node)
    else:
        node.battery_pct = hardware_data.get("battery_pct", node.battery_pct)
        node.cpu_usage_pct = hardware_data.get("cpu_usage_pct", node.cpu_usage_pct)
        node.ram_usage_mb = hardware_data.get("ram_usage_mb", node.ram_usage_mb)
        node.inference_latency_ms = hardware_data.get("inference_latency_ms", node.inference_latency_ms)
        node.packets_processed = hardware_data.get("packets_processed", node.packets_processed)
        node.status = hardware_data.get("status", node.status)
        node.last_seen = time.time()
        
    db.commit()
    db.refresh(node)
    return node
