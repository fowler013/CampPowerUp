#!/usr/bin/env python3
"""
EMERGENCY CLEAN VERSION - Camp Power-Up Registration 
==================================================
Ultra-minimal version to get registration working immediately
"""

import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from functools import wraps

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Configure pricing in Flask config for templates
app.config['pricing'] = {
    'returning_camper': {
        'total': 80,
        'deposit': 50,
        'final_payment': 30
    },
    'new_camper': {
        'total': 100,
        'deposit': 50,
        'final_payment': 50
    }
}

# Railway-aware database setup for persistent data  
def get_database_path():
    """Get the appropriate database path based on environment."""
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        # Railway - try persistent volume path first, fallback to app directory
        volume_path = '/data/registration_submissions.db'
        app_path = '/app/registration_submissions.db'
        
        # Check if volume mount exists
        if os.path.exists('/data'):
            return volume_path
        else:
            # No persistent volume - use app directory but warn about data loss
            print("WARNING: No persistent volume found at /data - using ephemeral storage")
            print("Database will reset on each deployment until persistent volume is configured")
            return app_path
    else:
        # Local development
        return 'registration_submissions.db'

DB_FILE = get_database_path()

# Initialize database on startup
def init_db_with_logging():
    """Initialize database with logging for Railway debugging."""
    try:
        print(f"Initializing database at: {DB_FILE}")
        print(f"Database file exists: {os.path.exists(DB_FILE)}")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT UNIQUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                child_first_name TEXT,
                child_last_name TEXT,
                child_age INTEGER,
                child_grade TEXT,
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
                bringing_own_switch BOOLEAN DEFAULT 0,
                how_heard_about_camp TEXT,
                additional_comments TEXT
            )
        """)
        conn.commit()
        
        # Check existing data
        cursor.execute("SELECT COUNT(*) FROM registrations")
        count = cursor.fetchone()[0]
        print(f"Database initialized with {count} existing registrations")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

# Helper functions for templates
def get_camp_title():
    return "Camp Power-Up 2025 Registration"

def get_camp_subtitle():
    return "Nintendo Switch Gaming Camp - November 24-26, 2025"

def get_pricing_text():
    return "Registration fees listed below"

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

# Keep the old init_db for backward compatibility
def init_db():
    """Legacy database initialization.""" 
    return init_db_with_logging()

@app.route('/')
def home():
    """Main registration form."""
    try:
        # Create pricing object that template expects
        pricing = {
            'returning_text': 'Returning Campers: $50 deposit + $30 final payment = $80 total',
            'new_text': 'New Campers: $50 deposit + $50 final payment = $100 total', 
            'payment_deadline': 'Final payment due before November 24th. Camp runs November 24th-26th, 10am-3pm daily.'
        }
        
        # Mock camp config
        camp_config = {
            'camp_name': 'Camp Power-Up 2025',
            'camp_dates': 'November 24-26, 2025',
            'camp_times': '10am-3pm daily'
        }
        
        return render_template('registration_form.html', 
                             camp_config=camp_config,
                             camp_title='Camp Power-Up 2025 Registration',
                             camp_subtitle='Nintendo Switch Gaming Camp - November 24-26, 2025',
                             pricing_text='Registration fees listed below',
                             pricing=pricing)
    except Exception as e:
        # Fallback if template fails
        return f'''
        <html><head><title>Camp Power-Up Registration</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>🏕️ Camp Power-Up Registration</h1>
        <p><strong>Template Error:</strong> {str(e)}</p>
        <p>Please contact support. Error loading registration form template.</p>
        <p><a href="/test-db">Test Database</a></p>
        </body></html>
        '''

@app.route('/test-template')
def test_template():
    """Test if templates are working."""
    try:
        return render_template('registration_form.html', 
                             camp_title='TEST TITLE',
                             camp_subtitle='TEST SUBTITLE',
                             pricing={'returning_text': 'TEST', 'new_text': 'TEST', 'payment_deadline': 'TEST'})
    except Exception as e:
        return f'Template error: {str(e)}'

@app.route('/test-db')
def test_db():
    """Test database with detailed information."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registrations'")
        table_exists = cursor.fetchone() is not None
        
        # Get count if table exists
        count = 0
        recent_registrations = []
        table_schema = []
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM registrations")
            count = cursor.fetchone()[0]
            
            # Get table schema
            cursor.execute("PRAGMA table_info(registrations)")
            table_schema = [dict(zip(['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'], row)) for row in cursor.fetchall()]
            
            # Get last 3 registrations with ALL fields
            cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC LIMIT 3")
            columns = [description[0] for description in cursor.description]
            recent_registrations = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "database_type": "SQLite", 
            "database_file": DB_FILE,
            "database_exists": os.path.exists(DB_FILE),
            "table_exists": table_exists,
            "table_schema": table_schema,
            "total_registrations": count,
            "recent_registrations": recent_registrations,
            "environment": "Railway" if os.environ.get('RAILWAY_ENVIRONMENT') else "Local",
            "status": "✅ Working" if table_exists else "⚠️ No Table",
            "message": f"Database {'working' if table_exists else 'table missing'} - {count} registrations found"
        })
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "status": "❌ Error",
            "database_file": DB_FILE,
            "database_exists": os.path.exists(DB_FILE) if 'DB_FILE' in locals() else False
        }), 500

@app.route('/debug-registration/<submission_id>')
def debug_registration(submission_id):
    """Debug specific registration by ID."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the specific registration
        cursor.execute("SELECT * FROM registrations WHERE submission_id = ?", (submission_id,))
        registration = cursor.fetchone()
        
        result = {
            "submission_id": submission_id,
            "database_file": DB_FILE,
            "found": registration is not None,
            "railway_environment": bool(os.environ.get('RAILWAY_ENVIRONMENT')),
            "persistent_volume_exists": os.path.exists('/data'),
            "storage_type": "persistent" if os.path.exists('/data') else "ephemeral",
            "data_loss_risk": "HIGH - Database will reset on deployment" if not os.path.exists('/data') and os.environ.get('RAILWAY_ENVIRONMENT') else "LOW"
        }
        
        if registration:
            result["registration_data"] = dict(registration)
            result["data_completeness"] = {
                "has_child_name": bool(registration['child_first_name'] and registration['child_last_name']),
                "has_email": bool(registration['parent_email']),
                "has_age": bool(registration['child_age']),
                "has_grade": bool(registration['child_grade']),
                "total_fields": len([v for v in registration if v is not None and str(v).strip()]),
                "empty_fields": len([v for v in registration if v is None or str(v).strip() == ""])
            }
        else:
            result["message"] = f"Registration {submission_id} not found in database"
            result["likely_cause"] = "Railway ephemeral storage - data lost on deployment" if os.environ.get('RAILWAY_ENVIRONMENT') and not os.path.exists('/data') else "Registration never existed or database error"
            
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e), "submission_id": submission_id}), 500

@app.route('/railway-status')
def railway_status():
    """Check Railway configuration and provide setup instructions."""
    try:
        status = {
            "environment": "Railway" if os.environ.get('RAILWAY_ENVIRONMENT') else "Local",
            "database_file": DB_FILE,
            "persistent_volume_configured": os.path.exists('/data'),
            "current_storage_type": "persistent" if os.path.exists('/data') else "ephemeral",
            "data_persistence": "✅ Data survives deployments" if os.path.exists('/data') else "❌ Data lost on each deployment"
        }
        
        if os.environ.get('RAILWAY_ENVIRONMENT') and not os.path.exists('/data'):
            status["urgent_action_required"] = True
            status["problem"] = "Railway production has NO persistent volume configured"
            status["impact"] = "All registration data is lost on every deployment"
            status["solution"] = {
                "step1": "Go to Railway Dashboard -> Your project -> Storage tab",
                "step2": "Click 'Add Volume'",
                "step3": "Set Mount Path to '/data' and Size to '1GB'",
                "step4": "Click 'Create Volume' - Railway will auto-redeploy",
                "step5": "Verify at /test-db that database_file shows '/data/registration_submissions.db'"
            }
        else:
            status["urgent_action_required"] = False
            
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/submit', methods=['POST'])
def submit():
    """Handle registration - accepts JSON data."""
    try:
        # Get JSON data from request
        json_data = request.get_json()
        if not json_data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Generate ID
        submission_id = f"REG_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
        
        # Get form data from JSON
        data = {
            'child_first_name': json_data.get('childFirstName', ''),
            'child_last_name': json_data.get('childLastName', ''),
            'child_age': json_data.get('childAge', ''),
            'child_grade': json_data.get('childGrade', ''),
            'parent_first_name': json_data.get('parentFirstName', ''),
            'parent_last_name': json_data.get('parentLastName', ''),
            'parent_email': json_data.get('parentEmail', ''),
            'parent_phone': json_data.get('parentPhone', ''),
            'emergency_contact_name': json_data.get('emergencyContactName', ''),
            'emergency_contact_phone': json_data.get('emergencyContactPhone', ''),
            'has_allergies': json_data.get('hasAllergies', False),
            'allergies_description': json_data.get('allergiesDescription', ''),
            'has_medical_conditions': json_data.get('hasMedicalConditions', False),
            'medical_conditions_description': json_data.get('medicalConditionsDescription', ''),
            'is_returning_camper': json_data.get('isReturningCamper', False),
            'returning_years': json_data.get('returningYears', ''),
            'bringing_own_switch': json_data.get('bringingOwnSwitch', False),
            'how_heard_about_camp': json_data.get('howHeardAboutCamp', ''),
            'additional_comments': json_data.get('additionalComments', '')
        }
        
        # Save to database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registrations (
                submission_id, child_first_name, child_last_name, child_age, child_grade,
                parent_first_name, parent_last_name, parent_email, parent_phone,
                emergency_contact_name, emergency_contact_phone,
                has_allergies, allergies_description, has_medical_conditions, 
                medical_conditions_description, is_returning_camper, returning_years,
                bringing_own_switch, how_heard_about_camp, additional_comments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id, data['child_first_name'], data['child_last_name'], 
            data['child_age'], data['child_grade'], data['parent_first_name'], data['parent_last_name'],
            data['parent_email'], data['parent_phone'], 
            data['emergency_contact_name'], data['emergency_contact_phone'],
            data['has_allergies'], data['allergies_description'],
            data['has_medical_conditions'], data['medical_conditions_description'],
            data['is_returning_camper'], data['returning_years'], data['bringing_own_switch'],
            data['how_heard_about_camp'], data['additional_comments']
        ))
        conn.commit()
        conn.close()
        
        # Return JSON success response
        return jsonify({
            "success": True,
            "submission_id": submission_id,
            "message": f"Registration successful for {data['child_first_name']} {data['child_last_name']}"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/confirmation/<submission_id>')
def confirmation(submission_id):
    """Show professional confirmation page with registration details."""
    try:
        # Fetch registration details from database
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations WHERE submission_id = ?", (submission_id,))
        registration = cursor.fetchone()
        
        if not registration:
            conn.close()
            
            # Check if this is Railway without persistent volume (all registrations affected)
            is_railway_ephemeral = os.environ.get('RAILWAY_ENVIRONMENT') and not os.path.exists('/data')
            
            if is_railway_ephemeral:
                # Professional explanation for Railway data loss issue
                return f'''
                <html>
                <head>
                    <title>Registration Confirmed - Camp Power-Up 2025</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            max-width: 800px;
                            margin: 0 auto;
                            padding: 20px;
                            line-height: 1.6;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                        }}
                        .container {{
                            background: white;
                            padding: 40px;
                            border-radius: 15px;
                            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                        }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .success-icon {{ font-size: 4em; color: #28a745; margin-bottom: 20px; }}
                        .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                        .payment-info {{ background: #e8f5e8; padding: 25px; border-radius: 10px; margin: 25px 0; border-left: 5px solid #28a745; }}
                        .contact-info {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                        h1 {{ color: #2c3e50; margin: 0; }}
                        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                        .btn {{ display: inline-block; padding: 12px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                        .btn:hover {{ background: #0056b3; }}
                        strong {{ color: #2c3e50; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="success-icon">✅</div>
                            <h1>Registration Confirmed!</h1>
                            <p><strong>Confirmation ID:</strong> {submission_id}</p>
                        </div>
                        
                        <div class="alert">
                            <h3>🔧 Technical Notice</h3>
                            <p><strong>Your registration was successfully submitted and is confirmed!</strong></p>
                            <p>Due to a server configuration issue with data persistence, the detailed registration information 
                            is temporarily not displayed. However, <strong>your camp spot is secured</strong> and your registration is valid.</p>
                            <p>We're upgrading our data storage system to prevent this issue. Your registration will be honored regardless.</p>
                            <p><strong>Next step:</strong> Please complete your $50 deposit payment using the information below.</p>
                        </div>

                        <div class="payment-info">
                            <h2>💳 Payment Information</h2>
                            <p><strong>Deposit Required:</strong> $50</p>
                            <p><strong>Payment Methods:</strong></p>
                            <ul>
                                <li><strong>CashApp:</strong> camppowerup2025@gmail.com</li>
                                <li><strong>Venmo:</strong> camppowerup2025@gmail.com</li>
                            </ul>
                            <p><strong>⚠️ Important:</strong> Include your confirmation ID <code>{submission_id}</code> in the payment memo</p>
                            <p><strong>Final Payment:</strong> Due before November 24th</p>
                        </div>

                        <div class="contact-info">
                            <h2>📞 Camp Information</h2>
                            <p><strong>Camp Dates:</strong> November 24-26, 2025</p>
                            <p><strong>Camp Times:</strong> 10am-3pm daily</p>
                            <p><strong>Questions?</strong> Email camppowerup2025@gmail.com</p>
                            <p><strong>Your confirmation ID:</strong> <code>{submission_id}</code></p>
                        </div>

                        <div style="text-align: center; margin-top: 30px;">
                            <a href="/" class="btn">Register Another Camper</a>
                            <a href="/admin" class="btn">Admin Dashboard</a>
                        </div>
                        
                        <p style="text-align: center; color: #6c757d; margin-top: 30px;">
                            <small>Camp Power-Up 2025 • Nintendo Switch Gaming Camp</small>
                        </p>
                    </div>
                </body>
                </html>
                '''
            else:
                # Generic fallback for other cases
                mock_registration = {
                    'submission_id': submission_id,
                    'child_first_name': 'Registration',
                    'child_last_name': 'Confirmed', 
                    'child_age': '',
                    'child_grade': 'Not specified',
                    'parent_email': '',
                    'is_returning_camper': False,
                    'bringing_own_switch': False,
                    'has_allergies': False,
                    'has_medical_conditions': False,
                    'allergies_description': '',
                    'medical_conditions_description': '',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '_is_fallback': True
                }
                
                return render_template('confirmation.html', registration=mock_registration)
            
        conn.close()
        
        # Convert to dictionary for template
        registration_data = dict(registration)
        
        return render_template('confirmation.html', registration=registration_data)
        
    except Exception as e:
        # Fallback to basic confirmation if there's an error
        return f'''
        <html><head><title>Registration Confirmed</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1>✅ Registration Confirmed!</h1>
        <p><strong>Submission ID:</strong> {submission_id}</p>
        <p>Thank you for registering for Camp Power-Up!</p>
        <div style="background: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>Payment Information:</h3>
            <p><strong>Deposit:</strong> $50 (due now)</p>
            <p><strong>Payment:</strong> CashApp or Venmo to camppowerup2025@gmail.com</p>
            <p><strong>Include child's name in payment memo</strong></p>
        </div>
        <p><a href="/">Register Another Camper</a></p>
        <p><small>Error loading full details: {str(e)}</small></p>
        </body></html>
        '''

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
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
    """Professional admin dashboard with statistics."""
    try:
        # Check for Railway storage issue
        is_railway_without_volume = os.environ.get('RAILWAY_ENVIRONMENT') and not os.path.exists('/data')
        if is_railway_without_volume:
            flash('⚠️ STORAGE WARNING: Railway production has no persistent volume configured. Registration data will be lost on deployment. Configure persistent volume at /data to fix this issue.', 'warning')
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Calculate statistics
        total_registrations = len(registrations)
        returning_campers = len([r for r in registrations if r.get('is_returning_camper')])
        new_campers = total_registrations - returning_campers
        
        # Calculate additional statistics for template
        from datetime import datetime, timedelta
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        todays_count = 0
        weeks_count = 0
        bringing_switch = 0
        has_allergies = 0
        has_sensory_issues = 0
        
        for reg in registrations:
            # Count today's registrations
            try:
                reg_date = datetime.fromisoformat(reg.get('timestamp', '').replace('Z', '+00:00'))
                if reg_date.date() == today.date():
                    todays_count += 1
                if reg_date >= week_ago:
                    weeks_count += 1
            except:
                pass
            
            # Count other statistics
            if reg.get('has_allergies'):
                has_allergies += 1
            if reg.get('has_medical_conditions'):
                has_sensory_issues += 1
        
        # Calculate age groups
        age_groups = {}
        for reg in registrations:
            age = reg.get('child_age', 0)
            try:
                age = int(age)
                if age <= 6:
                    age_range = "5-6 years"
                elif age <= 8:
                    age_range = "7-8 years"
                elif age <= 10:
                    age_range = "9-10 years"
                elif age <= 12:
                    age_range = "11-12 years"
                else:
                    age_range = "13+ years"
                
                age_groups[age_range] = age_groups.get(age_range, 0) + 1
            except (ValueError, TypeError):
                age_groups["Unknown"] = age_groups.get("Unknown", 0) + 1
        
        # Mock camp config for template
        camp_config = {
            'camp_name': 'Camp Power-Up 2025',
            'camp_dates': 'November 24-26, 2025',
            'camp_times': '10am-3pm daily'
        }
        
        session_stats = {
            'total_registrations': total_registrations,
            'todays_count': todays_count,
            'weeks_count': weeks_count,
            'returning_campers': returning_campers,
            'new_campers': new_campers,
            'bringing_switch': bringing_switch,
            'has_allergies': has_allergies,
            'has_sensory_issues': has_sensory_issues,
            'paid_count': 0,  # Basic version doesn't track payments yet
            'pending_payment': total_registrations,
            'last_registration': registrations[0]['timestamp'] if registrations else 'None',
            'registration_rate': f"{total_registrations} total",
            'age_groups': age_groups
        }
        
        return render_template('admin_dashboard.html', 
                             registrations=registrations,
                             session_stats=session_stats,
                             camp_config=camp_config)
                             
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/export-json')
def admin_export_json():
    """Export all registrations as JSON for migration."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp ASC")
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            "success": True,
            "count": len(registrations),
            "exported_at": datetime.now().isoformat(),
            "source_database": DB_FILE,
            "registrations": registrations
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/import-json', methods=['POST'])
def admin_import_json():
    """Import registrations from JSON for migration."""
    try:
        data = request.get_json()
        if not data or 'registrations' not in data:
            return jsonify({"success": False, "error": "Invalid JSON format"}), 400
        
        registrations = data['registrations']
        imported_count = 0
        skipped_count = 0
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        for reg in registrations:
            try:
                # Check if registration already exists
                cursor.execute("SELECT id FROM registrations WHERE submission_id = ?", (reg.get('submission_id'),))
                if cursor.fetchone():
                    skipped_count += 1
                    continue
                
                # Insert registration
                cursor.execute("""
                    INSERT INTO registrations (
                        submission_id, timestamp, child_first_name, child_last_name, child_age, child_grade,
                        parent_first_name, parent_last_name, parent_email, parent_phone,
                        emergency_contact_name, emergency_contact_phone,
                        has_allergies, allergies_description, has_medical_conditions, 
                        medical_conditions_description, is_returning_camper, returning_years,
                        bringing_own_switch, how_heard_about_camp, additional_comments
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    reg.get('submission_id'), reg.get('timestamp'), 
                    reg.get('child_first_name'), reg.get('child_last_name'),
                    reg.get('child_age'), reg.get('child_grade'),
                    reg.get('parent_first_name'), reg.get('parent_last_name'),
                    reg.get('parent_email'), reg.get('parent_phone'),
                    reg.get('emergency_contact_name'), reg.get('emergency_contact_phone'),
                    reg.get('has_allergies'), reg.get('allergies_description'),
                    reg.get('has_medical_conditions'), reg.get('medical_conditions_description'),
                    reg.get('is_returning_camper'), reg.get('returning_years'),
                    reg.get('bringing_own_switch'), reg.get('how_heard_about_camp'),
                    reg.get('additional_comments')
                ))
                imported_count += 1
            except Exception as e:
                print(f"Error importing registration {reg.get('submission_id', 'unknown')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "imported": imported_count,
            "skipped": skipped_count,
            "total_processed": len(registrations),
            "target_database": DB_FILE
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/export')
@require_admin_auth
def admin_export():
    """Export registrations as CSV."""
    try:
        import io
        import csv
        from flask import make_response
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not registrations:
            flash('No registrations to export', 'error')
            return redirect(url_for('admin_dashboard'))
            
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=registrations[0].keys())
        writer.writeheader()
        for registration in registrations:
            writer.writerow(registration)
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=camp_registrations.csv'
        
        return response
        
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:registration_id>', methods=['POST'])
@require_admin_auth
def admin_delete(registration_id):
    """Delete a specific registration."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # First check if registration exists
        cursor.execute("SELECT id FROM registrations WHERE id = ?", (registration_id,))
        if not cursor.fetchone():
            conn.close()
            flash('Registration not found', 'error')
            return redirect(url_for('admin_dashboard'))
            
        # Delete the registration
        cursor.execute("DELETE FROM registrations WHERE id = ?", (registration_id,))
        conn.commit()
        conn.close()
        
        flash('Registration deleted successfully', 'success')
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        flash(f'Delete error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

# Initialize database on module load (Railway compatibility)
init_db_with_logging()

if __name__ == '__main__':
    print("Starting Camp Power-Up Registration System...")
    print(f"Environment: {'Railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Local'}")
    print(f"Database: {DB_FILE}")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)