import asyncio
import json
import logging
import os
import sys
import time
import requests
from typing import Dict, List

from edge_ai.config import EdgeConfig
from edge_ai.signal_processing import SignalProcessor
from edge_ai.model import EdgeAnomalyDetector
from edge_ai.simulator import VitalSignSimulator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] EdgeAI: %(message)s")

class EdgeNodeDaemon:
    """
    Simulated Edge AI Device Node.
    Processes live vital sign streams, filters ECG waveforms, executes AI anomaly detection,
    and forwards high-value clinical alerts & telemetry to the backend.
    """
    def __init__(self, patients_file: str = "data/patients.json"):
        self.signal_processor = SignalProcessor(fs=EdgeConfig.SAMPLING_RATE_HZ)
        self.ai_model = EdgeAnomalyDetector()
        
        # Load patient profiles
        if os.path.exists(patients_file):
            with open(patients_file, "r") as f:
                patient_data = json.load(f)
        else:
            patient_data = [
                {
                    "id": "PAT-101",
                    "name": "Eleanor Vance",
                    "baseline_hr": 74,
                    "baseline_spo2": 97,
                    "baseline_sys_bp": 124,
                    "baseline_dia_bp": 82,
                    "baseline_temp": 36.8,
                    "baseline_rr": 16,
                    "edge_node_id": "EDGE-NODE-01",
                    "status": "Normal"
                }
            ]
            
        self.simulators: Dict[str, VitalSignSimulator] = {
            p["id"]: VitalSignSimulator(p["id"], p) for p in patient_data
        }
        
        self.backend_rest_url = os.getenv("BACKEND_REST_URL", "http://127.0.0.1:8000/api/v1")
        self.battery_level = 98.5
        self.start_time = time.time()

    def get_hardware_telemetry(self, avg_latency: float) -> Dict[str, Any]:
        """
        Simulates onboard edge hardware telemetry (CPU, RAM, Battery, Latency).
        """
        uptime_sec = int(time.time() - self.start_time)
        # Slowly deplete battery over simulation run
        self.battery_level = max(15.0, 98.5 - (uptime_sec / 3600.0) * 5.0)
        
        return {
            "node_id": EdgeConfig.DEVICE_MODEL,
            "battery_pct": round(self.battery_level, 1),
            "cpu_usage_pct": round(14.2 + (avg_latency * 1.5), 1),
            "ram_usage_mb": 142.8,
            "inference_latency_ms": round(avg_latency, 2),
            "packets_processed": int(uptime_sec * len(self.simulators)),
            "status": "Healthy" if self.battery_level > 20 else "Low Battery Warning"
        }

    async def run(self):
        logging.info(f"Starting Edge AI Node on device: {EdgeConfig.DEVICE_MODEL}")
        logging.info(f"Monitoring {len(self.simulators)} patient sensor nodes at {EdgeConfig.SAMPLING_RATE_HZ}Hz...")
        
        step_count = 0
        while True:
            cycle_start = time.time()
            sim_time = cycle_start
            
            telemetry_batch = []
            alerts_batch = []
            latencies = []
            
            for patient_id, sim in self.simulators.items():
                # 1. Generate 1s waveform batch & digital vitals
                raw_data = sim.step(sim_time, num_samples=EdgeConfig.NUM_SAMPLES)
                
                # 2. Digital filtering on raw ECG
                filtered_ecg = self.signal_processor.bandpass_filter(
                    raw_data["waveforms"]["ecg"],
                    lowcut=EdgeConfig.LOWPASS_CUTOFF / 70.0,
                    highcut=EdgeConfig.LOWPASS_CUTOFF
                )
                
                # 3. Peak Detection & HRV computation
                peaks = self.signal_processor.detect_qrs_peaks(filtered_ecg)
                hrv = self.signal_processor.calculate_hrv(peaks)
                
                # 4. Edge AI Anomaly Model Inference
                is_anomaly, score, alert_level, condition, latency_ms = self.ai_model.predict(
                    raw_data["vitals"], hrv
                )
                latencies.append(latency_ms)
                
                patient_telemetry = {
                    "patient_id": patient_id,
                    "patient_name": raw_data["patient_name"],
                    "edge_node_id": raw_data["edge_node_id"],
                    "timestamp": raw_data["timestamp"],
                    "vitals": raw_data["vitals"],
                    "hrv": hrv,
                    "waveforms": {
                        "ecg": filtered_ecg.tolist(),
                        "ppg": raw_data["waveforms"]["ppg"]
                    },
                    "edge_analysis": {
                        "is_anomaly": is_anomaly,
                        "anomaly_score": score,
                        "alert_level": alert_level,
                        "condition": condition,
                        "inference_latency_ms": latency_ms
                    }
                }
                telemetry_batch.append(patient_telemetry)
                
                # If critical anomaly detected, queue an alert payload
                if is_anomaly and alert_level in ["Warning", "Critical"]:
                    alerts_batch.append({
                        "patient_id": patient_id,
                        "patient_name": raw_data["patient_name"],
                        "edge_node_id": raw_data["edge_node_id"],
                        "severity": alert_level,
                        "title": f"Edge AI Alert: {condition}",
                        "description": f"{condition} flagged at Edge node (Score: {score*100:.0f}%). Vitals: HR={raw_data['vitals']['heart_rate']}, SpO2={raw_data['vitals']['spo2']}%.",
                        "timestamp": raw_data["timestamp"],
                        "acknowledged": False
                    })
            
            # Send batch to Backend REST API / Broadcaster
            avg_lat = sum(latencies) / len(latencies) if latencies else 3.5
            hardware_metrics = self.get_hardware_telemetry(avg_lat)
            
            try:
                # Transmit telemetry payload
                requests.post(
                    f"{self.backend_rest_url}/telemetry/ingest",
                    json={
                        "telemetry": telemetry_batch,
                        "alerts": alerts_batch,
                        "edge_hardware": hardware_metrics
                    },
                    timeout=0.8
                )
            except Exception:
                pass # Backend may be offline or starting up
                
            step_count += 1
            if step_count % 10 == 0:
                logging.info(f"Edge AI Loop #{step_count}: Processed {len(telemetry_batch)} patients. Avg Latency: {avg_lat:.2f}ms. Battery: {hardware_metrics['battery_pct']}%")
                
            await asyncio.sleep(1.0)

def main():
    daemon = EdgeNodeDaemon()
    asyncio.run(daemon.run())

if __name__ == "__main__":
    main()
