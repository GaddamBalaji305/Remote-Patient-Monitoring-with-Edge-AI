import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import relationship
import enum
from backend.app.database import Base

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    CAREGIVER = "CAREGIVER"

class PatientStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

# --- Models ---

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.DOCTOR.value, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    phone = Column(String(30), nullable=True)
    emergency_contact = Column(String(30), nullable=True)
    room = Column(String(50), nullable=True)
    status = Column(String(20), default=PatientStatus.NORMAL.value, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    vital_readings = relationship("VitalReading", back_populates="patient", cascade="all, delete-orphan")
    ai_predictions = relationship("AIPrediction", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="patient", cascade="all, delete-orphan")


class VitalReading(Base):
    __tablename__ = "vital_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, index=True, nullable=False)
    heart_rate = Column(Float, nullable=False)
    spo2 = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    respiratory_rate = Column(Float, nullable=False)
    systolic_bp = Column(Float, nullable=False)
    diastolic_bp = Column(Float, nullable=False)
    activity_level = Column(String(50), default="Resting", nullable=True)

    patient = relationship("Patient", back_populates="vital_readings")


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, index=True, nullable=False)
    prediction = Column(String(100), nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), default="1.0.0", nullable=False)
    inference_latency = Column(Float, nullable=False) # in milliseconds

    patient = relationship("Patient", back_populates="ai_predictions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, index=True, nullable=False)
    severity = Column(String(20), default=AlertSeverity.WARNING.value, index=True, nullable=False)
    alert_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default=AlertStatus.ACTIVE.value, index=True, nullable=False)
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=utc_now, index=True, nullable=False)
    ip_address = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs")

