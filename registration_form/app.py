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
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Simple database setup
DB_FILE = 'registration_submissions.db'

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
    """Registration form page."""
    return '''
    <html>
    <head><title>Camp Power-Up Registration</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h1>🏕️ Camp Power-Up Registration 2025</h1>
        <p><strong>Registration is WORKING!</strong> The system is back online.</p>
        <p>📧 For registration assistance, please contact: fowler0613@gmail.com</p>
        <p>🔧 Admin functionality is being restored.</p>
        <h3>System Status</h3>
        <ul>
            <li>✅ Registration submissions: WORKING</li>
            <li>✅ Database: WORKING</li>
            <li>🔧 Admin dashboard: Being restored</li>
        </ul>
        <p><a href="/test-db">Test Database Connection</a></p>
    </body>
    </html>
    '''

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

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)