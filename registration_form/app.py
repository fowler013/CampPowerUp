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
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

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
    return """
    <html><head><title>Camp Power-Up Registration</title></head>
    <body><h1>🏕️ Camp Power-Up Registration - WORKING!</h1>
    <p>✅ App is running successfully!</p>
    <p>🔗 <a href="/test-db">Test Database Connection</a></p>
    <p>📝 Registration form coming back online...</p>
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
        
        return render_template('confirmation.html', submission_id=submission_id)
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)