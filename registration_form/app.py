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
from flask import Flask, request, jsonify, render_template

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

# Simple database setup
DB_FILE = 'registration_submissions.db'

# Helper functions for templates
def get_camp_title():
    return "Camp Power-Up 2025 Registration"

def get_camp_subtitle():
    return "Nintendo Switch Gaming Camp - November 24-26, 2025"

def get_pricing_text():
    return "Registration fees listed below"

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
    """Show confirmation page."""
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
    </body></html>
    '''

@app.route('/admin')
def admin():
    """Simple admin view."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Simple HTML response with registration list
        html = '''
        <html><head><title>Camp Power-Up Admin</title></head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
        <h1>🏕️ Camp Power-Up Admin Dashboard</h1>
        '''
        
        if registrations:
            html += f'<p><strong>Total Registrations:</strong> {len(registrations)}</p>'
            html += '<table border="1" style="border-collapse: collapse; width: 100%;">'
            html += '''<tr style="background: #f0f0f0;">
                <th>ID</th><th>Child Name</th><th>Age</th><th>Parent</th><th>Email</th><th>Phone</th><th>Timestamp</th>
            </tr>'''
            
            for reg in registrations:
                html += f'''<tr>
                    <td>{reg["submission_id"]}</td>
                    <td>{reg["child_first_name"]} {reg["child_last_name"]}</td>
                    <td>{reg["child_age"]}</td>
                    <td>{reg["parent_first_name"]} {reg["parent_last_name"]}</td>
                    <td>{reg["parent_email"]}</td>
                    <td>{reg["parent_phone"]}</td>
                    <td>{reg["timestamp"]}</td>
                </tr>'''
            html += '</table>'
        else:
            html += '<p>No registrations yet.</p>'
            
        html += '''
        <p style="margin-top: 20px;">
            <a href="/admin/export">📥 Export CSV</a> | 
            <a href="/">📝 Registration Form</a>
        </p>
        </body></html>
        '''
        return html
        
    except Exception as e:
        return f'Admin Error: {str(e)}', 500

@app.route('/admin/export')
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
            return "No registrations to export", 404
            
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
        return f'Export Error: {str(e)}', 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)