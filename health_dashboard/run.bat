@echo off
title Local Personal Health Dashboard
echo ======================================================================
echo   LOCAL PERSONAL HEALTH DASHBOARD WITH AI HEALTH ASSISTANT
echo   Vignana Bharathi Institute of Technology (VBIT) - Major Project
echo ======================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

:: Ensure dependencies
echo [*] Checking dependencies...
pip install -r requirements.txt --quiet

:: Start application
echo [*] Launching application on http://127.0.0.1:5000
echo [*] Press Ctrl+C to terminate the server.
echo.
python app.py
pause
