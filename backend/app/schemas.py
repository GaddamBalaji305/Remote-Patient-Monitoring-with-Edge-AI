import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional
from backend.app.models import UserRole, PatientStatus, AlertSeverity, AlertStatus

# --- Auth & Login Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str

class UserBase(BaseModel):
    name: str
    email: str
    role: str = UserRole.DOCTOR.value

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Patient Schemas ---
class PatientBase(BaseModel):
    patient_code: str
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    room: Optional[str] = None
    status: str = PatientStatus.NORMAL.value

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150.")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        v_clean = v.strip().title() if isinstance(v, str) else v
        if v_clean not in ["Male", "Female", "Other"]:
            raise ValueError("Gender must be 'Male', 'Female', or 'Other'.")
        return v_clean

    @field_validator("patient_code")
    @classmethod
    def validate_patient_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Patient code cannot be empty.")
        return v.strip().upper()

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    room: Optional[str] = None
    status: Optional[str] = None

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 0 or v > 150):
            raise ValueError("Age must be between 0 and 150.")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().title() if isinstance(v, str) else v
            if v_clean not in ["Male", "Female", "Other"]:
                raise ValueError("Gender must be 'Male', 'Female', or 'Other'.")
            return v_clean
        return v

class PatientResponse(PatientBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

# --- VitalReading Schemas ---
class VitalReadingCreate(BaseModel):
    patient_id: int
    heart_rate: float
    spo2: float
    temperature: float
    respiratory_rate: float
    systolic_bp: float
    diastolic_bp: float
    activity_level: Optional[str] = "Resting"
    timestamp: Optional[datetime.datetime] = None

class VitalReadingResponse(VitalReadingCreate):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# --- AIPrediction Schemas ---
class AIPredictionCreate(BaseModel):
    patient_id: int
    prediction: str
    risk_score: float
    confidence: float
    model_version: Optional[str] = "1.0.0"
    inference_latency: float
    timestamp: Optional[datetime.datetime] = None

class AIPredictionResponse(AIPredictionCreate):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# --- Alert Schemas ---
class AlertCreate(BaseModel):
    patient_id: int
    severity: str = AlertSeverity.WARNING.value
    alert_type: str
    message: str
    status: str = AlertStatus.ACTIVE.value
    timestamp: Optional[datetime.datetime] = None

class AlertAcknowledge(BaseModel):
    acknowledged_by: str = "Dr. On-Duty"

class AlertResponse(AlertCreate):
    id: int
    timestamp: datetime.datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# --- Detailed Patient Response Schema ---
class PatientDetailResponse(PatientResponse):
    latest_vitals: Optional[VitalReadingResponse] = None
    latest_prediction: Optional[AIPredictionResponse] = None
    latest_alert: Optional[AlertResponse] = None
    last_updated: datetime.datetime

    class Config:
        from_attributes = True

# --- Dashboard Statistics Schema ---
class DashboardStatisticsResponse(BaseModel):
    total_patients: int
    active_monitoring: int
    warning: int
    critical: int
    offline: int

# --- Edge Ingestion Schemas ---
class EdgeVitalsPayload(BaseModel):
    heart_rate: float
    spo2: float
    temperature: float
    respiratory_rate: float
    systolic_bp: Optional[float] = 120.0
    diastolic_bp: Optional[float] = 80.0
    activity_level: Optional[str] = "RESTING"

class EdgePredictionPayload(BaseModel):
    label: str
    risk_score: float
    confidence: float

class EdgeEventCreate(BaseModel):
    patient_id: str  # Code or ID e.g. "P001" or "PAT-001"
    timestamp: Optional[str] = None
    vitals: EdgeVitalsPayload
    prediction: EdgePredictionPayload
    inference_latency: float

class EdgeEventResponse(BaseModel):
    status: str = "success"
    message: str
    patient_id: int
    vital_reading_id: int
    prediction_id: int
    alert_created: bool = False
    alert_id: Optional[int] = None
    patient_status: str
