import pandas as pd
import numpy as np
import joblib
import os
import sys

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from edge_ai.training.generate_dataset import generate_synthetic_dataset

FEATURE_COLUMNS = [
    "heart_rate",
    "spo2",
    "temperature",
    "respiratory_rate",
    "systolic_bp",
    "diastolic_bp",
    "activity_level",
    "heart_rate_change",
    "spo2_change",
    "temperature_change",
    "rolling_heart_rate",
    "rolling_spo2"
]

TARGET_COLUMN = "class_label"

def train_edge_model(
    dataset_path: str = "data/edge_training_dataset.csv",
    model_output_path: str = "edge_ai/models/edge_random_forest.joblib"
):
    """
    Training pipeline:
    Load Data -> Preprocess -> Train/Test Split (80/20) -> Fit RandomForest -> Save Model Artifact
    """
    if not os.path.exists(dataset_path):
        print("Dataset file not found. Generating fresh dataset...")
        df = generate_synthetic_dataset(output_csv=dataset_path)
    else:
        df = pd.read_csv(dataset_path)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    print(f"Splitting dataset into 80% Train and 20% Test (Total: {len(df)} samples)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print("Training RandomForestClassifier for Edge AI deployment...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, model.predict(X_test))
    
    print(f"Model Training Complete! Train Accuracy: {train_acc*100:.2f}%, Test Accuracy: {test_acc*100:.2f}%")

    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump({
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "classes": list(model.classes_)
    }, model_output_path)

    print(f"Saved trained Edge AI model artifact to {model_output_path}")
    return model, X_test, y_test

if __name__ == "__main__":
    train_edge_model()
