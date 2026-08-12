import os

class EdgeConfig:
    # Sampling parameters
    SAMPLING_RATE_HZ = int(os.getenv("EDGE_SAMPLING_RATE_HZ", "100"))
    WAVEFORM_WINDOW_SEC = 5.0  # 5 seconds waveform window (500 samples)
    NUM_SAMPLES = int(SAMPLING_RATE_HZ * WAVEFORM_WINDOW_SEC)
    
    # Filter settings
    LOWPASS_CUTOFF = 35.0  # Hz
    HIGHPASS_CUTOFF = 0.5  # Hz
    
    # Vital Sign Normal Ranges
    HR_MIN_NORMAL = 60
    HR_MAX_NORMAL = 100
    SPO2_MIN_NORMAL = 95
    SYS_BP_MAX_NORMAL = 130
    DIA_BP_MAX_NORMAL = 85
    TEMP_MAX_NORMAL = 37.5
    RR_MIN_NORMAL = 12
    RR_MAX_NORMAL = 20
    
    # AI Detection Thresholds
    ANOMALY_THRESHOLD = 0.65  # Probability > 0.65 triggers alert
    
    # Target Edge Device Specs (simulated)
    DEVICE_MODEL = "NVIDIA Jetson Orin Nano / ARM Cortex-M55"
    EDGE_TARGET_LATENCY_MS = 4.2
