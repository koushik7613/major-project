"""
Module 1 & 3: Analytics and Visualization Engine
Calculates health summaries, weekly/monthly aggregations, Pearson correlations,
and a comprehensive composite Health Vitality Score.
"""
import pandas as pd
import numpy as np
from database import get_db_connection, get_user_by_id

def calculate_health_score(df: pd.DataFrame, user_goals: dict) -> dict:
    """
    Computes a composite Health Vitality Score (0 - 100) based on:
    - Steps consistency vs user goal (30%)
    - Sleep duration & quality (25%)
    - Resting Heart Rate normality (25%)
    - Active minutes & physical movement (20%)
    """
    if df.empty:
        return {"score": 0, "status": "Insufficient Data", "color": "secondary", "breakdown": {}}
        
    recent_df = df.tail(14) # Use last 14 days
    
    # 1. Step Score (max 30 pts)
    step_goal = user_goals.get('daily_step_goal', 10000)
    avg_steps = recent_df['steps'].mean()
    step_ratio = min(1.2, avg_steps / max(1, step_goal))
    step_pts = min(30.0, step_ratio * 30.0)
    
    # 2. Sleep Score (max 25 pts)
    # Ideal adult sleep: 7.0 - 8.5 hours
    avg_sleep = recent_df['sleep_hours'].mean()
    if 7.0 <= avg_sleep <= 8.5:
        sleep_pts = 25.0
    elif 6.0 <= avg_sleep < 7.0 or 8.5 < avg_sleep <= 9.5:
        sleep_pts = 20.0
    elif 5.0 <= avg_sleep < 6.0:
        sleep_pts = 14.0
    else:
        sleep_pts = 8.0
        
    # 3. Heart Rate Score (max 25 pts)
    # Ideal resting heart rate: 60 - 75 bpm
    avg_rhr = recent_df['resting_heart_rate'].mean()
    if 58 <= avg_rhr <= 72:
        hr_pts = 25.0
    elif 50 <= avg_rhr < 58 or 72 < avg_rhr <= 80:
        hr_pts = 21.0
    elif 80 < avg_rhr <= 90:
        hr_pts = 15.0
    else:
        hr_pts = 10.0
        
    # 4. Activity Score (max 20 pts)
    act_goal = user_goals.get('active_min_goal', 45)
    avg_act = recent_df['active_minutes'].mean()
    act_ratio = min(1.2, avg_act / max(1, act_goal))
    act_pts = min(20.0, act_ratio * 20.0)
    
    total_score = round(step_pts + sleep_pts + hr_pts + act_pts)
    total_score = max(5, min(100, total_score))
    
    if total_score >= 85:
        status, color = "Optimal Health", "success"
    elif total_score >= 70:
        status, color = "Good Vitality", "info"
    elif total_score >= 55:
        status, color = "Moderate - Room for Improvement", "warning"
    else:
        status, color = "Needs Attention", "danger"
        
    return {
        "score": total_score,
        "status": status,
        "color": color,
        "breakdown": {
            "steps": {"points": round(step_pts, 1), "max": 30, "label": "Steps Consistency"},
            "sleep": {"points": round(sleep_pts, 1), "max": 25, "label": "Sleep Restfulness"},
            "heart_rate": {"points": round(hr_pts, 1), "max": 25, "label": "Cardiac Efficiency"},
            "activity": {"points": round(act_pts, 1), "max": 20, "label": "Active Lifestyle"}
        }
    }

def get_dashboard_summary(user_id: int) -> dict:
    """
    Module 1: Calculates overall KPI cards, recent activity, and goal completions.
    """
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM health_records WHERE user_id = ? ORDER BY record_date ASC",
        conn, params=(user_id,)
    )
    user = get_user_by_id(user_id)
    conn.close()
    
    if df.empty:
        return {
            "has_data": False,
            "total_records": 0,
            "message": "No health data found. Please upload a wearable CSV file to view insights."
        }
        
    user_goals = {
        'daily_step_goal': user['daily_step_goal'] if user else 10000,
        'sleep_goal_hours': user['sleep_goal_hours'] if user else 8.0,
        'active_min_goal': user['active_min_goal'] if user else 45
    }
    
    total_records = len(df)
    latest_record = df.iloc[-1].to_dict()
    
    # Calculate overall KPIs
    kpis = {
        "total_steps": int(df['steps'].sum()),
        "avg_steps": int(df['steps'].mean()),
        "avg_resting_hr": round(float(df['resting_heart_rate'].mean()), 1),
        "avg_heart_rate": round(float(df['avg_heart_rate'].mean()), 1),
        "max_heart_rate_recorded": round(float(df['max_heart_rate'].max()), 1),
        "avg_sleep_hours": round(float(df['sleep_hours'].mean()), 2),
        "avg_deep_sleep": round(float(df['deep_sleep_hours'].mean()), 2),
        "avg_active_mins": round(float(df['active_minutes'].mean()), 1),
        "total_calories": int(df['calories_burned'].sum()),
        "avg_calories": int(df['calories_burned'].mean()),
        "total_distance_km": round(float(df['distance_km'].sum()), 1),
        "avg_spo2": round(float(df['spo2'].mean()), 1),
        "avg_stress": round(float(df['stress_level'].mean()), 1)
    }
    
    # 7-day delta trends vs previous 7-day period
    trend_deltas = {}
    if len(df) >= 14:
        last_7 = df.tail(7)
        prev_7 = df.iloc[-14:-7]
        for metric in ['steps', 'resting_heart_rate', 'sleep_hours', 'active_minutes']:
            m_last = last_7[metric].mean()
            m_prev = prev_7[metric].mean()
            pct_change = round(((m_last - m_prev) / (m_prev + 1e-6)) * 100, 1)
            trend_deltas[metric] = pct_change
    else:
        for metric in ['steps', 'resting_heart_rate', 'sleep_hours', 'active_minutes']:
            trend_deltas[metric] = 0.0

    # Composite health score
    health_score = calculate_health_score(df, user_goals)
    
    # Recent 10 records for table
    recent_records = df.tail(10).sort_values(by='record_date', ascending=False).to_dict(orient='records')
    
    return {
        "has_data": True,
        "total_records": total_records,
        "date_range": {
            "start": str(df['record_date'].iloc[0])[:10],
            "end": str(df['record_date'].iloc[-1])[:10]
        },
        "latest": latest_record,
        "kpis": kpis,
        "trend_deltas": trend_deltas,
        "health_score": health_score,
        "user_goals": user_goals,
        "recent_records": recent_records
    }

def get_visualization_data(user_id: int) -> dict:
    """
    Module 3: Prepares structured series for interactive Chart.js visualizations.
    - Daily steps line chart with moving average
    - Heart rate trend (Resting, Average, Peak)
    - Sleep duration stacked/bar (Deep sleep vs light/REM)
    - Day-of-week activity breakdown (Mon - Sun)
    - Monthly statistics
    - Metric correlation matrix
    """
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM health_records WHERE user_id = ? ORDER BY record_date ASC",
        conn, params=(user_id,)
    )
    conn.close()
    
    if df.empty:
        return {"has_data": False}
        
    df['date_dt'] = pd.to_datetime(df['record_date'])
    df['day_name'] = df['date_dt'].dt.day_name()
    df['month_year'] = df['date_dt'].dt.strftime('%b %Y')
    
    # 7-day rolling averages
    df['steps_7d_ma'] = df['steps'].rolling(window=7, min_periods=1).mean().round(0)
    df['hr_7d_ma'] = df['avg_heart_rate'].rolling(window=7, min_periods=1).mean().round(1)
    
    # 1. Daily trends (dates, steps, heart rate, sleep, active)
    dates = df['record_date'].astype(str).str[:10].tolist()
    steps = df['steps'].tolist()
    steps_ma = df['steps_7d_ma'].tolist()
    
    resting_hr = df['resting_heart_rate'].round(1).tolist()
    avg_hr = df['avg_heart_rate'].round(1).tolist()
    max_hr = df['max_heart_rate'].round(1).tolist()
    
    sleep_total = df['sleep_hours'].round(2).tolist()
    sleep_deep = df['deep_sleep_hours'].round(2).tolist()
    sleep_light = (df['sleep_hours'] - df['deep_sleep_hours']).clip(lower=0).round(2).tolist()
    
    active_mins = df['active_minutes'].round(1).tolist()
    calories = df['calories_burned'].round(0).tolist()
    
    # 2. Day-of-week average comparison
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_df = df.groupby('day_name')[['steps', 'active_minutes', 'sleep_hours', 'avg_heart_rate']].mean().reindex(day_order).fillna(0)
    
    dow_data = {
        "labels": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        "steps": [round(x) for x in dow_df['steps'].tolist()],
        "active_minutes": [round(x, 1) for x in dow_df['active_minutes'].tolist()],
        "sleep_hours": [round(x, 2) for x in dow_df['sleep_hours'].tolist()],
        "avg_heart_rate": [round(x, 1) for x in dow_df['avg_heart_rate'].tolist()]
    }
    
    # 3. Monthly statistics
    monthly_df = df.groupby('month_year', sort=False)[['steps', 'sleep_hours', 'avg_heart_rate', 'calories_burned']].agg({
        'steps': 'mean',
        'sleep_hours': 'mean',
        'avg_heart_rate': 'mean',
        'calories_burned': 'mean'
    }).round(1)
    
    monthly_data = {
        "labels": monthly_df.index.tolist(),
        "avg_steps": monthly_df['steps'].tolist(),
        "avg_sleep": monthly_df['sleep_hours'].tolist(),
        "avg_hr": monthly_df['avg_heart_rate'].tolist(),
        "avg_calories": monthly_df['calories_burned'].tolist()
    }
    
    # 4. Correlation matrix between core health metrics
    corr_cols = ['steps', 'resting_heart_rate', 'sleep_hours', 'active_minutes', 'calories_burned', 'stress_level']
    corr_matrix = df[corr_cols].corr().round(2).to_dict()
    
    # Correlation pairs formatted for scatter charts
    scatter_steps_calories = [{"x": float(row['steps']), "y": float(row['calories_burned'])} for _, row in df.iterrows()]
    scatter_active_rhr = [{"x": float(row['active_minutes']), "y": float(row['resting_heart_rate'])} for _, row in df.iterrows()]
    scatter_sleep_stress = [{"x": float(row['sleep_hours']), "y": float(row['stress_level'])} for _, row in df.iterrows()]

    return {
        "has_data": True,
        "daily": {
            "dates": dates,
            "steps": steps,
            "steps_ma": steps_ma,
            "resting_hr": resting_hr,
            "avg_hr": avg_hr,
            "max_hr": max_hr,
            "sleep_total": sleep_total,
            "sleep_deep": sleep_deep,
            "sleep_light": sleep_light,
            "active_mins": active_mins,
            "calories": calories
        },
        "day_of_week": dow_data,
        "monthly": monthly_data,
        "correlations": {
            "matrix": corr_matrix,
            "metrics": ['Steps', 'Resting HR', 'Sleep Hours', 'Active Mins', 'Calories', 'Stress'],
            "scatter_steps_calories": scatter_steps_calories,
            "scatter_active_rhr": scatter_active_rhr,
            "scatter_sleep_stress": scatter_sleep_stress
        }
    }
