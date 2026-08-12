import datetime
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from backend.app import models

class AlertService:
    """
    Intelligent Clinical Alert Engine.
    Evaluates physiological vital sign thresholds and Edge AI risk scores.
    Enforces database persistence and cooldown windows to prevent alert spam.
    """
    def __init__(self, cooldown_seconds: int = 60):
        self.cooldown_seconds = cooldown_seconds
        # In-memory dictionary tracking (patient_id, alert_type) -> last_alert_timestamp
        self._last_alert_time: Dict[Tuple[int, str], datetime.datetime] = {}

    def reset_cooldown(self):
        """Clears all in-memory cooldown state (used for testing)."""
        self._last_alert_time.clear()

    def evaluate_telemetry(
        self,
        db: Session,
        patient: models.Patient,
        vitals: dict,
        prediction: dict
    ) -> Optional[models.Alert]:
        """
        Evaluates patient vitals and AI predictions to generate actionable alerts.
        Enforces cooldown anti-spam protection.
        """
        patient_id = patient.id
        patient_code = patient.patient_code or f"P{patient_id:03d}"
        
        hr = vitals.get("heart_rate", 75)
        spo2 = vitals.get("spo2", 98)
        temp = vitals.get("temperature", 36.8)
        rr = vitals.get("respiratory_rate", 16)
        act = vitals.get("activity_level", "RESTING")
        
        label = prediction.get("prediction") or prediction.get("label") or "NORMAL"
        risk_score = prediction.get("risk_score", 0.0)
        
        severity = None
        alert_type = None
        
        # 1. Evaluate Critical Physiological & AI Conditions
        if spo2 < 90.0:
            severity = "CRITICAL"
            alert_type = "LOW_SPO2_HYPOXIA"
        elif act == "SUDDEN_FALL" or label == "FALL":
            severity = "CRITICAL"
            alert_type = "PATIENT_FALL_DETECTED"
        elif hr > 130:
            severity = "CRITICAL"
            alert_type = "SEVERE_TACHYCARDIA"
        elif hr < 45:
            severity = "CRITICAL"
            alert_type = "SEVERE_BRADYCARDIA"
        elif temp > 38.5:
            severity = "CRITICAL"
            alert_type = "HIGH_FEVER"
        elif label == "CRITICAL" or risk_score >= 0.85:
            severity = "CRITICAL"
            alert_type = "MULTI_PARAMETER_CRITICAL"
            
        # 2. Evaluate Warning Level Conditions
        elif spo2 <= 94.0:
            severity = "WARNING"
            alert_type = "MILD_HYPOXIA"
        elif hr > 100:
            severity = "WARNING"
            alert_type = "MODERATE_TACHYCARDIA"
        elif hr < 55:
            severity = "WARNING"
            alert_type = "MODERATE_BRADYCARDIA"
        elif temp >= 37.8:
            severity = "WARNING"
            alert_type = "MODERATE_FEVER"
        elif risk_score >= 0.65:
            severity = "WARNING"
            alert_type = "ELEVATED_RISK_OBSERVATION"
        elif label != "NORMAL":
            severity = "INFO"
            alert_type = f"PHYSIOLOGICAL_{label}"

        now = datetime.datetime.now(datetime.timezone.utc)

        # If vitals/predictions are completely NORMAL, update patient status to NORMAL
        if not severity or not alert_type:
            if patient.status != "NORMAL":
                patient.status = "NORMAL"
                patient.updated_at = now
                db.commit()
                db.refresh(patient)
            return None

        # 3. Check Cooldown Window to Avoid Alert Spam
        key = (patient_id, alert_type)
        if key in self._last_alert_time:
            last_time = self._last_alert_time[key]
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=datetime.timezone.utc)
            if (now - last_time).total_seconds() < self.cooldown_seconds:
                # Suppress alert creation due to active cooldown, but keep patient status updated
                if patient.status != severity:
                    patient.status = severity
                    patient.updated_at = now
                    db.commit()
                    db.refresh(patient)
                return None

        # Update last alert timestamp
        self._last_alert_time[key] = now

        # 4. Format Structured Alert Message
        msg = (
            f"Patient: {patient_code} ({patient.name})\n"
            f"SpO₂: {spo2:.1f}%\n"
            f"Heart Rate: {hr:.0f} BPM\n"
            f"Temp: {temp:.1f}°C, RR: {rr:.0f} br/m\n"
            f"Prediction: {label}\n"
            f"Risk Score: {risk_score:.2f}"
        )

        # 5. Persist Alert to Database
        alert = models.Alert(
            patient_id=patient_id,
            alert_type=alert_type,
            severity=severity,
            message=msg,
            timestamp=now,
            status="ACTIVE"
        )
        
        # Update patient status in DB to match alert severity
        patient.status = severity
        patient.updated_at = now

        db.add(alert)
        db.commit()
        db.refresh(alert)
        db.refresh(patient)

        return alert

# Global Singleton Alert Service Instance
alert_service = AlertService(cooldown_seconds=60)
