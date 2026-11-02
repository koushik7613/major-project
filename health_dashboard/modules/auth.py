"""
Module 7: Authentication and User Profile Management
Handles secure login, registration, session management, and profile updates.
"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import (
    create_user, verify_user, get_user_by_id, update_user_profile, 
    clear_user_data, get_db_connection
)

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to protect routes requiring authenticated sessions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access your health dashboard.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('login.html', username=username)
            
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", "success")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard_view'))
        else:
            flash("Invalid username or password. Please try again.", "danger")
            return render_template('login.html', username=username)
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        age = int(request.form.get('age', 22) or 22)
        gender = request.form.get('gender', 'Other')
        weight = float(request.form.get('weight_kg', 70.0) or 70.0)
        height = float(request.form.get('height_cm', 175.0) or 175.0)
        
        if not username or not email or not password or not full_name:
            flash("All required fields must be filled.", "danger")
            return render_template('register.html')
            
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')
            
        user_id, error = create_user(username, email, password, full_name, age, gender, weight, height)
        if error:
            flash(error, "danger")
            return render_template('register.html')
            
        # Automatically log the newly registered user in
        session['user_id'] = user_id
        session['username'] = username
        session['full_name'] = full_name
        flash("Registration successful! Welcome to your Health Dashboard.", "success")
        return redirect(url_for('dashboard_view'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been safely signed out.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        age = int(request.form.get('age', 24) or 24)
        gender = request.form.get('gender', 'Other')
        weight = float(request.form.get('weight_kg', 70.0) or 70.0)
        height = float(request.form.get('height_cm', 172.0) or 172.0)
        step_goal = int(request.form.get('daily_step_goal', 10000) or 10000)
        sleep_goal = float(request.form.get('sleep_goal_hours', 8.0) or 8.0)
        active_goal = int(request.form.get('active_min_goal', 45) or 45)
        
        update_user_profile(user_id, full_name, age, gender, weight, height, step_goal, sleep_goal, active_goal)
        session['full_name'] = full_name
        flash("Health profile and wellness targets updated successfully!", "success")
        return redirect(url_for('auth.profile'))
        
    user = get_user_by_id(user_id)
    
    # Get upload files list
    conn = get_db_connection()
    files = conn.execute(
        "SELECT * FROM uploaded_files WHERE user_id = ? ORDER BY upload_time DESC",
        (user_id,)
    ).fetchall()
    record_count = conn.execute(
        "SELECT COUNT(*) as count FROM health_records WHERE user_id = ?",
        (user_id,)
    ).fetchone()['count']
    conn.close()
    
    return render_template('profile.html', user=user, files=files, record_count=record_count)

@auth_bp.route('/clear-data', methods=['POST'])
@login_required
def clear_data():
    user_id = session['user_id']
    clear_user_data(user_id)
    flash("All your uploaded health data and records have been completely cleared.", "info")
    return redirect(url_for('dashboard_view'))
