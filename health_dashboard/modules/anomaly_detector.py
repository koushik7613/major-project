"""
Module 4: Machine Learning Anomaly Detection Engine
Uses Scikit-learn Isolation Forest algorithm supplemented with robust statistical
Z-score / IQR bounds to identify atypical patterns in wearable biometric data.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from database import get_db_connection

def detect_and_store_anomalies(user_id: int) -> dict:
    """
    Executes machine learning anomaly detection on user's health records.
    Identifies outliers across Steps, Resting HR, Sleep Duration, and Activity.
    Stores anomalies in SQLite database.
    """
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM health_records WHERE user_id = ? ORDER BY record_date ASC",
        conn, params=(user_id,)
    )
    
    if df.empty or len(df) < 7:
        conn.close()
        return {
            "success": False,
            "message": "At least 7 days of health records are required for reliable machine learning anomaly detection.",
            "anomalies": []
        }
        
    # Feature columns for multivariate Isolation Forest
    feature_cols = ['steps', 'resting_heart_rate', 'sleep_hours', 'active_minutes']
    
    # Fill any nulls just in case
    X = df[feature_cols].copy().fillna(df[feature_cols].median())
    
    # 1. Fit Isolation Forest model
    contamination_rate = min(0.12, max(0.04, 5.0 / len(df)))
    iso_model = IsolationForest(
        n_estimators=100,
        contamination=contamination_rate,
        random_state=42
    )
    
    iso_preds = iso_model.fit_predict(X) # -1 is anomaly, 1 is normal
    df['is_iso_anomaly'] = iso_preds == -1
    
    # 2. Baseline statistics (rolling 30-day or total)
    anomalies_detected = []
    
    for idx, row in df.iterrows():
        rec_date = str(row['record_date'])[:10]
        
        # Check specific metrics against user mean and standard deviation
        metrics_to_check = [
            ('resting_heart_rate', 'Resting Heart Rate', 'bpm', 55, 95),
            ('steps', 'Daily Steps', 'steps', 1000, 30000),
            ('sleep_hours', 'Sleep Duration', 'hours', 4.0, 11.0),
            ('active_minutes', 'Physical Activity', 'minutes', 5, 200)
        ]
        
        is_ml_outlier = row['is_iso_anomaly']
        
        for col_name, label, unit, abs_min, abs_max in metrics_to_check:
            actual = float(row[col_name])
            mean_val = float(df[col_name].mean())
            std_val = float(df[col_name].std()) + 1e-5
            z_score = (actual - mean_val) / std_val
            
            # Anomaly trigger criteria:
            # - Multivariate Isolation Forest flagged AND Z-score magnitude > 1.8
            # - OR extreme statistical deviation |Z-score| >= 2.3
            is_anomaly = (is_ml_outlier and abs(z_score) > 1.8) or abs(z_score) >= 2.3 or actual < abs_min or actual > abs_max
            
            if is_anomaly:
                dev_pct = round(((actual - mean_val) / (mean_val + 1e-5)) * 100, 1)
                
                # Determine severity
                if abs(z_score) >= 2.8 or abs(dev_pct) > 50:
                    severity = "High"
                elif abs(z_score) >= 2.0 or abs(dev_pct) > 30:
                    severity = "Moderate"
                else:
                    severity = "Mild"
                    
                # Generate contextual plain-language explanation
                if col_name == 'resting_heart_rate':
                    if actual > mean_val:
                        explanation = f"Resting heart rate reached {actual:.1f} {unit}, noticeably elevated by +{dev_pct}% above your normal baseline of {mean_val:.1f} {unit}. May correlate with physical fatigue, heightened stress, dehydration, or immune response."
                    else:
                        explanation = f"Resting heart rate dropped to {actual:.1f} {unit} (-{abs(dev_pct)}% below normal baseline of {mean_val:.1f} {unit}). Notable bradycardia-like dip during rest."
                elif col_name == 'steps':
                    if actual < mean_val:
                        explanation = f"Step volume decreased to {int(actual)} {unit} (-{abs(dev_pct)}% versus daily baseline of {int(mean_val)} {unit}), representing a sudden drop in daily mobility or prolonged sedentary day."
                    else:
                        explanation = f"Step volume reached {int(actual)} {unit} (+{dev_pct}% above baseline of {int(mean_val)} {unit}), an unusually strenuous active spike."
                elif col_name == 'sleep_hours':
                    if actual < mean_val:
                        explanation = f"Sleep duration curtailed to {actual:.1f} {unit} (-{abs(dev_pct)}% below average of {mean_val:.1f} {unit}). Acute sleep restriction pattern."
                    else:
                        explanation = f"Extended sleep duration of {actual:.1f} {unit} (+{dev_pct}% above baseline of {mean_val:.1f} {unit}), indicating recovery sleep after deprivation or fatigue."
                else:
                    explanation = f"Active movement recorded {actual:.1f} {unit} ({dev_pct:+}% relative to typical {mean_val:.1f} {unit})."
                    
                anomalies_detected.append({
                    "record_date": rec_date,
                    "metric_name": label,
                    "actual_value": round(actual, 1),
                    "baseline_value": round(mean_val, 1),
                    "deviation_pct": dev_pct,
                    "unit": unit,
                    "severity": severity,
                    "explanation": explanation
                })

    # Clear previous anomalies for this user and persist fresh ones
    conn.execute("DELETE FROM anomalies WHERE user_id = ?", (user_id,))
    
    for anom in anomalies_detected:
        conn.execute("""
        INSERT INTO anomalies 
        (user_id, record_date, metric_name, actual_value, baseline_value, deviation_pct, severity, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, anom['record_date'], anom['metric_name'], anom['actual_value'],
            anom['baseline_value'], anom['deviation_pct'], anom['severity'], anom['explanation']
        ))
        
    conn.commit()
    conn.close()
    
    # Sort by date descending
    anomalies_detected.sort(key=lambda x: x['record_date'], reverse=True)
    
    return {
        "success": True,
        "total_anomalies": len(anomalies_detected),
        "anomalies": anomalies_detected,
        "disclaimer": "Machine learning anomaly detection identifies statistical outliers and is strictly informational. It does not constitute medical diagnosis or clinical assessment."
    }

def get_stored_anomalies(user_id: int) -> list:
    """Retrieves stored anomalies from the database."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM anomalies WHERE user_id = ? ORDER BY record_date DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
