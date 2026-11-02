"""
Utility Script: Generates Realistic Sample Wearable CSV Datasets
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / 'sample_data'
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
start_date = datetime.now() - timedelta(days=90)
dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(90)]

steps = []
rhr = []
avg_hr = []
max_hr = []
sleep = []
deep_sleep = []
active = []
cals = []
dist = []
spo2 = []
stress = []

for i in range(90):
    dow = (start_date + timedelta(days=i)).weekday()  # 0=Mon, 6=Sun
    base_step = 9500 if dow in [5, 6] else 8200
    st = int(np.clip(np.random.normal(base_step, 1400), 3000, 18000))
    
    rh = round(float(np.random.normal(67.5, 2.5)), 1)
    av_h = round(rh + np.random.uniform(7.0, 13.0), 1)
    mx_h = round(av_h + np.random.uniform(40.0, 65.0), 1)
    
    sl = round(float(np.clip(np.random.normal(7.35, 0.65), 4.8, 9.5)), 2)
    dsl = round(float(np.clip(sl * np.random.uniform(0.20, 0.28), 0.9, 2.4)), 2)
    
    act = round(float(np.clip(st / 210 + np.random.normal(4, 6), 18, 90)), 1)
    d = round(st * 0.00078, 2)
    c = round(1650 + (st * 0.045) + (act * 4.2), 0)
    sp = round(float(np.clip(np.random.normal(98.2, 0.5), 95.0, 99.8)), 1)
    str_lvl = round(float(np.clip(np.random.normal(28, 6), 12, 60)), 1)
    
    # Authentic real-world anomaly days:
    if i == 22:  # Acute mild viral infection / fever day
        st = 1120
        rh = 88.5
        av_h = 96.0
        mx_h = 130.0
        sl = 10.4
        dsl = 2.8
        act = 8.0
        str_lvl = 62.0
    elif i == 45:  # Strenuous outdoor hiking marathon day
        st = 23450
        rh = 63.5
        av_h = 98.0
        mx_h = 168.0
        sl = 6.2
        dsl = 1.9
        act = 145.0
        str_lvl = 48.0
    elif i == 68:  # Exam / submission deadline all-nighter
        st = 4100
        rh = 79.5
        av_h = 85.0
        mx_h = 125.0
        sl = 3.6
        dsl = 0.5
        act = 18.0
        str_lvl = 74.0
        
    steps.append(st)
    rhr.append(rh)
    avg_hr.append(av_h)
    max_hr.append(mx_h)
    sleep.append(sl)
    deep_sleep.append(dsl)
    active.append(act)
    cals.append(c)
    dist.append(d)
    spo2.append(sp)
    stress.append(str_lvl)

df_90 = pd.DataFrame({
    'record_date': dates,
    'steps': steps,
    'resting_heart_rate': rhr,
    'avg_heart_rate': avg_hr,
    'max_heart_rate': max_hr,
    'sleep_hours': sleep,
    'deep_sleep_hours': deep_sleep,
    'active_minutes': active,
    'calories_burned': cals,
    'distance_km': dist,
    'spo2': spo2,
    'stress_level': stress
})

df_90.to_csv(SAMPLE_DIR / 'sample_wearable_data_90days.csv', index=False)

# Fitbit alternative format (30 days) to test automatic column header detection
df_fitbit = pd.DataFrame({
    'ActivityDate': dates[-30:],
    'StepCount': steps[-30:],
    'HeartRate': avg_hr[-30:],
    'RestingPulse': rhr[-30:],
    'SleepDuration': sleep[-30:],
    'VeryActiveMinutes': active[-30:],
    'Calories': cals[-30:]
})
df_fitbit.to_csv(SAMPLE_DIR / 'sample_fitbit_format.csv', index=False)

print(f"Generated {len(df_90)} records in sample_wearable_data_90days.csv")
print(f"Generated {len(df_fitbit)} records in sample_fitbit_format.csv")
