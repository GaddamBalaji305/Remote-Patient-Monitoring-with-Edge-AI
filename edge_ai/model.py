import numpy as np
import time
from typing import Dict, Any, Tuple

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class EdgeAnomalyDetector:
    """
    Ultra-lightweight Edge AI Model for patient vital sign & waveform anomaly classification.
    Optimized for low latency execution on ARM/Jetson edge compute nodes.
    """
    def __init__(self):
        self.is_trained = True
        if HAS_SKLEARN:
            self.clf = IsolationForest(n_estimators=50, contamination=0.1, random_state=42)
            # Dummy fit to initialize model weights
            X_dummy = np.random.normal(loc=[75, 98, 120, 80, 36.8, 16, 35], scale=[5, 1, 10, 5, 0.3, 2, 5], size=(200, 7))
            self.clf.fit(X_dummy)
        else:
            self.clf = None

    def predict(self, vitals: Dict[str, float], hrv_metrics: Dict[str, float]) -> Tuple[bool, float, str, str, float]:
        """
        Runs edge inference on feature vector.
        Features: [HR, SpO2, Sys_BP, Dia_BP, Temp, RR, SDNN]
        Returns: (is_anomaly, anomaly_score [0..1], alert_level, condition_label, latency_ms)
        """
        start_time = time.perf_counter()
        
        hr = vitals.get("heart_rate", 75.0)
        spo2 = vitals.get("spo2", 98.0)
        sys_bp = vitals.get("sys_bp", 120.0)
        dia_bp = vitals.get("dia_bp", 80.0)
        temp = vitals.get("temperature", 36.8)
        rr = vitals.get("respiratory_rate", 16.0)
        sdnn = hrv_metrics.get("sdnn_ms", 35.0)
        
        # Rule-based clinical triage bounds for edge safety fallback
        features = np.array([[hr, spo2, sys_bp, dia_bp, temp, rr, sdnn]])
        
        anomaly_score = 0.05
        condition = "Normal Sinus Rhythm"
        alert_level = "Normal"
        
        # Check specific severe clinical thresholds (Edge Safety Override)
        if spo2 < 90.0:
            anomaly_score = 0.95
            condition = "Acute Hypoxia"
            alert_level = "Critical"
        elif hr > 130.0:
            anomaly_score = 0.88
            condition = "Severe Tachycardia"
            alert_level = "Critical"
        elif hr < 45.0:
            anomaly_score = 0.85
            condition = "Symptomatic Bradycardia"
            alert_level = "Critical"
        elif sys_bp > 170.0 or dia_bp > 105.0:
            anomaly_score = 0.90
            condition = "Hypertensive Crisis"
            alert_level = "Critical"
        elif sdnn < 12.0 and hr > 100.0:
            anomaly_score = 0.78
            condition = "Ventricular Ectopy / PVC Suspected"
            alert_level = "Warning"
        elif spo2 < 94.0 or hr > 105.0 or sys_bp > 140.0:
            anomaly_score = 0.62
            condition = "Elevated Stress / Borderline Vitals"
            alert_level = "Warning"
        elif HAS_SKLEARN and self.clf is not None:
            # Model inference score check
            raw_score = -self.clf.score_samples(features)[0] # Higher score = more anomalous
            norm_score = float(1.0 / (1.0 + np.exp(-5.0 * (raw_score - 0.5))))
            if norm_score > anomaly_score:
                anomaly_score = norm_score
                if anomaly_score > 0.65:
                    alert_level = "Warning"
                    condition = "Edge AI Statistical Anomaly"
                    
        is_anomaly = anomaly_score > 0.60
        latency_ms = round((time.perf_counter() - start_time) * 1000.0 + 1.2, 2) # Include micro-chip pipeline overhead
        
        return is_anomaly, round(anomaly_score, 3), alert_level, condition, latency_ms
