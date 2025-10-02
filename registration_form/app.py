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
        # Railway production - use persistent volume path
        data_dir = '/app/data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'registration_submissions.db')
    else:
        # Local development
        return 'registration_submissions.db'

DB_FILE = get_database_path()

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

def init_db():
    """Initialize database."""
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
            additional_comments TEXT
        )
    """)
    conn.commit()
    conn.close()

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
    """Test database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM registrations")
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({
            "database_type": "SQLite",
            "environment": "production",
            "registrations_count": count,
            "success": True,
            "message": "Database working - your registration data is safe!"
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

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
            'how_heard_about_camp': json_data.get('howHeardAboutCamp', ''),
            'additional_comments': json_data.get('additionalComments', '')
        }
        
        # Save to database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registrations (
                submission_id, child_first_name, child_last_name, child_age,
                parent_first_name, parent_last_name, parent_email, parent_phone,
                emergency_contact_name, emergency_contact_phone,
                has_allergies, allergies_description, has_medical_conditions, 
                medical_conditions_description, is_returning_camper, returning_years,
                how_heard_about_camp, additional_comments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id, data['child_first_name'], data['child_last_name'], 
            data['child_age'], data['parent_first_name'], data['parent_last_name'],
            data['parent_email'], data['parent_phone'], 
            data['emergency_contact_name'], data['emergency_contact_phone'],
            data['has_allergies'], data['allergies_description'],
            data['has_medical_conditions'], data['medical_conditions_description'],
            data['is_returning_camper'], data['returning_years'],
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
        
        # Debug: Check if registration exists and log details
        if not registration:
            # Check if any registrations exist at all
            cursor.execute("SELECT COUNT(*) as count FROM registrations")
            count_result = cursor.fetchone()
            total_registrations = count_result[0] if count_result else 0
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registrations'")
            table_exists = cursor.fetchone() is not None
            
            conn.close()
            
            return f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h1>⚠️ Registration Not Found</h1>
                <p><strong>Submission ID:</strong> {submission_id}</p>
                <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Debug Information:</h3>
                    <p><strong>Database Path:</strong> {DB_FILE}</p>
                    <p><strong>Table Exists:</strong> {table_exists}</p>
                    <p><strong>Total Registrations:</strong> {total_registrations}</p>
                    <p><strong>Environment:</strong> {"Railway" if os.environ.get("RAILWAY_ENVIRONMENT") else "Local"}</p>
                </div>
                <p><a href="/">← Back to Registration Form</a></p>
            </div>
            ''', 404
            
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

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)