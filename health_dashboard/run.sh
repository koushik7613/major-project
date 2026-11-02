#!/usr/bin/env bash
# Startup script for Local Personal Health Dashboard
echo "======================================================================"
echo "  LOCAL PERSONAL HEALTH DASHBOARD WITH AI HEALTH ASSISTANT"
echo "  Vignana Bharathi Institute of Technology (VBIT) - Major Project"
echo "======================================================================"

if ! command -v python3 &> /dev/null
then
    echo "[ERROR] python3 could not be found. Please install Python 3.10+."
    exit 1
fi

echo "[*] Checking Python dependencies..."
pip install -r requirements.txt --quiet

echo "[*] Launching Health Dashboard on http://127.0.0.1:5000"
python3 app.py
