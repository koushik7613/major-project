"""
Unit Tests for Time-Series Forecasting (Module 5)
"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.forecaster import forecast_health_metric
from modules.data_processor import process_and_save_health_csv
from database import init_db, create_user

class TestForecaster(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.user_id, _ = create_user("test_user_fc", "testfc@example.com", "pass123", "Test Forecast User")
        sample_path = str(Path(__file__).resolve().parent.parent / 'sample_data' / 'sample_wearable_data_90days.csv')
        process_and_save_health_csv(sample_path, cls.user_id)

    def test_forecast_steps(self):
        res = forecast_health_metric(self.user_id, metric_name='steps', forecast_horizon=7)
        self.assertTrue(res['success'])
        self.assertEqual(len(res['forecast']['predicted']), 7)
        self.assertEqual(len(res['forecast']['lower_bound']), 7)
        self.assertEqual(len(res['forecast']['upper_bound']), 7)
        self.assertIn('rmse', res['evaluation'])
        self.assertGreater(res['evaluation']['rmse'], 0)

    def test_forecast_heart_rate(self):
        res = forecast_health_metric(self.user_id, metric_name='avg_heart_rate', forecast_horizon=7)
        self.assertTrue(res['success'])
        self.assertEqual(len(res['forecast']['predicted']), 7)
        self.assertGreater(res['forecast']['predicted'][0], 40.0)

    def test_insufficient_data_guard(self):
        # Create user with zero records
        empty_user_id, _ = create_user("test_empty_fc", "emptyfc@example.com", "pass123", "Empty User")
        res = forecast_health_metric(empty_user_id, metric_name='steps')
        self.assertFalse(res['success'])
        self.assertIn('Insufficient data', res['error'])

if __name__ == '__main__':
    unittest.main()
