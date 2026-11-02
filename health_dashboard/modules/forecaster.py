"""
Module 5: Time-Series Health Forecasting Engine
Implements autoregressive linear/ridge forecasting with weekly seasonality and polynomial trend,
evaluates forecast accuracy using Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE),
and outputs future 7-day projections with confidence bounds.
"""
import math
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from database import get_db_connection

def forecast_health_metric(user_id: int, metric_name: str = 'steps', forecast_horizon: int = 7) -> dict:
    """
    Builds a time-series forecast model for a chosen health metric:
    - 'steps' (Daily Steps)
    - 'avg_heart_rate' (Average Heart Rate)
    - 'sleep_hours' (Sleep Duration)
    - 'resting_heart_rate' (Resting Heart Rate)
    
    Returns:
    - Historical data points
    - Test set validation predictions vs actuals
    - Model evaluation metrics (RMSE, MAE)
    - 7-day future projections with upper/lower confidence bounds
    """
    valid_metrics = {
        'steps': {'label': 'Daily Steps', 'unit': 'steps', 'decimals': 0},
        'avg_heart_rate': {'label': 'Average Heart Rate', 'unit': 'bpm', 'decimals': 1},
        'resting_heart_rate': {'label': 'Resting Heart Rate', 'unit': 'bpm', 'decimals': 1},
        'sleep_hours': {'label': 'Sleep Duration', 'unit': 'hours', 'decimals': 2},
        'active_minutes': {'label': 'Active Minutes', 'unit': 'mins', 'decimals': 1}
    }
    
    if metric_name not in valid_metrics:
        metric_name = 'steps'
        
    meta = valid_metrics[metric_name]
    
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT record_date, steps, resting_heart_rate, avg_heart_rate, sleep_hours, active_minutes "
        "FROM health_records WHERE user_id = ? ORDER BY record_date ASC",
        conn, params=(user_id,)
    )
    conn.close()
    
    min_required_records = 10
    if len(df) < min_required_records:
        return {
            "success": False,
            "error": f"Insufficient data points for forecasting. Minimum {min_required_records} records required, but only {len(df)} available.",
            "metric": metric_name,
            "metric_meta": meta
        }
        
    df['date_dt'] = pd.to_datetime(df['record_date'])
    series = df[metric_name].astype(float).values
    n = len(series)
    
    # Feature engineering for time series:
    # 1. Linear & Quadratic trend (t, t^2)
    # 2. Day-of-week seasonality (sin/cos of day of week)
    # 3. Lag-1 and Lag-7 autoregressive features
    
    t = np.arange(n)
    dows = df['date_dt'].dt.day_of_week.values
    
    sin_dow = np.sin(2 * np.pi * dows / 7.0)
    cos_dow = np.cos(2 * np.pi * dows / 7.0)
    
    # Lag 1 and Lag 7 (with backward fill for early values)
    lag1 = np.roll(series, 1)
    lag1[0] = series[0]
    
    lag7 = np.roll(series, 7)
    lag7[:7] = series[:7]
    
    X = np.column_stack([
        t / n,               # Normalized linear trend
        (t / n) ** 2,        # Quadratic acceleration/deceleration
        sin_dow,             # Weekly seasonality sine
        cos_dow,             # Weekly seasonality cosine
        lag1,                # Recent momentum (lag 1)
        lag7                 # Same-day-last-week momentum (lag 7)
    ])
    
    y = series
    
    # Train / Test split (Hold out last 7 days for test evaluation, or 20% if smaller)
    test_size = min(7, max(3, int(n * 0.2)))
    train_size = n - test_size
    
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    # Fit Ridge Regression model
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    
    # Predict on test set
    y_test_pred = model.predict(X_test)
    
    # Evaluation Metrics
    rmse = float(root_mean_squared_error(y_test, y_test_pred))
    mae = float(mean_absolute_error(y_test, y_test_pred))
    
    # Standard deviation of residuals for confidence intervals
    train_preds = model.predict(X_train)
    residuals = y_train - train_preds
    residual_std = float(np.std(residuals)) + 1e-4
    
    # Refit model on entire dataset for maximum accuracy into future
    full_model = Ridge(alpha=1.0)
    full_model.fit(X, y)
    
    # Project 7 days into future
    last_date = df['date_dt'].iloc[-1]
    future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, forecast_horizon + 1)]
    future_labels = [d.strftime('%Y-%m-%d') for d in future_dates]
    
    future_t = np.arange(n, n + forecast_horizon)
    future_dows = np.array([d.day_of_week for d in future_dates])
    future_sin = np.sin(2 * np.pi * future_dows / 7.0)
    future_cos = np.cos(2 * np.pi * future_dows / 7.0)
    
    # Recursive forecasting for lags
    future_preds = []
    future_lower = []
    future_upper = []
    
    curr_series = list(series)
    for i in range(forecast_horizon):
        curr_t = (future_t[i]) / n
        curr_t2 = curr_t ** 2
        curr_sin = future_sin[i]
        curr_cos = future_cos[i]
        curr_lag1 = curr_series[-1]
        curr_lag7 = curr_series[-7] if len(curr_series) >= 7 else curr_series[0]
        
        feature_vec = np.array([[curr_t, curr_t2, curr_sin, curr_cos, curr_lag1, curr_lag7]])
        pred_val = float(full_model.predict(feature_vec)[0])
        
        # Enforce physical reality bounds (e.g. steps >= 0, heart rate >= 40, sleep >= 0)
        if metric_name == 'steps':
            pred_val = max(100.0, pred_val)
        elif metric_name in ['avg_heart_rate', 'resting_heart_rate']:
            pred_val = max(45.0, min(160.0, pred_val))
        elif metric_name == 'sleep_hours':
            pred_val = max(3.0, min(14.0, pred_val))
            
        future_preds.append(pred_val)
        curr_series.append(pred_val)
        
        # Expanding confidence interval over horizon
        uncertainty = 1.96 * residual_std * math.sqrt(1 + 0.1 * i)
        future_lower.append(max(0.0, pred_val - uncertainty))
        future_upper.append(pred_val + uncertainty)

    # Format historical series
    hist_dates = df['record_date'].astype(str).str[:10].tolist()
    hist_values = [round(v, meta['decimals']) for v in y.tolist()]
    
    # Format test evaluation for chart
    test_dates = hist_dates[train_size:]
    test_actuals = [round(v, meta['decimals']) for v in y_test.tolist()]
    test_preds = [round(v, meta['decimals']) for v in y_test_pred.tolist()]
    
    # Format forecast values
    forecast_values = [round(v, meta['decimals']) for v in future_preds]
    forecast_lower_b = [round(v, meta['decimals']) for v in future_lower]
    forecast_upper_b = [round(v, meta['decimals']) for v in future_upper]
    
    return {
        "success": True,
        "metric": metric_name,
        "metric_meta": meta,
        "evaluation": {
            "rmse": round(rmse, 2),
            "mae": round(mae, 2),
            "test_sample_size": test_size,
            "training_sample_size": train_size,
            "interpretation": f"RMSE of {rmse:.2f} {meta['unit']} indicates average prediction deviation on unseen data."
        },
        "historical": {
            "dates": hist_dates,
            "values": hist_values
        },
        "test_validation": {
            "dates": test_dates,
            "actuals": test_actuals,
            "predicted": test_preds
        },
        "forecast": {
            "dates": future_labels,
            "predicted": forecast_values,
            "lower_bound": forecast_lower_b,
            "upper_bound": forecast_upper_b
        },
        "disclaimer": "Time-series forecasts reflect statistical extrapolations of historical wearable habits and cannot anticipate acute medical events or sudden lifestyle changes."
    }
