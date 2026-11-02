"""
Local Personal Health Dashboard Configuration
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'health-dashboard-super-secure-key-vbit-2026')
    
    # Project Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / 'data'
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH = DATA_DIR / 'health_dashboard.db'
    
    # Upload Settings
    UPLOAD_FOLDER = DATA_DIR / 'uploads'
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    ALLOWED_EXTENSIONS = {'csv'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # AI Chatbot API configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    
    # Application settings
    APP_NAME = "Local Personal Health Dashboard"
    APP_VERSION = "2.0.0"
    INSTITUTE_NAME = "Vignana Bharathi Institute of Technology (VBIT)"
    PROJECT_TITLE = "Local Personal Health Dashboard with AI Health Assistant"
