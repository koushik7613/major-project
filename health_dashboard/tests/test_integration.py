"""
End-to-End Integration Tests for Health Dashboard Web Application
Tests full workflow from session login, sample CSV ingestion,
dashboard analytics, anomaly detection, time-series forecasting,
to AI chatbot interaction and clinical report generation.
"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from database import init_db

class TestIntegrationFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_complete_user_flow(self):
        # 1. Sign in with demo credentials
        res_login = self.client.post('/login', data={'username': 'demo_user', 'password': 'demo123'}, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)

        # 2. Ingest 90-day sample wearable dataset
        res_sample = self.client.post('/api/load-sample-data')
        self.assertEqual(res_sample.status_code, 200)
        data_sample = res_sample.get_json()
        self.assertTrue(data_sample['success'])
        self.assertGreaterEqual(data_sample['processed_rows'], 80)

        # 3. Retrieve Dashboard Summary
        res_summary = self.client.get('/api/dashboard-summary')
        self.assertEqual(res_summary.status_code, 200)
        data_summary = res_summary.get_json()
        self.assertTrue(data_summary['has_data'])
        self.assertGreater(data_summary['kpis']['total_steps'], 100000)
        self.assertGreater(data_summary['health_score']['score'], 0)

        # 4. Check Visualizations API
        res_viz = self.client.get('/api/visualization-data')
        self.assertEqual(res_viz.status_code, 200)
        data_viz = res_viz.get_json()
        self.assertTrue(data_viz['has_data'])
        self.assertIn('daily', data_viz)
        self.assertIn('correlations', data_viz)

        # 5. Check Anomaly Detection API
        res_anom = self.client.get('/api/anomalies')
        self.assertEqual(res_anom.status_code, 200)
        data_anom = res_anom.get_json()
        self.assertTrue(data_anom['success'])
        self.assertGreater(len(data_anom['anomalies']), 0)

        # 6. Check Time-Series Forecasting API
        res_fc = self.client.get('/api/forecast?metric=steps&horizon=7')
        self.assertEqual(res_fc.status_code, 200)
        data_fc = res_fc.get_json()
        self.assertTrue(data_fc['success'])
        self.assertEqual(len(data_fc['forecast']['predicted']), 7)
        self.assertGreater(data_fc['evaluation']['rmse'], 0)

        # 7. Check AI Chatbot Interaction
        res_chat = self.client.post('/api/chat', json={'message': 'What are common side effects of Ibuprofen?'})
        self.assertEqual(res_chat.status_code, 200)
        data_chat = res_chat.get_json()
        self.assertTrue(data_chat['success'])
        self.assertIn('Ibuprofen', data_chat['reply'])

        # 8. Check Health Report Generation
        res_report = self.client.get('/api/health-report')
        self.assertEqual(res_report.status_code, 200)
        data_report = res_report.get_json()
        self.assertTrue(data_report['has_data'])
        self.assertIn('vitals_summary', data_report)

if __name__ == '__main__':
    unittest.main()
