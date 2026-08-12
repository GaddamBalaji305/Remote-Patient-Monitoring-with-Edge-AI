from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "Online"

def test_get_patients():
    response = client.get("/api/v1/patients")
    assert response.status_code == 200
    patients = response.json()
    assert isinstance(patients, list)
    assert len(patients) >= 1

def test_get_edge_metrics():
    response = client.get("/api/v1/edge/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert "battery_pct" in metrics
    assert "inference_latency_ms" in metrics

def test_simulate_anomaly():
    payload = {
        "patient_id": "PAT-101",
        "anomaly_type": "Hypoxia"
    }
    response = client.post("/api/v1/simulate/anomaly", json=payload)
    assert response.status_code == 200
    assert response.json()["active_anomaly"] == "Hypoxia"
