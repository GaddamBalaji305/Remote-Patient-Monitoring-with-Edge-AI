import enum
from typing import Dict, Any

class ScenarioType(str, enum.Enum):
    NORMAL = "NORMAL"
    TACHYCARDIA = "TACHYCARDIA"
    BRADYCARDIA = "BRADYCARDIA"
    LOW_SPO2 = "LOW_SPO2"
    FEVER = "FEVER"
    ABNORMAL_RESPIRATION = "ABNORMAL_RESPIRATION"
    FALL = "FALL"
    CRITICAL = "CRITICAL"
    MULTI_PARAMETER_CRITICAL = "MULTI_PARAMETER_CRITICAL"

class ScenarioConfig:
    """
    Defines physiological target states and transition curves for each simulation scenario.
    """
    @staticmethod
    def get_scenario_targets(scenario: ScenarioType, baseline: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        targets = {
            "heart_rate": baseline["baseline_hr"],
            "spo2": baseline["baseline_spo2"],
            "temperature": baseline["baseline_temp"],
            "respiratory_rate": baseline["baseline_rr"],
            "systolic_bp": baseline["baseline_sys_bp"],
            "diastolic_bp": baseline["baseline_dia_bp"],
            "activity_level": baseline["baseline_activity"]
        }

        # Progress factor [0.0 .. 1.0] over first 10 steps
        progress = min(1.0, max(0.0, step_index / 10.0))

        if scenario == ScenarioType.NORMAL:
            pass

        elif scenario == ScenarioType.TACHYCARDIA:
            # Gradually increase HR from baseline (~75) to ~145 bpm
            targets["heart_rate"] = baseline["baseline_hr"] + progress * (145.0 - baseline["baseline_hr"])
            targets["systolic_bp"] = baseline["baseline_sys_bp"] + progress * 15.0
            targets["activity_level"] = "MODERATE_ACTIVITY" if progress > 0.5 else "LIGHT_MOVEMENT"

        elif scenario == ScenarioType.BRADYCARDIA:
            # Gradually decrease HR from baseline (~75) to ~38 bpm
            targets["heart_rate"] = baseline["baseline_hr"] - progress * (baseline["baseline_hr"] - 38.0)
            targets["systolic_bp"] = baseline["baseline_sys_bp"] - progress * 12.0
            targets["activity_level"] = "RESTING"

        elif scenario == ScenarioType.LOW_SPO2:
            # Gradually produce SpO2 desaturation: 97 -> 96 -> 95 -> 93 -> 91 -> 89 -> 87 -> 84%
            targets["spo2"] = baseline["baseline_spo2"] - progress * (baseline["baseline_spo2"] - 84.0)
            # Compensatory respiratory rate elevation
            targets["respiratory_rate"] = baseline["baseline_rr"] + progress * 10.0
            targets["heart_rate"] = baseline["baseline_hr"] + progress * 15.0

        elif scenario == ScenarioType.FEVER:
            # Gradually increase temperature from 36.8°C to 39.5°C
            targets["temperature"] = baseline["baseline_temp"] + progress * (39.5 - baseline["baseline_temp"])
            targets["heart_rate"] = baseline["baseline_hr"] + progress * 20.0
            targets["respiratory_rate"] = baseline["baseline_rr"] + progress * 6.0

        elif scenario == ScenarioType.ABNORMAL_RESPIRATION:
            # Respiratory rate spikes to 32 breaths/min (Tachypnea)
            targets["respiratory_rate"] = baseline["baseline_rr"] + progress * (32.0 - baseline["baseline_rr"])
            targets["spo2"] = baseline["baseline_spo2"] - progress * 4.0

        elif scenario == ScenarioType.FALL:
            # Step progression: 0-2 (RESTING/LIGHT_MOVEMENT) -> 3 (SUDDEN_FALL) -> 4+ (INACTIVE)
            if step_index < 2:
                targets["activity_level"] = "LIGHT_MOVEMENT"
            elif step_index == 2 or step_index == 3:
                targets["activity_level"] = "SUDDEN_FALL"
                targets["heart_rate"] = baseline["baseline_hr"] + 40.0
                targets["systolic_bp"] = baseline["baseline_sys_bp"] + 25.0
            else:
                targets["activity_level"] = "INACTIVE"
                targets["heart_rate"] = baseline["baseline_hr"] + 20.0

        elif scenario in (ScenarioType.CRITICAL, ScenarioType.MULTI_PARAMETER_CRITICAL):
            # Severe multi-vital collapse
            targets["spo2"] = baseline["baseline_spo2"] - progress * (baseline["baseline_spo2"] - 82.0)
            targets["heart_rate"] = baseline["baseline_hr"] + progress * (150.0 - baseline["baseline_hr"])
            targets["systolic_bp"] = baseline["baseline_sys_bp"] + progress * 45.0
            targets["diastolic_bp"] = baseline["baseline_dia_bp"] + progress * 25.0
            targets["respiratory_rate"] = baseline["baseline_rr"] + progress * 14.0
            targets["temperature"] = baseline["baseline_temp"] + progress * 1.8
            targets["activity_level"] = "MODERATE_ACTIVITY" if progress < 0.5 else "INACTIVE"

        return targets
