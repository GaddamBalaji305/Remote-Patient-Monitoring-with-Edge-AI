"""
Physiological Sensor Simulator Package
"""
__version__ = "1.0.0"

from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.simulator.patient_profiles import PATIENT_PROFILES, get_patient_profile
from edge_ai.simulator.scenarios import ScenarioType

# Alias for backwards compatibility
VitalSignSimulator = PhysiologicalSensorSimulator
