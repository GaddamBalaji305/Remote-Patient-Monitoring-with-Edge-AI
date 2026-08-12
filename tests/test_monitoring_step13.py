import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from scripts.seed_database import seed
from edge_ai.inference.metrics_tracker import EdgeMetricsTracker
from edge_ai.benchmark import run_controlled_benchmark

class TestMonitoringStep13(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()
        cls.client = TestClient(app)

    def test_01_metrics_tracker_metrics_collection(self):
        """Verify EdgeMetricsTracker records latency samples and reports system stats."""
        tracker = EdgeMetricsTracker()
        tracker.record_inference(1.85, bytes_sent=520)
        tracker.record_inference(1.72, bytes_sent=520)

        summary = tracker.get_metrics_summary()
        self.assertEqual(summary["model_version"], "1.2.0-rf-edge")
        self.assertGreater(summary["model_size_kb"], 0)
        self.assertGreater(summary["cpu_usage_percent"], 0)
        self.assertGreater(summary["memory_usage_mb"], 0)
        self.assertEqual(summary["processed_samples_count"], 2)
        self.assertEqual(summary["total_network_bytes_sent"], 1040)

    def test_02_backend_monitoring_metrics_endpoint(self):
        """Verify GET /api/monitoring/metrics returns CPU, RAM, Model size, and DB sample counts."""
        res = self.client.get("/api/monitoring/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("model_version", data)
        self.assertIn("model_size_kb", data)
        self.assertIn("cpu_usage_percent", data)
        self.assertIn("memory_usage_mb", data)
        self.assertIn("average_inference_latency_ms", data)
        self.assertIn("db_vitals_count", data)
        self.assertEqual(data["connection_status"], "ONLINE")

    def test_03_controlled_benchmark_execution(self):
        """Verify run_controlled_benchmark measures empirical Edge vs Cloud performance."""
        report = run_controlled_benchmark(iterations=3)
        self.assertEqual(report["iterations"], 3)
        self.assertIn("edge_local", report)
        self.assertIn("cloud_remote", report)
        self.assertIn("performance_gain", report)
        self.assertIn("stage_breakdown", report)

        self.assertGreater(report["edge_local"]["avg_latency_ms"], 0)
        self.assertGreater(report["cloud_remote"]["avg_latency_ms"], 0)
        self.assertEqual(report["edge_local"]["network_transfer_bytes_per_sample"], 0)

    def test_04_backend_monitoring_benchmark_endpoint(self):
        """Verify GET /api/monitoring/benchmark executes live benchmark."""
        res = self.client.get("/api/monitoring/benchmark?iterations=3")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("edge_local", data)
        self.assertIn("cloud_remote", data)
        self.assertIn("performance_gain", data)

if __name__ == "__main__":
    unittest.main()
