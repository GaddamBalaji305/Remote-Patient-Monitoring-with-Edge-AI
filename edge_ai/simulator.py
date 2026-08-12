import numpy as np
import time
from typing import Dict, Any, List

class VitalSignSimulator:
    """
    Generates realistic high-frequency continuous ECG and PPG waveforms
    along with multi-parameter digital vital sign readings for synthetic patients.
    Supports real-time state manipulation to inject medical anomalies on demand.
    """
    def __init__(self, patient_id: str, baseline_vitals: Dict[str, Any]):
        self.patient_id = patient_id
        self.baseline = baseline_vitals
        self.current_state = baseline_vitals.get("status", "Normal")
        
        # State override for simulation controls
        self.active_anomaly = "None" # "None", "Arrhythmia", "Hypoxia", "Hypertension", "SensorDisconnect"
        self.phase = 0.0
        
    def set_anomaly(self, anomaly_type: str):
        self.active_anomaly = anomaly_type

    def generate_ecg_point(self, t: float, hr_bpm: float) -> float:
        """
        Generates realistic ECG P-Q-R-S-T wave mathematically.
        t: current timestamp in seconds
        """
        if self.active_anomaly == "SensorDisconnect":
            return float(np.random.normal(0.0, 0.02))
            
        freq = hr_bpm / 60.0
        phase = (t * freq) % 1.0
        
        # Cardiac waveform components
        # P-wave (Atrial depolarization): small positive bump at ~0.1 phase
        p_wave = 0.15 * np.exp(-((phase - 0.12) / 0.03) ** 2)
        # Q-wave: small negative deflection at ~0.22
        q_wave = -0.15 * np.exp(-((phase - 0.22) / 0.01) ** 2)
        # R-wave (Ventricular depolarization): tall sharp positive peak at ~0.25
        r_height = 1.2 if self.active_anomaly != "Arrhythmia" else (1.6 if np.random.rand() > 0.4 else 0.4)
        r_wave = r_height * np.exp(-((phase - 0.25) / 0.012) ** 2)
        # S-wave: sharp negative deflection right after R at ~0.28
        s_wave = -0.35 * np.exp(-((phase - 0.28) / 0.015) ** 2)
        # T-wave (Ventricular repolarization): medium positive bump at ~0.45
        t_wave = 0.3 * np.exp(-((phase - 0.45) / 0.05) ** 2)
        
        # Additional baseline noise & muscle artifact
        noise = np.random.normal(0.0, 0.02)
        
        # Premature Ventricular Contraction (PVC) irregularity injection
        if self.active_anomaly == "Arrhythmia" and (phase > 0.6 and phase < 0.75) and np.random.rand() > 0.6:
            pvc_wave = 0.9 * np.exp(-((phase - 0.68) / 0.02) ** 2) - 0.4 * np.exp(-((phase - 0.71) / 0.02) ** 2)
            return float(p_wave + q_wave + r_wave + s_wave + t_wave + pvc_wave + noise)
            
        return float(p_wave + q_wave + r_wave + s_wave + t_wave + noise)

    def generate_ppg_point(self, t: float, hr_bpm: float) -> float:
        """
        Generates realistic Photoplethysmogram (PPG) pulse wave.
        """
        if self.active_anomaly == "SensorDisconnect":
            return float(np.random.normal(0.0, 0.01))
            
        freq = hr_bpm / 60.0
        phase = (t * freq) % 1.0
        
        # Systolic peak + Dicrotic notch
        sys_peak = 0.8 * np.exp(-((phase - 0.3) / 0.08) ** 2)
        dicrotic = 0.3 * np.exp(-((phase - 0.5) / 0.06) ** 2)
        noise = np.random.normal(0.0, 0.01)
        
        return float(sys_peak + dicrotic + noise)

    def get_current_vitals(self) -> Dict[str, float]:
        return self.baseline

    def step(self, t: float, num_samples: int = 100) -> Dict[str, Any]:
        """
        Generates a 1-second batch of telemetry & waveforms for the patient.
        """
        # Determine current target vitals based on anomaly injection state
        target_hr = float(self.baseline["baseline_hr"])
        target_spo2 = float(self.baseline["baseline_spo2"])
        target_sys = float(self.baseline["baseline_sys_bp"])
        target_dia = float(self.baseline["baseline_dia_bp"])
        target_temp = float(self.baseline["baseline_temp"])
        target_rr = float(self.baseline["baseline_rr"])
        
        if self.active_anomaly == "Arrhythmia":
            target_hr += float(np.random.uniform(25, 45))
        elif self.active_anomaly == "Hypoxia":
            target_spo2 = float(np.random.uniform(84, 89))
            target_rr += float(np.random.uniform(8, 14))
        elif self.active_anomaly == "Hypertension":
            target_sys += float(np.random.uniform(40, 60))
            target_dia += float(np.random.uniform(20, 35))
        elif self.active_anomaly == "SensorDisconnect":
            target_spo2 = 0.0
            target_hr = 0.0

        # Add minor natural random drift
        current_hr = round(float(target_hr + np.random.uniform(-1.5, 1.5)), 1)
        current_spo2 = round(float(np.clip(target_spo2 + np.random.uniform(-0.3, 0.3), 70.0, 100.0)), 1)
        current_sys = round(float(target_sys + np.random.uniform(-2, 2)), 1)
        current_dia = round(float(target_dia + np.random.uniform(-1, 1)), 1)
        current_temp = round(float(target_temp + np.random.uniform(-0.05, 0.05)), 1)
        current_rr = round(float(target_rr + np.random.uniform(-0.5, 0.5)), 1)

        # Generate high-frequency waveform arrays at 100Hz sampling rate
        dt = 0.01 # 10ms per sample at 100Hz
        ecg_points = [self.generate_ecg_point(t + i * dt, max(current_hr, 30.0)) for i in range(num_samples)]
        ppg_points = [self.generate_ppg_point(t + i * dt, max(current_hr, 30.0)) for i in range(num_samples)]
        return {
            "patient_id": self.patient_id,
            "patient_name": self.baseline["name"],
            "edge_node_id": self.baseline["edge_node_id"],
            "timestamp": time.time(),
            "active_anomaly": self.active_anomaly,
            "vitals": {
                "heart_rate": current_hr,
                "spo2": current_spo2,
                "sys_bp": current_sys,
                "dia_bp": current_dia,
                "temperature": current_temp,
                "respiratory_rate": current_rr
            },
            "waveforms": {
                "ecg": [round(val, 4) for val in ecg_points],
                "ppg": [round(val, 4) for val in ppg_points]
            }
        }
