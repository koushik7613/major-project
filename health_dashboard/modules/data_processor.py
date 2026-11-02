"""
Module 2: CSV Upload and Data Processing
Handles CSV file ingestion, flexible column mapping, validation, cleaning,
missing value imputation, duplicate removal, and database persistence.
"""
import os
import re
import pandas as pd
import numpy as np
from datetime import datetime
from database import get_db_connection

# Known synonymous column headers for automatic flexible mapping
STANDARD_COLUMNS = {
    'record_date': [
        'date', 'record_date', 'timestamp', 'datetime', 'day', 'activitydate', 
        'activity_date', 'reading_date', 'recorded_date'
    ],
    'steps': [
        'steps', 'step_count', 'stepcount', 'daily_steps', 'total_steps', 
        'walk_steps', 'steps_taken'
    ],
    'resting_heart_rate': [
        'resting_heart_rate', 'resting_hr', 'resting_pulse', 'rhr', 'rest_heart_rate'
    ],
    'avg_heart_rate': [
        'avg_heart_rate', 'heart_rate', 'heartrate', 'avg_hr', 'mean_heart_rate',
        'pulse', 'pulse_rate', 'bpm', 'average_heart_rate'
    ],
    'max_heart_rate': [
        'max_heart_rate', 'max_hr', 'maximum_heart_rate', 'peak_heart_rate', 'peak_hr'
    ],
    'sleep_hours': [
        'sleep_hours', 'sleep_duration', 'sleep_hrs', 'total_sleep_hours', 
        'hours_asleep', 'sleep_time', 'time_in_bed', 'minutesasleep'
    ],
    'deep_sleep_hours': [
        'deep_sleep_hours', 'deep_sleep', 'deep_sleep_hrs', 'rem_sleep_hours'
    ],
    'active_minutes': [
        'active_minutes', 'physical_activity', 'activity_duration', 'veryactiveminutes', 
        'moderatelyactiveminutes', 'active_mins', 'exercise_minutes', 'active_time'
    ],
    'calories_burned': [
        'calories_burned', 'calories', 'total_calories', 'active_calories', 'kcal'
    ],
    'distance_km': [
        'distance_km', 'distance', 'total_distance', 'km', 'distance_walked'
    ],
    'spo2': [
        'spo2', 'oxygen_saturation', 'blood_oxygen', 'o2_sat', 'o2_saturation'
    ],
    'stress_level': [
        'stress_level', 'stress_score', 'stress', 'daily_stress'
    ]
}

def normalize_column_name(col_name: str) -> str:
    """Normalizes header string by lowercasing and stripping non-alphanumeric chars."""
    return re.sub(r'[^a-z0-9]', '', str(col_name).strip().lower())

def auto_detect_column_mapping(df_columns: list) -> dict:
    """
    Automatically detects best-match standard field names from uploaded CSV columns.
    Returns dict: {standard_name: uploaded_column_name}
    """
    mapping = {}
    normalized_uploaded = {normalize_column_name(c): c for c in df_columns}
    
    for std_key, aliases in STANDARD_COLUMNS.items():
        found = False
        for alias in aliases:
            norm_alias = normalize_column_name(alias)
            if norm_alias in normalized_uploaded:
                mapping[std_key] = normalized_uploaded[norm_alias]
                found = True
                break
        if not found:
            # Fallback fuzzy substring search
            for norm_col, orig_col in normalized_uploaded.items():
                if norm_col in [normalize_column_name(a) for a in aliases] or any(a in norm_col for a in aliases if len(a) > 4):
                    mapping[std_key] = orig_col
                    break
    return mapping

def preview_csv(file_path: str, max_rows: int = 5) -> dict:
    """
    Loads raw CSV and returns headers, sample preview rows, row count,
    and automatic mapping proposals for the UI.
    """
    try:
        df = pd.read_csv(file_path, nrows=max_rows)
        # Determine total rows safely
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            total_lines = sum(1 for _ in f) - 1
            total_lines = max(0, total_lines)
            
        columns = list(df.columns)
        auto_mapping = auto_detect_column_mapping(columns)
        
        # Format preview rows
        preview_data = df.fillna("").to_dict(orient='records')
        
        return {
            "success": True,
            "total_rows": total_lines,
            "columns": columns,
            "auto_mapping": auto_mapping,
            "preview_rows": preview_data,
            "standard_fields": list(STANDARD_COLUMNS.keys())
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to preview CSV: {str(e)}"
        }

def process_and_save_health_csv(file_path: str, user_id: int, custom_mapping: dict = None) -> dict:
    """
    Full pipeline:
    1. Read CSV.
    2. Apply column mapping.
    3. Validate mandatory fields (record_date).
    4. Clean, parse dates, cast types.
    5. Handle missing values (imputation).
    6. Deduplicate records.
    7. Store into SQLite health_records table.
    8. Record file upload history.
    """
    try:
        df = pd.read_csv(file_path)
        original_row_count = len(df)
        
        if original_row_count == 0:
            return {"success": False, "error": "The uploaded CSV file is empty."}
            
        # Determine column mapping
        mapping = custom_mapping if custom_mapping else auto_detect_column_mapping(list(df.columns))
        
        # Invert mapping: {uploaded_col: standard_col}
        inv_mapping = {v: k for k, v in mapping.items() if v and v in df.columns}
        
        # Check required fields
        if 'record_date' not in inv_mapping.values():
            return {
                "success": False,
                "error": "Required 'record_date' column could not be identified. Please map the date column."
            }
            
        # Rename mapped columns
        df_mapped = df.rename(columns=inv_mapping)
        
        # Keep only recognized standard columns
        valid_cols = [c for c in STANDARD_COLUMNS.keys() if c in df_mapped.columns]
        df_clean = df_mapped[valid_cols].copy()
        
        # 1. Parse and standardize dates to YYYY-MM-DD
        df_clean['record_date'] = pd.to_datetime(df_clean['record_date'], errors='coerce')
        # Drop rows where date cannot be parsed
        invalid_dates_count = df_clean['record_date'].isna().sum()
        df_clean = df_clean.dropna(subset=['record_date'])
        
        if len(df_clean) == 0:
            return {"success": False, "error": "No valid dates found in the date column."}
            
        df_clean['record_date'] = df_clean['record_date'].dt.strftime('%Y-%m-%d')
        
        # 2. Handle duplicates (keep most recent/last occurrence per date)
        duplicates_removed = df_clean.duplicated(subset=['record_date']).sum()
        df_clean = df_clean.drop_duplicates(subset=['record_date'], keep='last')
        
        # 3. Numeric conversions & sanitization
        numeric_cols = [
            'steps', 'resting_heart_rate', 'avg_heart_rate', 'max_heart_rate',
            'sleep_hours', 'deep_sleep_hours', 'active_minutes', 'calories_burned',
            'distance_km', 'spo2', 'stress_level'
        ]
        
        missing_values_count = 0
        for col in numeric_cols:
            if col in df_clean.columns:
                # If sleep was reported in minutes (e.g. Fitbit minutesasleep > 60), convert to hours
                if col in ['sleep_hours', 'deep_sleep_hours']:
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                    df_clean[col] = df_clean[col].apply(lambda x: x / 60.0 if pd.notnull(x) and x > 24 else x)
                else:
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                    
                col_nulls = df_clean[col].isna().sum()
                missing_values_count += int(col_nulls)
                
                # Impute missing: forward fill, backward fill, then sensible medians
                if col_nulls > 0:
                    df_clean[col] = df_clean[col].ffill().bfill()
                    # Fallback default values
                    default_vals = {
                        'steps': 6000, 'resting_heart_rate': 68.0, 'avg_heart_rate': 74.0,
                        'max_heart_rate': 120.0, 'sleep_hours': 7.2, 'deep_sleep_hours': 1.8,
                        'active_minutes': 35.0, 'calories_burned': 2100.0, 'distance_km': 4.5,
                        'spo2': 98.0, 'stress_level': 28.0
                    }
                    df_clean[col] = df_clean[col].fillna(default_vals.get(col, 0))
            else:
                # Synthesize reasonable default/derived if optional metric is missing
                if col == 'avg_heart_rate' and 'resting_heart_rate' in df_clean.columns:
                    df_clean['avg_heart_rate'] = df_clean['resting_heart_rate'] + 8.0
                elif col == 'resting_heart_rate' and 'avg_heart_rate' in df_clean.columns:
                    df_clean['resting_heart_rate'] = df_clean['avg_heart_rate'] - 8.0
                elif col == 'distance_km' and 'steps' in df_clean.columns:
                    df_clean['distance_km'] = (df_clean['steps'] * 0.00078).round(2)
                elif col == 'calories_burned' and 'steps' in df_clean.columns:
                    df_clean['calories_burned'] = (1500 + df_clean['steps'] * 0.045).round(1)
                else:
                    defaults = {
                        'steps': 0, 'resting_heart_rate': 70.0, 'avg_heart_rate': 75.0,
                        'max_heart_rate': 125.0, 'sleep_hours': 7.0, 'deep_sleep_hours': 1.5,
                        'active_minutes': 30.0, 'calories_burned': 2000.0, 'distance_km': 3.0,
                        'spo2': 98.0, 'stress_level': 25.0
                    }
                    df_clean[col] = defaults.get(col, 0)
        
        # Ensure integer fields
        df_clean['steps'] = df_clean['steps'].astype(int)
        
        # Sort chronologically
        df_clean = df_clean.sort_values(by='record_date').reset_index(drop=True)
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Log upload file
        filename = os.path.basename(file_path)
        cursor.execute("""
        INSERT INTO uploaded_files (user_id, filename, original_name, file_path, row_count, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, filename, filename, str(file_path), len(df_clean), 'processed'))
        file_id = cursor.lastrowid
        
        # Insert or replace health records
        records_to_insert = []
        for _, row in df_clean.iterrows():
            records_to_insert.append((
                user_id, file_id, str(row['record_date']),
                int(row['steps']), float(row['resting_heart_rate']),
                float(row['avg_heart_rate']), float(row['max_heart_rate']),
                float(row['sleep_hours']), float(row['deep_sleep_hours']),
                float(row['active_minutes']), float(row['calories_burned']),
                float(row['distance_km']), float(row['spo2']),
                float(row['stress_level'])
            ))
            
        cursor.executemany("""
        INSERT INTO health_records (
            user_id, file_id, record_date, steps, resting_heart_rate, avg_heart_rate,
            max_heart_rate, sleep_hours, deep_sleep_hours, active_minutes,
            calories_burned, distance_km, spo2, stress_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, record_date) DO UPDATE SET
            file_id = excluded.file_id,
            steps = excluded.steps,
            resting_heart_rate = excluded.resting_heart_rate,
            avg_heart_rate = excluded.avg_heart_rate,
            max_heart_rate = excluded.max_heart_rate,
            sleep_hours = excluded.sleep_hours,
            deep_sleep_hours = excluded.deep_sleep_hours,
            active_minutes = excluded.active_minutes,
            calories_burned = excluded.calories_burned,
            distance_km = excluded.distance_km,
            spo2 = excluded.spo2,
            stress_level = excluded.stress_level
        """, records_to_insert)
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "file_id": file_id,
            "original_rows": original_row_count,
            "processed_rows": len(df_clean),
            "duplicates_removed": int(duplicates_removed),
            "missing_values_imputed": missing_values_count,
            "date_range": {
                "start": df_clean['record_date'].min(),
                "end": df_clean['record_date'].max()
            },
            "columns_mapped": list(inv_mapping.values())
        }
    except Exception as e:
        return {"success": False, "error": f"Error during data processing: {str(e)}"}

def get_user_records_df(user_id: int) -> pd.DataFrame:
    """Returns all health records for a user as a sorted pandas DataFrame."""
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM health_records WHERE user_id = ? ORDER BY record_date ASC",
        conn, params=(user_id,)
    )
    conn.close()
    if not df.empty and 'record_date' in df.columns:
        df['record_date'] = pd.to_datetime(df['record_date'])
    return df
