"""
Unit Tests for AI Health and Medicine Chatbot (Module 6)
"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.chatbot import handle_chat_query, generate_offline_clinical_response
from database import init_db, create_user

class TestChatbot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.user_id, _ = create_user("test_user_chat", "testchat@example.com", "pass123", "Test Chat User")

    def test_emergency_symptom_warning(self):
        resp = handle_chat_query(self.user_id, "I have severe chest pain and shortness of breath")
        self.assertTrue(resp['success'])
        self.assertIn("URGENT MEDICAL NOTICE", resp['reply'])
        self.assertIn("emergency", resp['reply'].lower())

    def test_medication_query(self):
        resp = handle_chat_query(self.user_id, "What are the common uses of Paracetamol?")
        self.assertTrue(resp['success'])
        self.assertIn("Paracetamol", resp['reply'])
        self.assertIn("Precautions", resp['reply'])
        self.assertIn("Disclaimer", resp['reply'])

    def test_dashboard_query(self):
        resp = handle_chat_query(self.user_id, "Analyze my dashboard data")
        self.assertTrue(resp['success'])
        self.assertIn("Dashboard", resp['reply'])

if __name__ == '__main__':
    unittest.main()
