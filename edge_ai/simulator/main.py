"""
CLI Runner for Physiological Sensor Simulator

Usage Examples:
    python edge_ai/simulator/main.py
    python edge_ai/simulator/main.py --scenario LOW_SPO2
    python edge_ai/simulator/main.py --scenario FALL --patient_id P002 --count 10
"""
import argparse
import json
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.simulator.scenarios import ScenarioType

def main():
    parser = argparse.ArgumentParser(description="RPM Edge AI Physiological Sensor Simulator")
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
        "--interval",
        type=float,
        default=1.0,
        help="Sampling interval in seconds between output events (default: 1.0)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of telemetry events to generate (default: 10, set 0 for continuous loop)"
    )

    args = parser.parse_args()

    simulator = PhysiologicalSensorSimulator(patient_id=args.patient_id, scenario=args.scenario)
    
    samples_generated = 0
    while True:
        event = simulator.generate_sample()
        print(json.dumps(event, indent=2))
        sys.stdout.flush()

        samples_generated += 1
        if args.count > 0 and samples_generated >= args.count:
            break

        time.sleep(args.interval)

if __name__ == "__main__":
    main()
