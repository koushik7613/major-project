"""
Unit Tests for Data Processor (Module 2)
"""
import unittest
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.data_processor import (
    normalize_column_name, auto_detect_column_mapping, preview_csv,
    process_and_save_health_csv
)
from database import init_db, get_db_connection, create_user

class TestDataProcessor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.user_id, _ = create_user("test_user_dp", "testdp@example.com", "pass123", "Test DP User")
        cls.sample_path = str(Path(__file__).resolve().parent.parent / 'sample_data' / 'sample_wearable_data_90days.csv')

    def test_normalize_column_name(self):
        self.assertEqual(normalize_column_name("Daily Steps"), "dailysteps")
        self.assertEqual(normalize_column_name("Heart_Rate (bpm)"), "heartratebpm")
        self.assertEqual(normalize_column_name("Sleep-Hours"), "sleephours")

    def test_auto_detect_column_mapping(self):
        cols = ['ActivityDate', 'StepCount', 'HeartRate', 'SleepDuration', 'Calories']
        mapping = auto_detect_column_mapping(cols)
        self.assertEqual(mapping.get('record_date'), 'ActivityDate')
        self.assertEqual(mapping.get('steps'), 'StepCount')
        self.assertEqual(mapping.get('sleep_hours'), 'SleepDuration')

    def test_preview_csv(self):
        res = preview_csv(self.sample_path, max_rows=5)
        self.assertTrue(res['success'])
        self.assertGreaterEqual(res['total_rows'], 80)
        self.assertEqual(len(res['preview_rows']), 5)
        self.assertIn('record_date', res['auto_mapping'])

    def test_process_and_save_health_csv(self):
        res = process_and_save_health_csv(self.sample_path, self.user_id)
        self.assertTrue(res['success'])
        self.assertGreater(res['processed_rows'], 0)
        self.assertIn('date_range', res)

        # Verify records in database
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) as c FROM health_records WHERE user_id = ?", (self.user_id,)).fetchone()['c']
        conn.close()
        self.assertEqual(count, res['processed_rows'])

if __name__ == '__main__':
    unittest.main()
