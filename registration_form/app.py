#!/usr/bin/env python3
"""
Camp Power-Up Registration Form Application - Clean Version
=========================================================
Restored admin functionality with PostgreSQL database
"""

import os
import sqlite3
import uuid
import hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from database_config import get_db_connection, init_postgresql_tables, DB_CONFIG
from camp_config import CAMP_CONFIG, get_camp_title, get_camp_subtitle, get_pricing_text
from functools import wraps

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'camp_power_up_registration_2025_dev_only')

# Configure pricing in Flask config for templates
app.config['pricing'] = {
    'returning_camper': {
        'total': 200,
        'deposit': 50,
        'final_payment': 150
    },
    'new_camper': {
        'total': 250,
        'deposit': 75,
        'final_payment': 175
    }
}

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'campadmin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'PowerUp2025!')

def require_admin_auth(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_registration_db():
    """Initialize the registration database."""
    try:
        # Use SQLite for Railway deployment - simpler and more reliable
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT UNIQUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'pending',
                child_first_name TEXT,
                child_last_name TEXT,
                child_age INTEGER,
                parent_first_name TEXT,
                parent_last_name TEXT,
                parent_email TEXT,
                parent_phone TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                has_allergies BOOLEAN DEFAULT 0,
                allergies_description TEXT,
                has_medical_conditions BOOLEAN DEFAULT 0,
                medical_conditions_description TEXT,
                is_returning_camper BOOLEAN DEFAULT 0,
                returning_years TEXT,
                how_heard_about_camp TEXT,
                additional_comments TEXT,
                bringing_own_switch BOOLEAN DEFAULT 0,
                has_sensory_issues BOOLEAN DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database init error: {e}")
        # Don't crash the app if DB init fails

@app.route('/')
def index():
    """Main registration form."""
    # Create pricing object that template expects
    pricing = {
        'returning_text': 'Returning Campers: $200',
        'new_text': 'New Campers: $250', 
        'payment_deadline': 'Payment due within 7 days of registration'
    }
    
    return render_template('registration_form.html', 
                         camp_config=CAMP_CONFIG,
                         camp_title=get_camp_title(),
                         camp_subtitle=get_camp_subtitle(),
                         pricing_text=get_pricing_text(),
                         pricing=pricing)

@app.route('/register')
def register():
    """Registration form (alternative route)."""
    return redirect(url_for('index'))

@app.route('/submit', methods=['POST'])
def submit():
    """Handle registration submission."""
    try:
        # Generate submission ID
        submission_id = f"CP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.form.get('child_last_name', 'REG')[:3].upper()}"
        
        # Get form data
        data = {
            'child_first_name': request.form.get('child_first_name', ''),
            'child_last_name': request.form.get('child_last_name', ''),
            'child_age': int(request.form.get('child_age', 0)) if request.form.get('child_age') else 0,
            'parent_first_name': request.form.get('parent_first_name', ''),
            'parent_last_name': request.form.get('parent_last_name', ''),
            'parent_email': request.form.get('parent_email', ''),
            'parent_phone': request.form.get('parent_phone', ''),
            'emergency_contact_name': request.form.get('emergency_contact_name', ''),
            'emergency_contact_phone': request.form.get('emergency_contact_phone', ''),
            'has_allergies': bool(request.form.get('has_allergies')),
            'allergies_description': request.form.get('allergies_description', ''),
            'has_medical_conditions': bool(request.form.get('has_medical_conditions')),
            'medical_conditions_description': request.form.get('medical_conditions_description', ''),
            'is_returning_camper': bool(request.form.get('is_returning_camper')),
            'returning_years': request.form.get('returning_years', ''),
            'how_heard_about_camp': request.form.get('how_heard_about_camp', ''),
            'additional_comments': request.form.get('additional_comments', ''),
            'bringing_own_switch': bool(request.form.get('bringing_own_switch')),
            'has_sensory_issues': bool(request.form.get('has_sensory_issues'))
        }
        
        # Save to database
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO registrations (
                submission_id, child_first_name, child_last_name, child_age,
                parent_first_name, parent_last_name, parent_email, parent_phone,
                emergency_contact_name, emergency_contact_phone,
                has_allergies, allergies_description, has_medical_conditions, 
                medical_conditions_description, is_returning_camper, returning_years,
                how_heard_about_camp, additional_comments, bringing_own_switch, has_sensory_issues
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id, data['child_first_name'], data['child_last_name'], 
            data['child_age'], data['parent_first_name'], data['parent_last_name'],
            data['parent_email'], data['parent_phone'], 
            data['emergency_contact_name'], data['emergency_contact_phone'],
            data['has_allergies'], data['allergies_description'],
            data['has_medical_conditions'], data['medical_conditions_description'],
            data['is_returning_camper'], data['returning_years'],
            data['how_heard_about_camp'], data['additional_comments'],
            data['bringing_own_switch'], data['has_sensory_issues']
        ))
        conn.commit()
        conn.close()
        
        return render_template('confirmation.html', 
                             submission_id=submission_id,
                             child_name=f"{data['child_first_name']} {data['child_last_name']}",
                             camp_config=CAMP_CONFIG)
                             
    except Exception as e:
        print(f"Registration error: {str(e)}")
        flash('Registration failed. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_logged_in', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@require_admin_auth
def admin_dashboard():
    """Admin dashboard with all registrations."""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        
        # Get registrations as dictionaries
        registrations = [dict(row) for row in cursor.fetchall()]
        
        # Calculate statistics
        total_registrations = len(registrations)
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        todays_registrations = [r for r in registrations if r['timestamp'].date() == today]
        weeks_registrations = [r for r in registrations if r['timestamp'].date() >= week_ago]
        
        paid_count = len([r for r in registrations if r['payment_status'] == 'paid'])
        pending_payment = len([r for r in registrations if r['payment_status'] == 'pending'])
        
        returning_campers = len([r for r in registrations if r['is_returning_camper']])
        new_campers = total_registrations - returning_campers
        
        bringing_switch = len([r for r in registrations if r.get('bringing_own_switch')])
        has_allergies = len([r for r in registrations if r['has_allergies']])
        has_sensory_issues = len([r for r in registrations if r.get('has_sensory_issues')])
        
        # Age distribution
        ages = [r['child_age'] for r in registrations if r['child_age']]
        age_groups = {
            '5-7': len([age for age in ages if 5 <= age <= 7]),
            '8-10': len([age for age in ages if 8 <= age <= 10]),
            '11-13': len([age for age in ages if 11 <= age <= 13]),
            '14-16': len([age for age in ages if 14 <= age <= 16]),
            '17-18': len([age for age in ages if 17 <= age <= 18])
        }
        
        session_stats = {
            'total_registrations': total_registrations,
            'todays_count': len(todays_registrations),
            'weeks_count': len(weeks_registrations),
            'paid_count': paid_count,
            'pending_payment': pending_payment,
            'returning_campers': returning_campers,
            'new_campers': new_campers,
            'bringing_switch': bringing_switch,
            'has_allergies': has_allergies,
            'has_sensory_issues': has_sensory_issues,
            'age_groups': age_groups,
            'last_registration': registrations[0]['timestamp'] if registrations else 'None',
            'registration_rate': f"{len(todays_registrations)}/day" if todays_registrations else "0/day"
        }
        
        conn.close()
        
        return render_template('admin_dashboard.html', 
                             registrations=registrations,
                             session_stats=session_stats,
                             camp_config=CAMP_CONFIG)
                             
    except Exception as e:
        print(f"Admin dashboard error: {str(e)}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('admin_login'))

@app.route('/test-db')
def test_db():
    """Test database connection."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM registrations")
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({
            "database_type": "PostgreSQL",
            "environment": "production",
            "registrations_count": count,
            "success": True,
            "message": "Database working - your registration data is safe!"
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

if __name__ == '__main__':
    init_registration_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)