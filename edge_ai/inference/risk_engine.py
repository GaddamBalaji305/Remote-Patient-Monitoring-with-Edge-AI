from typing import Dict, Any

class RiskEngine:
    """
    Configurable Clinical Risk Engine.
    Maps model prediction & risk scores into risk categories (LOW, MEDIUM, HIGH)
    and patient status badges (NORMAL, WARNING, CRITICAL).
    """
    def __init__(
        self,
        medium_risk_threshold: float = 0.35,
        high_risk_threshold: float = 0.70
    ):
        self.medium_risk_threshold = medium_risk_threshold
        self.high_risk_threshold = high_risk_threshold

    def evaluate_risk(self, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates risk level and alerts based on model prediction and risk score.
        """
        prediction = prediction_result.get("prediction", "NORMAL")
        risk_score = float(prediction_result.get("risk_score", 0.0))
        confidence = float(prediction_result.get("confidence", 0.0))
        latency = float(prediction_result.get("inference_latency_ms", 0.0))

        # Risk Category Mapping
        if risk_score >= self.high_risk_threshold or prediction in ["CRITICAL", "FALL", "LOW_SPO2"]:
            risk_level = "HIGH"
            patient_status = "CRITICAL"
            action_required = "Immediate clinical intervention and emergency alert dispatch."
        elif risk_score >= self.medium_risk_threshold or prediction in ["TACHYCARDIA", "BRADYCARDIA", "FEVER", "ABNORMAL_RESPIRATION"]:
            risk_level = "MEDIUM"
            patient_status = "WARNING"
            action_required = "Caregiver notification and vital trend observation."
        else:
            risk_level = "LOW"
            patient_status = "NORMAL"
            action_required = "Routine monitoring."

        return {
            "prediction": prediction,
            "risk_score": risk_score,
            "confidence": confidence,
            "risk_level": risk_level,
            "patient_status": patient_status,
            "action_required": action_required,
            "inference_latency_ms": latency
        }
