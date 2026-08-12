"""
Edge AI Integrated Pipeline Runner with Offline-First Store-and-Forward Resiliency

Connects:
Sensor Simulator → Edge Preprocessing → Edge AI Model → Risk Engine → [Backend Online / SQLite Offline Queue] → Sync

Usage Examples:
    python edge_ai/run.py
    python edge_ai/run.py --scenario LOW_SPO2
    python edge_ai/run.py --scenario FALL --patient_id P002 --count 5
"""
import argparse
import json
import sys
import os
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.simulator.scenarios import ScenarioType
from edge_ai.inference.predictor import EdgePredictor
from edge_ai.inference.risk_engine import RiskEngine
from edge_ai.offline_queue import OfflineQueue

def post_event_to_backend(url: str, payload: dict, timeout: float = 3.0) -> dict:
    """Attempts HTTP POST of telemetry event payload to Backend API."""
    json_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=json_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def flush_offline_queue(queue: OfflineQueue, url: str) -> int:
    """Flushes pending offline queued events to backend API upon reconnection."""
    pending = queue.get_pending_events(limit=50)
    if not pending:
        return 0

    print(f"   [RECONNECTING] Synchronizing {len(pending)} pending offline events to Backend...")
    synced_count = 0

    for ev in pending:
        payload = {
            "patient_id": ev["patient_id"],
            "timestamp": ev["timestamp"],
            "vitals": ev["vitals"],
            "prediction": ev["prediction"],
            "inference_latency": ev["inference_latency"]
        }
        try:
            resp_body = post_event_to_backend(url, payload, timeout=3.0)
            queue.mark_synced(ev["id"])
            synced_count += 1
        except Exception as e:
            print(f"      [SYNC RETRY PAUSED] Backend error during sync ({e}). Will retry next loop.")
            break

    print(f"   [RECONNECTED] Successfully synchronized {synced_count}/{len(pending)} offline events.\n")
    return synced_count

def main():
    parser = argparse.ArgumentParser(description="RPM Edge AI Continuous Streaming Pipeline")
    parser.add_argument(
        "--scenario",
        type=str,
        default="NORMAL",
        choices=[s.value for s in ScenarioType],
        help="Physiological scenario to simulate (default: NORMAL)"
    )
    parser.add_argument(
        "--patient_id",
        type=str,
        default="P001",
        help="Target patient ID (default: P001)"
    )
    parser.add_argument(
        "--backend_url",
        type=str,
        default="http://127.0.0.1:8000/api/edge/events",
        help="Backend API ingestion endpoint URL (default: http://127.0.0.1:8000/api/edge/events)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Interval in seconds between telemetry samples (default: 1.0)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of events to process (default: 10, set 0 for continuous loop)"
    )

    args = parser.parse_args()

    print(f"\n=======================================================")
    print(f"   STARTING OFFLINE-FIRST EDGE AI PIPELINE RUNNER      ")
    print(f"=======================================================")
    print(f"Target Patient ID:   {args.patient_id}")
    print(f"Selected Scenario:   {args.scenario}")
    print(f"Backend Endpoint:    {args.backend_url}")
    print(f"Offline Storage:     SQLite (edge_ai/data/offline_queue.db)")
    print(f"Processing Count:    {'Continuous' if args.count == 0 else args.count}")
    print(f"=======================================================\n")

    # 1. Initialize Edge Components & Offline Storage Queue
    simulator = PhysiologicalSensorSimulator(patient_id=args.patient_id, scenario=args.scenario)
    predictor = EdgePredictor(model_path="edge_ai/models/edge_random_forest.joblib")
    risk_engine = RiskEngine(medium_risk_threshold=0.35, high_risk_threshold=0.70)
    queue = OfflineQueue()

    events_processed = 0

    while True:
        # Step 1: Flush pending offline queue if backend is reachable
        if queue.get_queue_count() > 0:
            flush_offline_queue(queue, args.backend_url)

        # Step 2: Generate Raw Sensor Telemetry Event
        sensor_event = simulator.generate_sample()
        
        # Step 3: Preprocess & Execute Real Edge AI Model Inference
        pred_res = predictor.predict(sensor_event)
        
        # Step 4: Calculate Clinical Risk Category
        risk_res = risk_engine.evaluate_risk(pred_res)

        # Step 5: Compile Backend Ingestion Payload
        payload = {
            "patient_id": args.patient_id,
            "timestamp": sensor_event["timestamp"],
            "vitals": {
                "heart_rate": sensor_event["heart_rate"],
                "spo2": sensor_event["spo2"],
                "temperature": sensor_event["temperature"],
                "respiratory_rate": sensor_event["respiratory_rate"],
                "systolic_bp": sensor_event["systolic_bp"],
                "diastolic_bp": sensor_event["diastolic_bp"],
                "activity_level": sensor_event["activity_level"]
            },
            "prediction": {
                "label": pred_res["prediction"],
                "risk_score": pred_res["risk_score"],
                "confidence": pred_res["confidence"]
            },
            "inference_latency": pred_res["inference_latency_ms"]
        }

        # Step 6: Print Edge Pipeline Processing Log
        print(f"[EDGE EVENT #{events_processed + 1}] Patient {args.patient_id} | "
              f"HR: {sensor_event['heart_rate']} bpm, SpO2: {sensor_event['spo2']}%, Temp: {sensor_event['temperature']} C | "
              f"Edge AI: {pred_res['prediction']} (Risk: {pred_res['risk_score']:.2f}, Latency: {pred_res['inference_latency_ms']}ms)")

        # Step 7: Transmit Result to Backend or Enqueue Locally
        try:
            resp_body = post_event_to_backend(args.backend_url, payload, timeout=2.5)
            alert_info = f"Alert ID: {resp_body['alert_id']}" if resp_body.get('alert_created') else "None"
            print(f"   [MODE: ONLINE] HTTP 201 | Vital DB ID: {resp_body['vital_reading_id']} | "
                  f"Alert Created: {resp_body['alert_created']} ({alert_info})\n")
        except Exception as e:
            # Backend is unavailable -> Enqueue locally in SQLite Offline Queue
            event_id = queue.enqueue(
                patient_id=args.patient_id,
                timestamp=sensor_event["timestamp"],
                vitals=payload["vitals"],
                prediction=payload["prediction"],
                inference_latency=pred_res["inference_latency_ms"]
            )
            print(f"   [MODE: OFFLINE] Backend unavailable ({type(e).__name__}). Event enqueued locally in SQLite (ID: {event_id}, Pending: {queue.get_queue_count()})\n")

        events_processed += 1
        if args.count > 0 and events_processed >= args.count:
            break

        time.sleep(args.interval)

    # Final check: Flush any remaining queue if reachable
    if queue.get_queue_count() > 0:
        flush_offline_queue(queue, args.backend_url)

    print("=======================================================")
    print(f"Completed processing {events_processed} telemetry events.")
    print(f"Pending Offline Queue Depth: {queue.get_queue_count()}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
