import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_signal_processing import test_butterworth_filter, test_qrs_peak_detection, test_hrv_calculation
from tests.test_edge_ai_model import test_normal_vitals_prediction, test_hypoxia_anomaly_detection
from tests.test_backend_step2 import TestBackendStep2
from tests.test_auth_step3 import TestAuthStep3
from tests.test_patients_step4 import TestPatientsStep4
from tests.test_simulator_step5 import TestSimulatorStep5
from tests.test_model_step6 import TestModelStep6
from tests.test_integration_step7 import TestIntegrationStep7
from tests.test_websockets_step8 import TestWebSocketsStep8
from tests.test_patient_page_step10 import TestPatientPageStep10
from tests.test_alerts_step11 import TestAlertsStep11
from tests.test_offline_edge_step12 import TestOfflineEdgeStep12
from tests.test_monitoring_step13 import TestMonitoringStep13
from tests.test_security_step14 import TestSecurityStep14
from tests.test_full_pipeline_step15 import TestFullPipelineStep15
from tests.test_docker_step16 import TestDockerStep16
from tests.test_demo_step17 import TestDemoStep17

class TestRPMEdgeAISignal(unittest.TestCase):
    def test_butterworth(self):
        test_butterworth_filter()

    def test_qrs(self):
        test_qrs_peak_detection()

    def test_hrv(self):
        test_hrv_calculation()

    def test_edge_normal(self):
        test_normal_vitals_prediction()

    def test_edge_hypoxia(self):
        test_hypoxia_anomaly_detection()

if __name__ == "__main__":
    unittest.main()
