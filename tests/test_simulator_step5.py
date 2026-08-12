import unittest
from edge_ai.simulator.sensor_simulator import PhysiologicalSensorSimulator
from edge_ai.simulator.scenarios import ScenarioType

class TestSimulatorStep5(unittest.TestCase):
    def test_01_normal_scenario(self):
        """Verify NORMAL scenario generates physiologically stable vital signs."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="NORMAL")
        sample = sim.generate_sample()
        
        self.assertEqual(sample["patient_id"], "P001")
        self.assertGreaterEqual(sample["heart_rate"], 60)
        self.assertLessEqual(sample["heart_rate"], 100)
        self.assertGreaterEqual(sample["spo2"], 95)
        self.assertEqual(sample["activity_level"], "RESTING")

    def test_02_tachycardia_scenario(self):
        """Verify TACHYCARDIA scenario produces progressive heart rate elevation."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="TACHYCARDIA")
        samples = [sim.generate_sample() for _ in range(12)]
        
        initial_hr = samples[0]["heart_rate"]
        final_hr = samples[-1]["heart_rate"]
        self.assertGreater(final_hr, initial_hr)
        self.assertGreaterEqual(final_hr, 125)

    def test_03_bradycardia_scenario(self):
        """Verify BRADYCARDIA scenario produces progressive heart rate drop."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="BRADYCARDIA")
        samples = [sim.generate_sample() for _ in range(12)]
        
        initial_hr = samples[0]["heart_rate"]
        final_hr = samples[-1]["heart_rate"]
        self.assertLess(final_hr, initial_hr)
        self.assertLessEqual(final_hr, 55)

    def test_04_low_spo2_scenario(self):
        """Verify LOW_SPO2 scenario produces smooth oxygen desaturation curve."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="LOW_SPO2")
        samples = [sim.generate_sample() for _ in range(12)]
        
        spo2_values = [s["spo2"] for s in samples]
        # Confirm general downward desaturation trend (e.g. 97 down to <= 88)
        self.assertGreater(spo2_values[0], spo2_values[-1])
        self.assertLessEqual(spo2_values[-1], 88)

    def test_05_fever_scenario(self):
        """Verify FEVER scenario produces smooth temperature elevation."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="FEVER")
        samples = [sim.generate_sample() for _ in range(12)]
        
        initial_temp = samples[0]["temperature"]
        final_temp = samples[-1]["temperature"]
        self.assertGreater(final_temp, initial_temp)
        self.assertGreaterEqual(final_temp, 38.5)

    def test_06_abnormal_respiration_scenario(self):
        """Verify ABNORMAL_RESPIRATION scenario produces elevated respiratory rate."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="ABNORMAL_RESPIRATION")
        samples = [sim.generate_sample() for _ in range(12)]
        
        final_rr = samples[-1]["respiratory_rate"]
        self.assertGreaterEqual(final_rr, 26)

    def test_07_fall_scenario(self):
        """Verify FALL scenario transitions from movement to SUDDEN_FALL to INACTIVE."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="FALL")
        samples = [sim.generate_sample() for _ in range(6)]
        
        activities = [s["activity_level"] for s in samples]
        self.assertIn("SUDDEN_FALL", activities)
        self.assertIn("INACTIVE", activities)

    def test_08_multi_parameter_critical_scenario(self):
        """Verify MULTI_PARAMETER_CRITICAL produces multi-vital collapse."""
        sim = PhysiologicalSensorSimulator(patient_id="P001", scenario="MULTI_PARAMETER_CRITICAL")
        samples = [sim.generate_sample() for _ in range(12)]
        final = samples[-1]
        
        self.assertLessEqual(final["spo2"], 88)
        self.assertGreaterEqual(final["heart_rate"], 130)
        self.assertGreaterEqual(final["systolic_bp"], 150)

    def test_09_physiological_plausibility_bounds(self):
        """Verify all generated parameters remain within valid human physiological bounds."""
        for scen in ScenarioType:
            sim = PhysiologicalSensorSimulator(patient_id="P001", scenario=scen.value)
            for _ in range(5):
                s = sim.generate_sample()
                self.assertTrue(30 <= s["heart_rate"] <= 220)
                self.assertTrue(70 <= s["spo2"] <= 100)
                self.assertTrue(34.0 <= s["temperature"] <= 42.0)
                self.assertTrue(4 <= s["respiratory_rate"] <= 50)
                self.assertTrue(60 <= s["systolic_bp"] <= 240)
                self.assertTrue(40 <= s["diastolic_bp"] <= 140)

if __name__ == "__main__":
    unittest.main()
