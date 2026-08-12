import numpy as np
from edge_ai.signal_processing import SignalProcessor
from edge_ai.simulator import VitalSignSimulator

def test_butterworth_filter():
    processor = SignalProcessor(fs=100)
    # Create noisy 1Hz sine wave
    t = np.linspace(0, 5, 500)
    raw_signal = np.sin(2 * np.pi * 1.0 * t) + 0.5 * np.random.normal(size=500)
    
    filtered = processor.bandpass_filter(raw_signal, lowcut=0.5, highcut=35.0)
    assert len(filtered) == len(raw_signal)
    assert np.std(filtered) < np.std(raw_signal)

def test_qrs_peak_detection():
    processor = SignalProcessor(fs=100)
    sim = VitalSignSimulator("PAT-TEST", {
        "name": "Test Patient",
        "baseline_hr": 75,
        "baseline_spo2": 98,
        "baseline_sys_bp": 120,
        "baseline_dia_bp": 80,
        "baseline_temp": 36.8,
        "baseline_rr": 16,
        "edge_node_id": "EDGE-TEST",
        "status": "Normal"
    })
    
    # Generate 5 seconds of continuous 100Hz ECG waveform (500 samples)
    step_data = sim.step(t=0.0, num_samples=500)
    ecg_signal = np.array(step_data["waveforms"]["ecg"])
    
    filtered = processor.bandpass_filter(ecg_signal)
    peaks = processor.detect_qrs_peaks(filtered)
    
    # 75 BPM over 5 seconds = ~6 beats
    assert len(peaks) >= 4

def test_hrv_calculation():
    processor = SignalProcessor(fs=100)
    r_peaks = np.array([80, 160, 240, 320, 400]) # exact 800ms intervals = 75 BPM
    
    hrv = processor.calculate_hrv(r_peaks)
    assert "mean_rr_ms" in hrv
    assert "sdnn_ms" in hrv
    assert "rmssd_ms" in hrv
    assert abs(hrv["calculated_hr"] - 75.0) < 2.0
