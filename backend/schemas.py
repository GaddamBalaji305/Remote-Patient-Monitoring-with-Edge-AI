from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class PatientBase(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    room: str
    condition: str
    baseline_hr: float
    baseline_spo2: float
    baseline_sys_bp: float
    baseline_dia_bp: float
    baseline_temp: float
    baseline_rr: float
    edge_node_id: str
    status: str = "Normal"

    class Config:
        from_attributes = True

class VitalReadingSchema(BaseModel):
    patient_id: str
    timestamp: float
    heart_rate: float
    spo2: float
    sys_bp: float
    dia_bp: float
    temperature: float
    respiratory_rate: float
    sdnn_ms: Optional[float] = 35.0
    anomaly_score: float = 0.0
    is_anomaly: bool = False
    alert_level: str = "Normal"
    condition: str = "Normal"

class AlertSchema(BaseModel):
    id: Optional[int] = None
    patient_id: str
    patient_name: str
    edge_node_id: str
    severity: str
    title: str
    description: str
    timestamp: float
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None

    class Config:
        from_attributes = True

class EdgeNodeSchema(BaseModel):
    node_id: str
    battery_pct: float
    cpu_usage_pct: float
    ram_usage_mb: float
    inference_latency_ms: float
    packets_processed: int
    status: str

class TelemetryIngestSchema(BaseModel):
    telemetry: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    edge_hardware: Dict[str, Any]

class AnomalySimulateSchema(BaseModel):
    patient_id: str
    anomaly_type: str  # "Arrhythmia", "Hypoxia", "Hypertension", "SensorDisconnect", "None"
