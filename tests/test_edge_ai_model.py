from edge_ai.model import EdgeAnomalyDetector

def test_normal_vitals_prediction():
    detector = EdgeAnomalyDetector()
    vitals = {
        "heart_rate": 74.0,
        "spo2": 98.0,
        "sys_bp": 120.0,
        "dia_bp": 80.0,
        "temperature": 36.8,
        "respiratory_rate": 16.0
    }
    hrv = {"sdnn_ms": 35.0}
    
    is_anomaly, score, alert_level, condition, latency = detector.predict(vitals, hrv)
    assert is_anomaly is False
    assert alert_level == "Normal"
    assert latency < 20.0 # under 20ms execution time

def test_hypoxia_anomaly_detection():
    detector = EdgeAnomalyDetector()
    vitals = {
        "heart_rate": 88.0,
        "spo2": 86.0, # Acute hypoxia drop
        "sys_bp": 120.0,
        "dia_bp": 80.0,
        "temperature": 36.8,
        "respiratory_rate": 24.0
    }
    hrv = {"sdnn_ms": 25.0}
    
    is_anomaly, score, alert_level, condition, latency = detector.predict(vitals, hrv)
    assert is_anomaly is True
    assert alert_level == "Critical"
    assert condition == "Acute Hypoxia"
