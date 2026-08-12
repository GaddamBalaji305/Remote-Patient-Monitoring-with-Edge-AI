import numpy as np
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.simulator.scenarios import ScenarioType

ACTIVITY_MAP = {
    "RESTING": 0,
    "LIGHT_MOVEMENT": 1,
    "MODERATE_ACTIVITY": 2,
    "SUDDEN_FALL": 3,
    "INACTIVE": 4
}

# Mapping scenario enum to target 8 model classes
CLASS_MAPPING = {
    ScenarioType.NORMAL.value: "NORMAL",
    ScenarioType.TACHYCARDIA.value: "TACHYCARDIA",
    ScenarioType.BRADYCARDIA.value: "BRADYCARDIA",
    ScenarioType.LOW_SPO2.value: "LOW_SPO2",
    ScenarioType.FEVER.value: "FEVER",
    ScenarioType.ABNORMAL_RESPIRATION.value: "ABNORMAL_RESPIRATION",
    ScenarioType.FALL.value: "FALL",
    ScenarioType.CRITICAL.value: "CRITICAL",
    ScenarioType.MULTI_PARAMETER_CRITICAL.value: "CRITICAL"
}

def generate_synthetic_dataset(samples_per_scenario: int = 1000, output_csv: str = "data/edge_training_dataset.csv") -> pd.DataFrame:
    """
    Generates synthetic time-series physiological training dataset containing 12 engineered features
    across all 8 physiological target classes.
    """
    print(f"Generating synthetic training dataset ({samples_per_scenario} samples x 8 classes = {samples_per_scenario * 8} total rows)...")
    
    rows = []
    patients = ["P001", "P002", "P003", "P004", "P005"]
    
    for scenario_enum in ScenarioType:
        class_label = CLASS_MAPPING[scenario_enum.value]
        
        for p_id in patients:
            sim = PhysiologicalSensorSimulator(patient_id=p_id, scenario=scenario_enum.value)
            
            # Rolling buffers per patient stream
            hr_history = []
            spo2_history = []
            temp_history = []
            
            count_per_patient = samples_per_scenario // len(patients)
            for _ in range(count_per_patient):
                event = sim.generate_sample()
                
                hr = float(event["heart_rate"])
                spo2 = float(event["spo2"])
                temp = float(event["temperature"])
                rr = float(event["respiratory_rate"])
                sys_bp = float(event["systolic_bp"])
                dia_bp = float(event["diastolic_bp"])
                act_str = event["activity_level"]
                act_enc = ACTIVITY_MAP.get(act_str, 0)
                
                # Update history buffers
                hr_history.append(hr)
                spo2_history.append(spo2)
                temp_history.append(temp)
                
                if len(hr_history) > 10:
                    hr_history.pop(0)
                    spo2_history.pop(0)
                    temp_history.pop(0)
                    
                # Feature engineering
                hr_change = hr - hr_history[-2] if len(hr_history) > 1 else 0.0
                spo2_change = spo2 - spo2_history[-2] if len(spo2_history) > 1 else 0.0
                temp_change = temp - temp_history[-2] if len(temp_history) > 1 else 0.0
                
                rolling_hr = float(np.mean(hr_history[-5:]))
                rolling_spo2 = float(np.mean(spo2_history[-5:]))
                
                rows.append({
                    "heart_rate": hr,
                    "spo2": spo2,
                    "temperature": temp,
                    "respiratory_rate": rr,
                    "systolic_bp": sys_bp,
                    "diastolic_bp": dia_bp,
                    "activity_level": act_enc,
                    "heart_rate_change": round(hr_change, 2),
                    "spo2_change": round(spo2_change, 2),
                    "temperature_change": round(temp_change, 2),
                    "rolling_heart_rate": round(rolling_hr, 2),
                    "rolling_spo2": round(rolling_spo2, 2),
                    "class_label": class_label
                })

    df = pd.DataFrame(rows)
    
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Dataset generated successfully and saved to {output_csv} (Shape: {df.shape})")
    return df

if __name__ == "__main__":
    generate_synthetic_dataset()
