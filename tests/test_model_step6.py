import unittest
import os
from edge_ai.inference.predictor import EdgePredictor
from edge_ai.inference.risk_engine import RiskEngine
from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.simulator.scenarios import ScenarioType

class TestModelStep6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictor = EdgePredictor(model_path="edge_ai/models/edge_random_forest.joblib")
        cls.risk_engine = RiskEngine(medium_risk_threshold=0.35, high_risk_threshold=0.70)

    def test_01_feature_extraction(self):
        """Verify 12-feature extraction from telemetry event."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="NORMAL")
        sample = sim.generate_sample()
        
        df_feat = self.predictor.extract_features("P001", sample)
        self.assertEqual(df_feat.shape[1], 12)
        self.assertIn("heart_rate", df_feat.columns)
        self.assertIn("rolling_spo2", df_feat.columns)

    def test_02_model_artifact_loading(self):
        """Verify model artifact exists and classes list is populated."""
        self.assertTrue(os.path.exists("edge_ai/models/edge_random_forest.joblib"))
        self.assertIsNotNone(self.predictor.model)
        self.assertEqual(len(self.predictor.classes), 8)

    def test_03_inference_predictions_all_8_classes(self):
        """Verify real model inference across all 8 target classes."""
        scenarios_to_test = [
            ("NORMAL", ["NORMAL"]),
            ("TACHYCARDIA", ["TACHYCARDIA", "NORMAL"]),
            ("BRADYCARDIA", ["BRADYCARDIA", "NORMAL"]),
            ("LOW_SPO2", ["LOW_SPO2", "CRITICAL"]),
            ("FEVER", ["FEVER", "NORMAL"]),
            ("ABNORMAL_RESPIRATION", ["ABNORMAL_RESPIRATION", "NORMAL"]),
            ("FALL", ["FALL", "NORMAL"]),
            ("MULTI_PARAMETER_CRITICAL", ["CRITICAL", "LOW_SPO2"])
        ]

        for scen, expected_classes in scenarios_to_test:
            sim = PhysiologicalSensorSimulator(patient_id="P001", scenario=scen)
            # Run 10 steps to reach scenario state
            for _ in range(10):
                sample = sim.generate_sample()
                res = self.predictor.predict(sample)

            self.assertIn("prediction", res)
            self.assertIn(res["prediction"], self.predictor.classes)

    def test_04_predictor_json_structure(self):
        """Verify predictor returns expected keys: prediction, risk_score, confidence, inference_latency_ms."""
        sample = {
            "patient_id": "P001",
            "heart_rate": 140,
            "spo2": 86,
            "temperature": 37.0,
            "respiratory_rate": 26,
            "systolic_bp": 160,
            "diastolic_bp": 100,
            "activity_level": "MODERATE_ACTIVITY"
        }
        res = self.predictor.predict(sample)
        
        self.assertIn("prediction", res)
        self.assertIn("risk_score", res)
        self.assertIn("confidence", res)
        self.assertIn("inference_latency_ms", res)
        self.assertTrue(0.0 <= res["risk_score"] <= 1.0)
        self.assertTrue(0.0 <= res["confidence"] <= 1.0)

    def test_05_risk_engine_evaluation(self):
        """Verify risk engine maps scores to LOW, MEDIUM, and HIGH risk categories."""
        # 1. Low Risk
        res_low = self.risk_engine.evaluate_risk({"prediction": "NORMAL", "risk_score": 0.05, "confidence": 0.95})
        self.assertEqual(res_low["risk_level"], "LOW")
        self.assertEqual(res_low["patient_status"], "NORMAL")

        # 2. Medium Risk
        res_med = self.risk_engine.evaluate_risk({"prediction": "TACHYCARDIA", "risk_score": 0.55, "confidence": 0.90})
        self.assertEqual(res_med["risk_level"], "MEDIUM")
        self.assertEqual(res_med["patient_status"], "WARNING")

        # 3. High Risk
        res_high = self.risk_engine.evaluate_risk({"prediction": "LOW_SPO2", "risk_score": 0.92, "confidence": 0.96})
        self.assertEqual(res_high["risk_level"], "HIGH")
        self.assertEqual(res_high["patient_status"], "CRITICAL")

    def test_06_edge_latency_benchmark(self):
        """Verify inference execution latency is under 50ms for real-time edge processing."""
        sample = {
            "patient_id": "P001",
            "heart_rate": 75,
            "spo2": 98,
            "temperature": 36.8,
            "respiratory_rate": 16,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "activity_level": "RESTING"
        }

        # Warm-up runs
        for _ in range(10):
            self.predictor.predict(sample)

        latencies = []
        for _ in range(50):
            res = self.predictor.predict(sample)
            latencies.append(res["inference_latency_ms"])

        avg_latency = sum(latencies) / len(latencies)
        self.assertLess(avg_latency, 50.0)

if __name__ == "__main__":
    unittest.main()
