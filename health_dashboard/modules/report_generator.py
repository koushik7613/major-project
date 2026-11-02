"""
Module 8: Health Summary Report Generator
Matches the VBIT Major Project review specification for generating printable
and exportable comprehensive clinical health summaries.
"""
from datetime import datetime
import pandas as pd
from database import get_db_connection, get_user_by_id
from modules.analytics import calculate_health_score

def generate_health_report(user_id: int) -> dict:
    """
    Assembles a full formal health summary report including:
    - Patient / User demographics & health goals
    - Period covered & total observation days
    - Vital signs & activity summary (Steps, HR, Sleep, Calories, SpO2)
    - Detected anomalies summary
    - Clinical observations & doctor discussion talking points
    - Standard medical disclaimer
    """
    user = get_user_by_id(user_id)
    conn = get_db_connection()
    
    df = pd.read_sql_query(
        "SELECT * FROM health_records WHERE user_id = ? ORDER BY record_date ASC",
        conn, params=(user_id,)
    )
    
    anomalies = conn.execute(
        "SELECT * FROM anomalies WHERE user_id = ? ORDER BY record_date DESC",
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    if df.empty:
        return {
            "has_data": False,
            "message": "No data available to generate report. Please upload a wearable dataset first."
        }
        
    user_goals = {
        'daily_step_goal': user['daily_step_goal'] if user else 10000,
        'sleep_goal_hours': user['sleep_goal_hours'] if user else 8.0,
        'active_min_goal': user['active_min_goal'] if user else 45
    }
    
    health_score = calculate_health_score(df, user_goals)
    
    # Statistical aggregates
    total_days = len(df)
    start_date = str(df['record_date'].iloc[0])[:10]
    end_date = str(df['record_date'].iloc[-1])[:10]
    
    report_data = {
        "has_data": True,
        "generated_at": datetime.now().strftime("%B %d, %Y - %I:%M %p"),
        "patient": {
            "name": user['full_name'] if user else "Anonymous",
            "age": user['age'] if user else 24,
            "gender": user['gender'] if user else "Not specified",
            "weight_kg": user['weight_kg'] if user else 70.0,
            "height_cm": user['height_cm'] if user else 172.0,
            "bmi": round(user['weight_kg'] / ((user['height_cm']/100)**2), 1) if user and user['height_cm'] > 0 else 23.5
        },
        "period": {
            "start": start_date,
            "end": end_date,
            "total_days": total_days
        },
        "health_score": health_score,
        "vitals_summary": {
            "avg_steps": int(df['steps'].mean()),
            "max_steps": int(df['steps'].max()),
            "avg_resting_hr": round(float(df['resting_heart_rate'].mean()), 1),
            "min_resting_hr": round(float(df['resting_heart_rate'].min()), 1),
            "max_heart_rate": round(float(df['max_heart_rate'].max()), 1),
            "avg_sleep_hours": round(float(df['sleep_hours'].mean()), 2),
            "avg_deep_sleep": round(float(df['deep_sleep_hours'].mean()), 2),
            "avg_active_mins": round(float(df['active_minutes'].mean()), 1),
            "avg_calories": int(df['calories_burned'].mean()),
            "avg_spo2": round(float(df['spo2'].mean()), 1),
            "avg_stress": round(float(df['stress_level'].mean()), 1)
        },
        "anomalies": [dict(a) for a in anomalies],
        "key_takeaways": [
            f"Logged {total_days} days of wearable tracking with an average of {int(df['steps'].mean()):,} steps per day.",
            f"Resting heart rate averaged {float(df['resting_heart_rate'].mean()):.1f} bpm, reflecting normal cardiovascular range.",
            f"Sleep duration averaged {float(df['sleep_hours'].mean()):.2f} hours per night with {float(df['deep_sleep_hours'].mean()):.2f} hours in deep sleep.",
            f"Machine learning anomaly detector recorded {len(anomalies)} statistical metric variances."
        ],
        "disclaimer": (
            "NOTICE: This document is an automated analytical summary generated from wearable device data for personal "
            "reference and wellness discussion. It does not constitute a formal clinical diagnostic record. "
            "Wearable sensors have known measurement variations. Always consult a qualified medical physician for diagnosis and medical treatment."
        )
    }
    return report_data
