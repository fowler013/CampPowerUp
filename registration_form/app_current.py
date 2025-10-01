#!/usr/bin/env python3
"""
EMERGENCY MINIMAL VERSION - Camp Power-Up Registration Form
==========================================================
Simplified version to get forms working immediately while debugging syntax issues.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, make_response
from functools import wraps

# Import our PostgreSQL database config
try:
    from database_config import get_db_connection, DB_CONFIG, REGISTRATION_DB
except ImportError:
    print("⚠️ Could not import database_config, using SQLite fallback")
    REGISTRATION_DB = 'registration_submissions.db'
    def get_db_connection():
        return sqlite3.connect(REGISTRATION_DB)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Admin configuration
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'campadmin')  # Original working username
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'PowerUp2025!')  # Original working password

def require_admin_auth(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_database():
    """Initialize the registration database."""
    conn = get_db_connection()
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
    print("✅ Database initialized")

@app.route('/')
def registration_form():
    """Display the registration form."""
    try:
        # Provide template variables
        pricing = {
            'returning_text': 'Returning Campers: $100 deposit + $200 final payment = $300 total',
            'new_text': 'New Campers: $125 deposit + $225 final payment = $350 total', 
            'payment_deadline': 'Final payment due before camp start. Camp runs July 15-19, 2025, 9:00 AM - 4:00 PM daily.'
        }
        
        config = {
            'pricing': {
                'returning_camper': {'total': 300},
                'new_camper': {'total': 350}
            }
        }
        
        return render_template('registration_form.html', pricing=pricing, config=config)
    except Exception as e:
        print(f"Template error: {e}")
        return f"""
        <html><head><title>Camp Power-Up Registration</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h1>🏕️ Camp Power-Up Registration</h1>
        <p><strong>⚠️ Template loading issue. Please contact support.</strong></p>
        <p>Error: {str(e)}</p>
        <p><a href="/test-db">Test Database Connection</a></p>
        </body></html>
        """

@app.route('/test-db')
def test_db():
    """Test database connection."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM registrations")
        count = cursor.fetchone()[0]
        conn.close()
        
        db_type = "PostgreSQL" if hasattr(conn, 'notices') or 'postgresql' in str(type(conn)) else "SQLite"
        
        return jsonify({
            "database_type": db_type,
            "environment": "production" if DB_CONFIG.get('is_production') else "development", 
            "registrations_count": count,
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/submit', methods=['POST'])
def submit_registration():
    """Handle form submissions."""
    try:
        # Extract form data
        form_data = {
            'child_first_name': request.form.get('child_first_name', '').strip(),
            'child_last_name': request.form.get('child_last_name', '').strip(),
            'child_age': request.form.get('child_age', '').strip(),
            'parent_first_name': request.form.get('parent_first_name', '').strip(),
            'parent_last_name': request.form.get('parent_last_name', '').strip(),
            'parent_email': request.form.get('parent_email', '').strip(),
            'parent_phone': request.form.get('parent_phone', '').strip(),
            'emergency_contact_name': request.form.get('emergency_contact_name', '').strip(),
            'emergency_contact_phone': request.form.get('emergency_contact_phone', '').strip(),
            'has_allergies': bool(request.form.get('has_allergies')),
            'allergies_description': request.form.get('allergies_description', '').strip(),
            'has_medical_conditions': bool(request.form.get('has_medical_conditions')),
            'medical_conditions_description': request.form.get('medical_conditions_description', '').strip(),
            'is_returning_camper': bool(request.form.get('is_returning_camper')),
            'returning_years': request.form.get('returning_years', '').strip(),
            'how_heard_about_camp': request.form.get('how_heard_about_camp', '').strip(),
            'additional_comments': request.form.get('additional_comments', '').strip()
        }
        
        # Generate submission ID
        submission_id = f"REG_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
        
        # Save to database
        conn = get_db_connection()
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
            submission_id, form_data['child_first_name'], form_data['child_last_name'], 
            form_data['child_age'], form_data['parent_first_name'], form_data['parent_last_name'],
            form_data['parent_email'], form_data['parent_phone'], 
            form_data['emergency_contact_name'], form_data['emergency_contact_phone'],
            form_data['has_allergies'], form_data['allergies_description'],
            form_data['has_medical_conditions'], form_data['medical_conditions_description'],
            form_data['is_returning_camper'], form_data['returning_years'],
            form_data['how_heard_about_camp'], form_data['additional_comments']
        ))
        
        conn.commit()
        conn.close()
        
        try:
            return render_template('confirmation.html', submission_id=submission_id)
        except:
            return f"""
            <html><head><title>Registration Successful</title></head>
            <body><h1>✅ Registration Successful!</h1>
            <p><strong>Submission ID:</strong> {submission_id}</p>
            <p>Thank you for registering for Camp Power-Up!</p>
            <p><a href="/">Register Another Camper</a></p>
            </body></html>
            """
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@app.route('/deployment-info')
def deployment_info():
    """Show deployment timestamp."""
    return jsonify({
        "deployment_time": "2025-10-01 18:25:00 UTC",
        "version": "minimal-v2-with-template-fix",
        "status": "registration_form_restored"
    })

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return '''
    <html><head><title>Camp Power-Up Admin Login</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; background: #f5f5f5;">
        <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2>🏕️ Camp Power-Up Admin</h2>
            <form method="post">
                <div style="margin-bottom: 15px;">
                    <label>Username:</label><br>
                    <input type="text" name="username" required style="width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label>Password:</label><br>
                    <input type="password" name="password" required style="width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                <button type="submit" style="background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">Login</button>
            </form>
        </div>
    </body></html>
    '''

@app.route('/admin')
@require_admin_auth
def admin_dashboard():
    """Admin dashboard."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get registration count and recent registrations
        cursor.execute("SELECT COUNT(*) FROM registrations")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT submission_id, child_first_name, child_last_name, parent_email, timestamp FROM registrations ORDER BY timestamp DESC LIMIT 10")
        recent_registrations = cursor.fetchall()
        
        conn.close()
        
        # Build HTML response
        registrations_html = ""
        for reg in recent_registrations:
            registrations_html += f'''
            <tr>
                <td>{reg[0]}</td>
                <td>{reg[1]} {reg[2]}</td>
                <td>{reg[3]}</td>
                <td>{reg[4]}</td>
            </tr>
            '''
        
        return f'''
        <html><head><title>Camp Power-Up Admin Dashboard</title></head>
        <body style="font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5;">
            <div style="background: white; padding: 30px; border-radius: 10px; margin-bottom: 20px;">
                <h1>🏕️ Camp Power-Up Admin Dashboard</h1>
                <p><strong>Total Registrations:</strong> {total_count}</p>
                <p><a href="/admin/export" style="background: #28a745; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px;">📊 Export CSV</a></p>
                <p><a href="/admin/logout" style="background: #dc3545; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px;">🚪 Logout</a></p>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 10px;">
                <h2>Recent Registrations</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 10px; border: 1px solid #ddd;">Submission ID</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Child Name</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Parent Email</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {registrations_html}
                    </tbody>
                </table>
            </div>
        </body></html>
        '''
        
    except Exception as e:
        return f"Admin Error: {str(e)}", 500

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/export')
@require_admin_auth
def export_registrations():
    """Export registrations as CSV."""
    import csv
    import io
    from datetime import datetime
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM registrations ORDER BY timestamp DESC"
        cursor.execute(query)
        registrations = cursor.fetchall()
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Submission ID', 'Timestamp', 'Child First Name', 'Child Last Name', 'Child Age',
            'Parent First Name', 'Parent Last Name', 'Parent Email', 'Parent Phone',
            'Emergency Contact Name', 'Emergency Contact Phone', 'Has Allergies', 'Allergies Description',
            'Has Medical Conditions', 'Medical Conditions Description', 'Is Returning Camper',
            'Returning Years', 'How Heard About Camp', 'Additional Comments'
        ])
        
        # Write data
        for reg in registrations:
            writer.writerow(reg)
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=camp_registrations_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return f"Export Error: {str(e)}", 500

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)