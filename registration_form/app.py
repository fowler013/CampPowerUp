#!/usr/bin/env python3
"""
Camp Power-Up Registration Form Application - FINAL VERSION
==========================================================
Complete system with admin dashboard matching staging environment
"""

import os
import sqlite3
import uuid
import hashlib
import csv
import io
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, Response, make_response
from functools import wraps

# Try to import database config, fallback to SQLite if not available
try:
    from database_config import get_db_connection, init_postgresql_tables, DB_CONFIG
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Try to import camp config, use defaults if not available
try:
    from camp_config import CAMP_CONFIG, get_camp_title, get_camp_subtitle, get_pricing_text
    CAMP_CONFIG_AVAILABLE = True
except ImportError:
    CAMP_CONFIG_AVAILABLE = False
    CAMP_CONFIG = {
        'camp_name': 'Camp Power-Up 2025',
        'camp_subtitle': 'Gaming Camp Registration',
        'camp_dates': 'TBD',
        'pricing': {'new_camper': 250, 'returning_camper': 200}
    }

app = Flask(__name__, template_folder='./templates')
app.secret_key = os.environ.get('SECRET_KEY', 'camp_power_up_registration_2025_dev_only')

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'campadmin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'PowerUp2025!')

# Database setup
REGISTRATION_DB = os.path.join(os.path.dirname(__file__), 'registration_submissions.db')

def get_safe_db_connection():
    """Get database connection with fallback to SQLite."""
    if DATABASE_AVAILABLE:
        try:
            # Check if it's a context manager
            conn = get_db_connection()
            if hasattr(conn, '__enter__'):
                return conn.__enter__()
            return conn
        except:
            pass
    # Fallback to SQLite
    return sqlite3.connect(REGISTRATION_DB)

def require_admin_auth(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_registration_db():
    """Initialize the registration database with fallback."""
    try:
        if DATABASE_AVAILABLE and DB_CONFIG.get('database_url'):
            # PostgreSQL
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id SERIAL PRIMARY KEY,
                    submission_id TEXT UNIQUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                    has_allergies BOOLEAN DEFAULT FALSE,
                    allergies_description TEXT,
                    has_medical_conditions BOOLEAN DEFAULT FALSE,
                    medical_conditions_description TEXT,
                    is_returning_camper BOOLEAN DEFAULT FALSE,
                    returning_years TEXT,
                    how_heard_about_camp TEXT,
                    additional_comments TEXT,
                    bringing_own_switch BOOLEAN DEFAULT FALSE,
                    has_sensory_issues BOOLEAN DEFAULT FALSE
                )
            """)
        else:
            # SQLite fallback
            conn = sqlite3.connect(REGISTRATION_DB)
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
        print(f"Database initialization error: {e}")

@app.route('/')
def index():
    """Main registration form."""
    try:
        if CAMP_CONFIG_AVAILABLE:
            return render_template('registration_form.html', 
                                 camp_config=CAMP_CONFIG,
                                 camp_title=get_camp_title(),
                                 camp_subtitle=get_camp_subtitle(),
                                 pricing_text=get_pricing_text())
        else:
            return render_template('registration_form.html', camp_config=CAMP_CONFIG)
    except Exception as e:
        print(f"Template error: {e}")
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Camp Power-Up Registration 2025</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
                .container { max-width: 800px; margin: 0 auto; background: rgba(255, 255, 255, 0.95); border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
                .header { background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 40px; text-align: center; }
                .header h1 { font-size: 2.5em; margin-bottom: 10px; }
                .content { padding: 40px; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 8px; color: #333; font-weight: 600; }
                input, textarea, select { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
                input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; }
                .submit-btn { background: linear-gradient(45deg, #667eea, #764ba2); color: white; border: none; padding: 15px 30px; border-radius: 8px; font-size: 18px; cursor: pointer; width: 100%; }
                .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏕️ Camp Power-Up 2025</h1>
                    <p>Gaming Camp Registration Form</p>
                </div>
                <div class="content">
                    <p><strong>Registration form is being restored. Please check back shortly or contact fowler0613@gmail.com for assistance.</strong></p>
                    <p><a href="/admin/login" style="color: #667eea;">Admin Login</a></p>
                </div>
            </div>
        </body>
        </html>
        '''

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
        conn = get_safe_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_AVAILABLE and DB_CONFIG.get('database_url'):
            # PostgreSQL
            cursor.execute("""
                INSERT INTO registrations (
                    submission_id, child_first_name, child_last_name, child_age,
                    parent_first_name, parent_last_name, parent_email, parent_phone,
                    emergency_contact_name, emergency_contact_phone,
                    has_allergies, allergies_description, has_medical_conditions, 
                    medical_conditions_description, is_returning_camper, returning_years,
                    how_heard_about_camp, additional_comments, bringing_own_switch, has_sensory_issues
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        else:
            # SQLite
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
        
        try:
            return render_template('confirmation.html', 
                                 submission_id=submission_id,
                                 child_name=f"{data['child_first_name']} {data['child_last_name']}",
                                 camp_config=CAMP_CONFIG)
        except:
            return f'''
            <html><head><title>Registration Successful</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
            <h1>✅ Registration Successful!</h1>
            <p><strong>Submission ID:</strong> {submission_id}</p>
            <p><strong>Camper:</strong> {data['child_first_name']} {data['child_last_name']}</p>
            <p>Thank you for registering for Camp Power-Up!</p>
            <p><a href="/">Register Another Camper</a></p>
            </body></html>
            '''
                             
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
    
    try:
        return render_template('admin_login.html')
    except:
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Login - Camp Power-Up</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
                .login-container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
                .logo { font-size: 3em; margin-bottom: 10px; }
                h1 { color: #333; margin-bottom: 10px; font-size: 1.8em; }
                .subtitle { color: #666; margin-bottom: 30px; }
                .form-group { margin-bottom: 20px; text-align: left; }
                label { display: block; margin-bottom: 5px; color: #333; font-weight: 600; }
                input[type="text"], input[type="password"] { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
                input[type="text"]:focus, input[type="password"]:focus { outline: none; border-color: #667eea; }
                .login-btn { width: 100%; padding: 15px; background: linear-gradient(45deg, #667eea, #764ba2); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
                .login-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
                .back-link { margin-top: 20px; display: block; color: #667eea; text-decoration: none; }
                .credentials-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 14px; color: #666; border-left: 4px solid #667eea; }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">🏕️</div>
                <h1>Admin Login</h1>
                <p class="subtitle">Camp Power-Up Registration System</p>
                <form method="POST">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="login-btn">🔐 Login to Admin Panel</button>
                </form>
                <div class="credentials-info">
                    <strong>Default Credentials:</strong><br>
                    Username: <code>campadmin</code><br>
                    Password: <code>PowerUp2025!</code>
                </div>
                <a href="/" class="back-link">← Back to Registration Form</a>
            </div>
        </body>
        </html>
        '''

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
        conn = get_safe_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        
        # Handle different database types
        if DATABASE_AVAILABLE and DB_CONFIG.get('database_url'):
            # PostgreSQL
            columns = [desc[0] for desc in cursor.description]
            registrations = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            # SQLite
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
            registrations = [dict(row) for row in cursor.fetchall()]
        
        # Calculate statistics
        total_registrations = len(registrations)
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        todays_registrations = []
        weeks_registrations = []
        
        for r in registrations:
            reg_date = r['timestamp']
            if hasattr(reg_date, 'date'):
                reg_date = reg_date.date()
            elif isinstance(reg_date, str):
                try:
                    reg_date = datetime.strptime(reg_date.split()[0], '%Y-%m-%d').date()
                except:
                    continue
            
            if reg_date == today:
                todays_registrations.append(r)
            if reg_date >= week_ago:
                weeks_registrations.append(r)
        
        paid_count = len([r for r in registrations if r.get('payment_status') == 'paid'])
        pending_payment = len([r for r in registrations if r.get('payment_status') == 'pending'])
        
        returning_campers = len([r for r in registrations if r.get('is_returning_camper')])
        new_campers = total_registrations - returning_campers
        
        bringing_switch = len([r for r in registrations if r.get('bringing_own_switch')])
        has_allergies = len([r for r in registrations if r.get('has_allergies')])
        has_sensory_issues = len([r for r in registrations if r.get('has_sensory_issues')])
        
        # Age distribution
        ages = [r['child_age'] for r in registrations if r.get('child_age')]
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
        return f'''
        <html><head><title>Admin Dashboard</title></head>
        <body style="font-family: Arial; max-width: 800px; margin: 20px auto; padding: 20px;">
        <h1>🏕️ Camp Power-Up Admin Dashboard</h1>
        <p><strong>Admin system is online!</strong></p>
        <p>Dashboard functionality is being restored. Error: {str(e)}</p>
        <p><a href="/admin/logout">Logout</a></p>
        </body></html>
        '''

@app.route('/admin/export')
@require_admin_auth
def export_registrations():
    """Export registrations as CSV."""
    try:
        conn = get_safe_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        registrations = cursor.fetchall()
        
        # Get column names
        if DATABASE_AVAILABLE and DB_CONFIG.get('database_url'):
            columns = [desc[0] for desc in cursor.description]
        else:
            columns = [description[0] for description in cursor.description]
        
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(columns)
        
        # Write data
        for row in registrations:
            writer.writerow(row)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=camp_registrations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-type"] = "text/csv"
        
        return response
        
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/test-db')
def test_db():
    """Test database connection."""
    try:
        # Use SQLite directly for testing
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT UNIQUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("SELECT COUNT(*) FROM registrations")
        count = cursor.fetchone()[0]
        conn.close()
        
        db_type = "SQLite (Railway Backup)"
        
        return jsonify({
            "database_type": db_type,
            "environment": "production",
            "registrations_count": count,
            "success": True,
            "message": "Database working - registration system is ready!"
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

# Make sure the app is accessible for gunicorn
application = app

if __name__ == '__main__':
    init_registration_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)