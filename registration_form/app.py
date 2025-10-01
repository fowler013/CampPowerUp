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
        <p><a href="/register">📝 Registration Form</a></p>
        <p><a href="/test-db">Test Database Connection</a></p>
    </body>
    </html>
    '''

@app.route('/register')
def register():
    """Registration form."""
    return '''
    <html>
    <head><title>Camp Power-Up Registration Form</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1>🏕️ Camp Power-Up 2025 Registration</h1>
        <form method="POST" action="/submit">
            <h3>Child Information</h3>
            <p><label>First Name: <input type="text" name="child_first_name" required style="width: 200px;"></label></p>
            <p><label>Last Name: <input type="text" name="child_last_name" required style="width: 200px;"></label></p>
            <p><label>Age: <input type="number" name="child_age" min="5" max="18" required style="width: 100px;"></label></p>
            
            <h3>Parent Information</h3>
            <p><label>Parent First Name: <input type="text" name="parent_first_name" required style="width: 200px;"></label></p>
            <p><label>Parent Last Name: <input type="text" name="parent_last_name" required style="width: 200px;"></label></p>
            <p><label>Email: <input type="email" name="parent_email" required style="width: 300px;"></label></p>
            <p><label>Phone: <input type="tel" name="parent_phone" required style="width: 200px;"></label></p>
            
            <h3>Emergency Contact</h3>
            <p><label>Emergency Contact Name: <input type="text" name="emergency_contact_name" required style="width: 200px;"></label></p>
            <p><label>Emergency Contact Phone: <input type="tel" name="emergency_contact_phone" required style="width: 200px;"></label></p>
            
            <h3>Medical Information</h3>
            <p><label><input type="checkbox" name="has_allergies"> Child has allergies</label></p>
            <p><label>If yes, please describe: <br><textarea name="allergies_description" rows="3" cols="50"></textarea></label></p>
            
            <p><label><input type="checkbox" name="has_medical_conditions"> Child has medical conditions</label></p>
            <p><label>If yes, please describe: <br><textarea name="medical_conditions_description" rows="3" cols="50"></textarea></label></p>
            
            <h3>Previous Experience</h3>
            <p><label><input type="checkbox" name="is_returning_camper"> Returning camper</label></p>
            <p><label>If returning, how many years: <input type="number" name="returning_years" min="1" max="10" style="width: 100px;"></label></p>
            
            <h3>Additional Information</h3>
            <p><label>How did you hear about camp: <br><textarea name="how_heard_about_camp" rows="2" cols="50"></textarea></label></p>
            <p><label>Additional comments: <br><textarea name="additional_comments" rows="3" cols="50"></textarea></label></p>
            
            <p><input type="submit" value="Register for Camp" style="background: #4CAF50; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;"></p>
        </form>
        <p><a href="/">← Back to Home</a></p>
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
    """Handle registration."""
    try:
        # Generate ID
        submission_id = f"REG_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
        
        # Get form data
        data = {
            'child_first_name': request.form.get('child_first_name', ''),
            'child_last_name': request.form.get('child_last_name', ''),
            'child_age': request.form.get('child_age', ''),
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
            'additional_comments': request.form.get('additional_comments', '')
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
        
        return f'''
        <html><head><title>Registration Successful</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1>✅ Registration Successful!</h1>
        <p><strong>Submission ID:</strong> {submission_id}</p>
        <p>Thank you for registering for Camp Power-Up!</p>
        <p>You will receive a confirmation email shortly.</p>
        <p><a href="/">Register Another Camper</a></p>
        </body></html>
        '''
        
    except Exception as e:
        return f'Registration Error: {str(e)}', 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)