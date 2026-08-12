import pandas as pd
import numpy as np
import joblib
import os
import sys

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from edge_ai.training.train_model import FEATURE_COLUMNS, TARGET_COLUMN, train_edge_model

def evaluate_edge_model(
    model_path: str = "edge_ai/models/edge_random_forest.joblib",
    dataset_path: str = "data/edge_training_dataset.csv"
):
    """
    Evaluates trained Edge AI model artifact on test set and computes Accuracy,
    Precision, Recall, F1-Score, and Confusion Matrix.
    """
    if not os.path.exists(model_path):
        print("Model artifact not found. Training model first...")
        train_edge_model(dataset_path=dataset_path, model_output_path=model_path)

    artifact = joblib.load(model_path)
    model = artifact["model"]
    classes = artifact["classes"]

    if not os.path.exists(dataset_path):
        df = pd.read_csv(dataset_path)
    else:
        df = pd.read_csv(dataset_path)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    y_pred = model.predict(X)

    acc = accuracy_score(y, y_pred)
    prec_macro = precision_score(y, y_pred, average="macro", zero_division=0)
    rec_macro = recall_score(y, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y, y_pred, labels=classes)

    print("\n=======================================================")
    print("        EDGE AI MODEL EVALUATION REPORT               ")
    print("=======================================================")
    print(f"Overall Accuracy:  {acc * 100:.2f}%")
    print(f"Macro Precision:   {prec_macro * 100:.2f}%")
    print(f"Macro Recall:      {rec_macro * 100:.2f}%")
    print(f"Macro F1-Score:    {f1_macro * 100:.2f}%")
    print("\nDetailed Per-Class Performance:")
    print(classification_report(y, y_pred, target_names=classes, zero_division=0))
    print("Confusion Matrix:")
    print(pd.DataFrame(cm, index=classes, columns=classes))
    print("=======================================================\n")

    return {
        "accuracy": acc,
        "precision_macro": prec_macro,
        "recall_macro": rec_macro,
        "f1_macro": f1_macro,
        "confusion_matrix": cm.tolist(),
        "classes": classes
    }

if __name__ == "__main__":
    evaluate_edge_model()
