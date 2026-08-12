from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from backend.database import Base

class PatientDB(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    room = Column(String)
    condition = Column(String)
    baseline_hr = Column(Float, default=75.0)
    baseline_spo2 = Column(Float, default=98.0)
    baseline_sys_bp = Column(Float, default=120.0)
    baseline_dia_bp = Column(Float, default=80.0)
    baseline_temp = Column(Float, default=36.8)
    baseline_rr = Column(Float, default=16.0)
    edge_node_id = Column(String, default="EDGE-NODE-01")
    status = Column(String, default="Normal")

    vitals = relationship("VitalReadingDB", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("AlertDB", back_populates="patient", cascade="all, delete-orphan")

class VitalReadingDB(Base):
    __tablename__ = "vital_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    timestamp = Column(Float, default=lambda: datetime.datetime.now().timestamp())
    heart_rate = Column(Float)
    spo2 = Column(Float)
    sys_bp = Column(Float)
    dia_bp = Column(Float)
    temperature = Column(Float)
    respiratory_rate = Column(Float)
    mean_rr_ms = Column(Float)
    sdnn_ms = Column(Float)
    rmssd_ms = Column(Float)
    anomaly_score = Column(Float, default=0.0)
    is_anomaly = Column(Boolean, default=False)
    alert_level = Column(String, default="Normal")
    condition = Column(String, default="Normal")

    patient = relationship("PatientDB", back_populates="vitals")

class AlertDB(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    patient_name = Column(String)
    edge_node_id = Column(String)
    severity = Column(String)  # "Critical", "Warning", "Info"
    title = Column(String)
    description = Column(Text)
    timestamp = Column(Float)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String, nullable=True)

    patient = relationship("PatientDB", back_populates="alerts")

class EdgeNodeDB(Base):
    __tablename__ = "edge_nodes"

    node_id = Column(String, primary_key=True)
    device_name = Column(String)
    battery_pct = Column(Float)
    cpu_usage_pct = Column(Float)
    ram_usage_mb = Column(Float)
    inference_latency_ms = Column(Float)
    packets_processed = Column(Integer)
    status = Column(String)
    last_seen = Column(Float)
