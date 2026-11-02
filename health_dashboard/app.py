"""
Local Personal Health Dashboard with AI Health Assistant
Main Application Entry Point and API Router
"""
import os
import shutil
from pathlib import Path
from flask import (
    Flask, render_template, request, jsonify, redirect, 
    url_for, session, flash, send_from_directory
)
from werkzeug.utils import secure_filename

from config import Config
from database import init_db, get_db_connection, get_user_by_id, search_medicine
from modules.auth import auth_bp, login_required
from modules.data_processor import (
    preview_csv, process_and_save_health_csv, get_user_records_df, STANDARD_COLUMNS
)
from modules.analytics import get_dashboard_summary, get_visualization_data
from modules.anomaly_detector import detect_and_store_anomalies, get_stored_anomalies
from modules.forecaster import forecast_health_metric
from modules.chatbot import handle_chat_query, get_recent_chat_history
from modules.report_generator import generate_health_report

app = Flask(__name__)
app.config.from_object(Config)

# Register Authentication Blueprint
app.register_blueprint(auth_bp)

# Initialize database on startup
init_db()

@app.context_processor
def inject_global_vars():
    """Provides global branding and user context to all templates."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return {
        'app_name': Config.APP_NAME,
        'app_version': Config.APP_VERSION,
        'institute_name': Config.INSTITUTE_NAME,
        'current_user': user
    }

# ==========================================
# PAGE VIEWS
# ==========================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard_view'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard_view():
    user_id = session['user_id']
    summary = get_dashboard_summary(user_id)
    return render_template('dashboard.html', active_page='dashboard', summary=summary)

@app.route('/upload')
@login_required
def upload_view():
    user_id = session['user_id']
    conn = get_db_connection()
    files = conn.execute(
        "SELECT * FROM uploaded_files WHERE user_id = ? ORDER BY upload_time DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return render_template('upload.html', active_page='upload', files=files, standard_columns=STANDARD_COLUMNS)

@app.route('/analytics')
@login_required
def analytics_view():
    return render_template('analytics.html', active_page='analytics')

@app.route('/anomalies')
@login_required
def anomalies_view():
    user_id = session['user_id']
    anomalies = get_stored_anomalies(user_id)
    return render_template('anomalies.html', active_page='anomalies', anomalies=anomalies)

@app.route('/forecasting')
@login_required
def forecasting_view():
    return render_template('forecasting.html', active_page='forecasting')

@app.route('/chatbot')
@login_required
def chatbot_view():
    user_id = session['user_id']
    history = get_recent_chat_history(user_id)
    return render_template('chatbot.html', active_page='chatbot', chat_history=history)

@app.route('/report')
@login_required
def report_view():
    user_id = session['user_id']
    report = generate_health_report(user_id)
    return render_template('report.html', active_page='report', report=report)

# ==========================================
# JSON APIs
# ==========================================

@app.route('/api/upload-preview', methods=['POST'])
@login_required
def api_upload_preview():
    """Receives CSV, saves temporarily, returns preview rows and column mapping."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
        
    if not file.filename.lower().endswith('.csv'):
        return jsonify({"success": False, "error": "Only .csv format files are supported"}), 400
        
    filename = secure_filename(file.filename)
    user_id = session['user_id']
    temp_dir = Config.UPLOAD_FOLDER / f"user_{user_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"temp_{filename}"
    file.save(str(temp_path))
    
    preview_res = preview_csv(str(temp_path))
    if preview_res.get('success'):
        # Store temp path in session for final commit
        session['last_temp_upload'] = str(temp_path)
        session['last_upload_filename'] = filename
        
    return jsonify(preview_res)

@app.route('/api/process-csv', methods=['POST'])
@login_required
def api_process_csv():
    """Applies column mapping and saves health data to database."""
    temp_path = session.get('last_temp_upload')
    if not temp_path or not os.path.exists(temp_path):
        return jsonify({"success": False, "error": "Uploaded file expired or missing. Please upload again."}), 400
        
    data = request.get_json() or {}
    custom_mapping = data.get('mapping', {})
    user_id = session['user_id']
    
    result = process_and_save_health_csv(temp_path, user_id, custom_mapping)
    if result.get('success'):
        # Automatically trigger anomaly detection for up-to-date insights
        detect_and_store_anomalies(user_id)
        
    return jsonify(result)

@app.route('/api/load-sample-data', methods=['POST'])
@login_required
def api_load_sample_data():
    """One-click convenience helper: loads sample 90-day wearable dataset."""
    sample_path = Config.BASE_DIR / 'sample_data' / 'sample_wearable_data_90days.csv'
    if not sample_path.exists():
        return jsonify({"success": False, "error": "Sample dataset file not found."}), 404
        
    user_id = session['user_id']
    result = process_and_save_health_csv(str(sample_path), user_id)
    if result.get('success'):
        detect_and_store_anomalies(user_id)
        
    return jsonify(result)

@app.route('/api/dashboard-summary')
@login_required
def api_dashboard_summary():
    user_id = session['user_id']
    summary = get_dashboard_summary(user_id)
    return jsonify(summary)

@app.route('/api/visualization-data')
@login_required
def api_visualization_data():
    user_id = session['user_id']
    data = get_visualization_data(user_id)
    return jsonify(data)

@app.route('/api/run-anomaly-detection', methods=['POST'])
@login_required
def api_run_anomaly_detection():
    user_id = session['user_id']
    res = detect_and_store_anomalies(user_id)
    return jsonify(res)

@app.route('/api/anomalies')
@login_required
def api_get_anomalies():
    user_id = session['user_id']
    anomalies = get_stored_anomalies(user_id)
    return jsonify({"success": True, "anomalies": anomalies})

@app.route('/api/forecast')
@login_required
def api_get_forecast():
    user_id = session['user_id']
    metric = request.args.get('metric', 'steps')
    horizon = int(request.args.get('horizon', 7))
    res = forecast_health_metric(user_id, metric, horizon)
    return jsonify(res)

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    user_id = session['user_id']
    data = request.get_json() or {}
    message = data.get('message', '')
    if not message.strip():
        return jsonify({"success": False, "error": "Message is required."}), 400
        
    reply_data = handle_chat_query(user_id, message)
    return jsonify(reply_data)

@app.route('/api/chat-history')
@login_required
def api_chat_history():
    user_id = session['user_id']
    history = get_recent_chat_history(user_id)
    return jsonify({"success": True, "history": history})

@app.route('/api/medicine-search')
@login_required
def api_medicine_search():
    q = request.args.get('q', '')
    results = search_medicine(q)
    return jsonify({"success": True, "results": results})

@app.route('/api/health-report')
@login_required
def api_health_report():
    user_id = session['user_id']
    report = generate_health_report(user_id)
    return jsonify(report)

@app.route('/api/delete-file/<int:file_id>', methods=['POST'])
@login_required
def api_delete_file(file_id):
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM health_records WHERE file_id = ? AND user_id = ?", (file_id, user_id))
    conn.execute("DELETE FROM uploaded_files WHERE id = ? AND user_id = ?", (file_id, user_id))
    conn.commit()
    conn.close()
    
    # Re-evaluate anomalies
    detect_and_store_anomalies(user_id)
    flash("Selected dataset and its associated records have been removed.", "info")
    return redirect(url_for('upload_view'))

if __name__ == '__main__':
    print("=" * 70)
    print("  LOCAL PERSONAL HEALTH DASHBOARD WITH AI HEALTH ASSISTANT")
    print(f"  Institution: {Config.INSTITUTE_NAME}")
    print("  Server starting locally at: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host='127.0.0.1', port=5000, debug=True)
