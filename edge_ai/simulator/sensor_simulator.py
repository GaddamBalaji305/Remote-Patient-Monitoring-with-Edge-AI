import datetime
import random
import math
from typing import Dict, Any, Optional

from edge_ai.simulator.patient_profiles import get_patient_profile
from edge_ai.simulator.scenarios import ScenarioType, ScenarioConfig

class PhysiologicalSensorSimulator:
    """
    Realistic Physiological Time-Series Sensor Simulator.
    
    Generates continuous multi-parameter telemetry (HR, SpO2, Temp, RR, BP, Activity)
    with smooth state evolution across normal and critical scenarios.
    
    Academic Simulation Notice:
    Data produced by this simulator is intended for academic research, demonstration,
    and algorithm testing purposes only and is not clinically validated.
    """
    def __init__(self, patient_id: str = "P001", scenario: Any = "NORMAL", baseline: Optional[Dict[str, Any]] = None):
        self.patient_id = patient_id
        
        # Backward compatibility for legacy tests passing baseline dict as 2nd arg
        if isinstance(scenario, dict):
            baseline = scenario
            scenario = "NORMAL"
            
        self.patient_profile = baseline or get_patient_profile(patient_id)
        
        try:
            self.scenario = ScenarioType(str(scenario).upper())
        except ValueError:
            self.scenario = ScenarioType.NORMAL
            
        self.step_index = 0
        
        # Initialize current state to patient baseline
        self.current_hr = float(self.patient_profile.get("baseline_hr", 75.0))
        self.current_spo2 = float(self.patient_profile.get("baseline_spo2", 98.0))
        self.current_temp = float(self.patient_profile.get("baseline_temp", 36.8))
        self.current_rr = float(self.patient_profile.get("baseline_rr", 16.0))
        self.current_sys_bp = float(self.patient_profile.get("baseline_sys_bp", 120.0))
        self.current_dia_bp = float(self.patient_profile.get("baseline_dia_bp", 80.0))
        self.current_activity = str(self.patient_profile.get("baseline_activity", "RESTING"))

    def set_scenario(self, scenario: str):
        """Update active simulation scenario."""
        try:
            self.scenario = ScenarioType(scenario.upper())
            self.step_index = 0
        except ValueError:
            pass

    def generate_ecg_point(self, t: float, hr_bpm: float) -> float:
        """Generates realistic ECG P-Q-R-S-T wave mathematically."""
        freq = hr_bpm / 60.0
        phase = (t * freq) % 1.0
        p_wave = 0.15 * math.exp(-(((phase - 0.12) / 0.03) ** 2))
        q_wave = -0.15 * math.exp(-(((phase - 0.22) / 0.01) ** 2))
        r_wave = 1.2 * math.exp(-(((phase - 0.25) / 0.012) ** 2))
        s_wave = -0.35 * math.exp(-(((phase - 0.28) / 0.015) ** 2))
        t_wave = 0.3 * math.exp(-(((phase - 0.45) / 0.05) ** 2))
        return float(p_wave + q_wave + r_wave + s_wave + t_wave + random.uniform(-0.02, 0.02))

    def step(self, t: float = 0.0, num_samples: int = 100) -> Dict[str, Any]:
        """Backward-compatible high-frequency waveform step generator."""
        dt = 0.01
        ecg_points = [self.generate_ecg_point(t + i * dt, max(self.current_hr, 30.0)) for i in range(num_samples)]
        ppg_points = [float(0.8 * math.exp(-((((t + i * dt) * max(self.current_hr, 30.0) / 60.0) % 1.0 - 0.3) / 0.08) ** 2)) for i in range(num_samples)]
        
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_profile.get("name", f"Patient {self.patient_id}"),
            "edge_node_id": "EDGE-NODE-01",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp(),
            "vitals": {
                "heart_rate": self.current_hr,
                "spo2": self.current_spo2,
                "sys_bp": self.current_sys_bp,
                "dia_bp": self.current_dia_bp,
                "temperature": self.current_temp,
                "respiratory_rate": self.current_rr
            },
            "waveforms": {
                "ecg": [round(v, 4) for v in ecg_points],
                "ppg": [round(v, 4) for v in ppg_points]
            }
        }

    def generate_sample(self) -> Dict[str, Any]:
        """
        Computes the next time-step sample in the continuous physiological stream.
        Applies smooth trend interpolation towards scenario target state.
        """
        targets = ScenarioConfig.get_scenario_targets(self.scenario, self.patient_profile, self.step_index)
        
        # Smooth interpolation rate alpha = 0.25 for continuous evolving values
        alpha = 0.25
        
        # 1. Heart Rate evolution & bounds [30 .. 220]
        hr_drift = random.uniform(-0.4, 0.4)
        self.current_hr += alpha * (targets["heart_rate"] - self.current_hr) + hr_drift
        self.current_hr = max(30.0, min(220.0, self.current_hr))
        
        # 2. SpO2 evolution & bounds [70 .. 100]
        spo2_drift = random.uniform(-0.15, 0.15)
        self.current_spo2 += alpha * (targets["spo2"] - self.current_spo2) + spo2_drift
        self.current_spo2 = max(70.0, min(100.0, self.current_spo2))
        
        # 3. Temperature evolution & bounds [34.0 .. 42.0]
        temp_drift = random.uniform(-0.02, 0.02)
        self.current_temp += alpha * (targets["temperature"] - self.current_temp) + temp_drift
        self.current_temp = max(34.0, min(42.0, self.current_temp))
        
        # 4. Respiratory Rate evolution & bounds [4 .. 50]
        rr_drift = random.uniform(-0.2, 0.2)
        self.current_rr += alpha * (targets["respiratory_rate"] - self.current_rr) + rr_drift
        self.current_rr = max(4.0, min(50.0, self.current_rr))
        
        # 5. Systolic & Diastolic BP evolution [60..240 / 40..140]
        sys_drift = random.uniform(-0.5, 0.5)
        self.current_sys_bp += alpha * (targets["systolic_bp"] - self.current_sys_bp) + sys_drift
        self.current_sys_bp = max(60.0, min(240.0, self.current_sys_bp))
        
        self.current_dia_bp = self.current_sys_bp * 0.65 + random.uniform(-1.0, 1.0)
        self.current_dia_bp = max(40.0, min(140.0, self.current_dia_bp))
        
        # 6. Activity Level
        self.current_activity = targets["activity_level"]

        self.step_index += 1
        
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return {
            "patient_id": self.patient_id,
            "timestamp": timestamp_str,
            "heart_rate": int(round(self.current_hr)),
            "spo2": int(round(self.current_spo2)),
            "temperature": round(self.current_temp, 1),
            "respiratory_rate": int(round(self.current_rr)),
            "systolic_bp": int(round(self.current_sys_bp)),
            "diastolic_bp": int(round(self.current_dia_bp)),
            "activity_level": self.current_activity
        }
