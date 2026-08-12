from typing import Dict, Any

PATIENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "P001": {
        "patient_id": "P001",
        "name": "Eleanor Vance",
        "age": 68,
        "gender": "Female",
        "baseline_hr": 74.0,
        "baseline_spo2": 97.0,
        "baseline_temp": 36.8,
        "baseline_rr": 16.0,
        "baseline_sys_bp": 124.0,
        "baseline_dia_bp": 82.0,
        "baseline_activity": "RESTING"
    },
    "P002": {
        "patient_id": "P002",
        "name": "Marcus Holloway",
        "age": 54,
        "gender": "Male",
        "baseline_hr": 82.0,
        "baseline_spo2": 96.0,
        "baseline_temp": 37.0,
        "baseline_rr": 18.0,
        "baseline_sys_bp": 135.0,
        "baseline_dia_bp": 86.0,
        "baseline_activity": "RESTING"
    },
    "P003": {
        "patient_id": "P003",
        "name": "Sophia Rodriguez",
        "age": 72,
        "gender": "Female",
        "baseline_hr": 68.0,
        "baseline_spo2": 98.0,
        "baseline_temp": 36.6,
        "baseline_rr": 15.0,
        "baseline_sys_bp": 118.0,
        "baseline_dia_bp": 76.0,
        "baseline_activity": "RESTING"
    },
    "P004": {
        "patient_id": "P004",
        "name": "Dr. Arthur Pendelton",
        "age": 81,
        "gender": "Male",
        "baseline_hr": 88.0,
        "baseline_spo2": 95.0,
        "baseline_temp": 37.2,
        "baseline_rr": 19.0,
        "baseline_sys_bp": 142.0,
        "baseline_dia_bp": 90.0,
        "baseline_activity": "RESTING"
    },
    "P005": {
        "patient_id": "P005",
        "name": "Clara Oswald",
        "age": 42,
        "gender": "Female",
        "baseline_hr": 72.0,
        "baseline_spo2": 99.0,
        "baseline_temp": 36.7,
        "baseline_rr": 14.0,
        "baseline_sys_bp": 116.0,
        "baseline_dia_bp": 74.0,
        "baseline_activity": "RESTING"
    }
}

def get_patient_profile(patient_id: str) -> Dict[str, Any]:
    """Retrieves patient baseline profile or constructs default if patient_id is unlisted."""
    if patient_id in PATIENT_PROFILES:
        return PATIENT_PROFILES[patient_id].copy()
    
    return {
        "patient_id": patient_id,
        "name": f"Patient {patient_id}",
        "age": 60,
        "gender": "Unknown",
        "baseline_hr": 75.0,
        "baseline_spo2": 98.0,
        "baseline_temp": 36.8,
        "baseline_rr": 16.0,
        "baseline_sys_bp": 120.0,
        "baseline_dia_bp": 80.0,
        "baseline_activity": "RESTING"
    }
