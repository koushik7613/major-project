"""
Unit Tests for Machine Learning Anomaly Detection (Module 4)
"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.anomaly_detector import detect_and_store_anomalies, get_stored_anomalies
from modules.data_processor import process_and_save_health_csv
from database import init_db, create_user

class TestAnomalyDetector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.user_id, _ = create_user("test_user_anom", "testanom@example.com", "pass123", "Test Anomaly User")
        sample_path = str(Path(__file__).resolve().parent.parent / 'sample_data' / 'sample_wearable_data_90days.csv')
        process_and_save_health_csv(sample_path, cls.user_id)

    def test_detect_and_store_anomalies(self):
        result = detect_and_store_anomalies(self.user_id)
        self.assertTrue(result['success'])
        self.assertGreater(result['total_anomalies'], 0)
        
        # Verify first anomaly structure
        first_anom = result['anomalies'][0]
        self.assertIn('metric_name', first_anom)
        self.assertIn('actual_value', first_anom)
        self.assertIn('baseline_value', first_anom)
        self.assertIn('deviation_pct', first_anom)
        self.assertIn('severity', first_anom)
        self.assertIn('explanation', first_anom)

    def test_get_stored_anomalies(self):
        anomalies = get_stored_anomalies(self.user_id)
        self.assertIsInstance(anomalies, list)
        self.assertGreater(len(anomalies), 0)

if __name__ == '__main__':
    unittest.main()
