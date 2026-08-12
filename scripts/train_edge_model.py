"""
Script to train lightweight Edge AI anomaly detector model
"""
import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest

def train_and_save():
    print("Generating synthetic physiological training dataset...")
    # Generate 5,000 normal vital sign frames: [HR, SpO2, Sys_BP, Dia_BP, Temp, RR, SDNN]
    normal_samples = np.random.normal(
        loc=[74.0, 97.5, 122.0, 80.0, 36.8, 16.0, 35.0],
        scale=[6.0, 1.2, 8.0, 5.0, 0.3, 2.0, 6.0],
        size=(5000, 7)
    )
    
    # Generate 500 anomaly samples (Arrhythmia, Hypoxia, Hypertensive crisis)
    arrhythmia = np.random.normal(loc=[125.0, 96.0, 130.0, 85.0, 37.0, 22.0, 10.0], scale=[15.0, 2.0, 10.0, 6.0, 0.4, 3.0, 3.0], size=(250, 7))
    hypoxia = np.random.normal(loc=[95.0, 86.0, 115.0, 75.0, 36.5, 26.0, 25.0], scale=[10.0, 3.0, 8.0, 5.0, 0.3, 4.0, 5.0], size=(250, 7))
    
    X_train = np.vstack([normal_samples, arrhythmia, hypoxia])
    
    print("Training IsolationForest model for Edge deployment...")
    model = IsolationForest(n_estimators=100, contamination=0.08, random_state=42)
    model.fit(X_train)
    
    out_dir = os.path.join(os.path.dirname(__file__), "..", "edge_ai", "models")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "edge_anomaly_model.joblib")
    
    joblib.dump(model, out_path)
    print(f"Edge AI Model saved successfully to {out_path}")

if __name__ == "__main__":
    train_and_save()
