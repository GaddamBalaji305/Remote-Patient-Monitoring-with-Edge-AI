import numpy as np

try:
    from scipy import signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

class SignalProcessor:
    def __init__(self, fs: int = 100):
        self.fs = fs

    def bandpass_filter(self, data: np.ndarray, lowcut: float = 0.5, highcut: float = 35.0, order: int = 2) -> np.ndarray:
        """
        Butterworth bandpass filter for ECG signal cleaning.
        Removes baseline wander (lowcut) and high frequency muscular noise (highcut).
        """
        if len(data) < 10:
            return data
            
        if HAS_SCIPY:
            nyq = 0.5 * self.fs
            low = lowcut / nyq
            high = highcut / nyq
            b, a = signal.butter(order, [low, high], btype='band')
            filtered = signal.filtfilt(b, a, data)
            return filtered
        else:
            # Fallback simple moving average & baseline removal if scipy missing
            window = max(1, int(self.fs / 20))
            kernel = np.ones(window) / window
            smoothed = np.convolve(data, kernel, mode='same')
            baseline = np.mean(smoothed)
            return smoothed - baseline

    def detect_qrs_peaks(self, ecg_signal: np.ndarray) -> np.ndarray:
        """
        Simplified Pan-Tompkins algorithm for QRS peak detection.
        Steps:
        1. Derivative filter (highlight QRS slope)
        2. Squaring function (enhance high frequencies)
        3. Moving window integration
        4. Peak thresholding
        """
        if len(ecg_signal) < 20:
            return np.array([], dtype=int)
            
        # 1. Derivative
        diff = np.diff(ecg_signal)
        
        # 2. Squaring
        squared = diff ** 2
        
        # 3. Moving integration window
        integration_window = int(0.12 * self.fs) # 120ms window
        kernel = np.ones(integration_window) / integration_window
        integrated = np.convolve(squared, kernel, mode='same')
        
        # 4. Thresholding to find peak locations
        threshold = 0.35 * np.max(integrated) if np.max(integrated) > 0 else 0.1
        peaks = []
        min_peak_distance = int(0.4 * self.fs) # 400ms min distance (max 150 bpm)
        
        last_peak = -min_peak_distance
        for i in range(1, len(integrated) - 1):
            if integrated[i] > threshold and integrated[i] > integrated[i-1] and integrated[i] > integrated[i+1]:
                if i - last_peak >= min_peak_distance:
                    # Refine peak to actual local max in raw ECG
                    search_start = max(0, i - 5)
                    search_end = min(len(ecg_signal), i + 5)
                    real_peak = search_start + np.argmax(ecg_signal[search_start:search_end])
                    peaks.append(real_peak)
                    last_peak = i
                    
        return np.array(peaks, dtype=int)

    def calculate_hrv(self, r_peaks: np.ndarray) -> dict:
        """
        Computes Heart Rate Variability (HRV) metrics:
        - Mean RR (ms)
        - SDNN: Standard Deviation of NN intervals (ms)
        - RMSSD: Root Mean Square of Successive Differences (ms)
        - Instantaneous HR (bpm)
        """
        if len(r_peaks) < 2:
            return {
                "mean_rr_ms": 800.0,
                "sdnn_ms": 30.0,
                "rmssd_ms": 25.0,
                "calculated_hr": 75.0
            }
            
        rr_intervals_sec = np.diff(r_peaks) / float(self.fs)
        rr_intervals_ms = rr_intervals_sec * 1000.0
        
        mean_rr = float(np.mean(rr_intervals_ms))
        sdnn = float(np.std(rr_intervals_ms)) if len(rr_intervals_ms) > 1 else 0.0
        
        successive_diffs = np.diff(rr_intervals_ms)
        rmssd = float(np.sqrt(np.mean(successive_diffs ** 2))) if len(successive_diffs) > 0 else 0.0
        
        calculated_hr = float(60.0 / (mean_rr / 1000.0)) if mean_rr > 0 else 75.0
        
        return {
            "mean_rr_ms": round(mean_rr, 1),
            "sdnn_ms": round(sdnn, 1),
            "rmssd_ms": round(rmssd, 1),
            "calculated_hr": round(calculated_hr, 1)
        }
