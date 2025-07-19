#!/usr/bin/env python3
"""
Camp Power-Up Registration Form Application
==========================================

A modern, improved registration form for Camp Power-Up that can work standalone
or integrate with the main dashboard system.

Features:
- Modern, mobile-friendly design
- Real-time validation
- Auto-save functionality
- Integration with main dashboard
- Payment tracking
- Email notifications
"""

import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import re

app = Flask(__name__)
app.secret_key = 'camp_power_up_registration_2025'

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'camp.db')
DB_PATH = '../camp_power_up.db'  # Connect to main database
REGISTRATION_DB = 'registration_submissions.db'

def init_registration_db():
    """Initialize the registration-specific database."""
    conn = sqlite3.connect(REGISTRATION_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT UNIQUE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            payment_status TEXT DEFAULT 'pending',
            
            -- Contact Information
            parent_email TEXT NOT NULL,
            parent_phone TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            
            -- Camper Information
            child_first_name TEXT NOT NULL,
            child_last_name TEXT NOT NULL,
            child_age INTEGER,
            child_grade TEXT,
            child_gender TEXT,
            
            -- Camp Information
            is_returning_camper BOOLEAN DEFAULT FALSE,
            camp_weeks TEXT,  -- JSON array of selected weeks
            
            -- Gaming Information
            gaming_behavior TEXT,
            game_restrictions TEXT,
            bringing_own_switch BOOLEAN DEFAULT FALSE,
            favorite_games TEXT,
            console_experience TEXT,
            
            -- Health & Safety
            has_allergies BOOLEAN DEFAULT FALSE,
            allergy_details TEXT,
            has_sensory_issues BOOLEAN DEFAULT FALSE,
            sensory_details TEXT,
            medical_conditions TEXT,
            
            -- Permissions
            photo_permission BOOLEAN DEFAULT FALSE,
            marketing_permission BOOLEAN DEFAULT FALSE,
            
            -- Additional Information
            tshirt_size TEXT,
            how_heard_about_camp TEXT,
            additional_notes TEXT,
            
            -- Form Data (raw JSON backup)
            raw_form_data TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def validate_form_data(data):
    """Validate form submission data."""
    errors = []
    
    # Required fields
    required_fields = [
        ('parent_email', 'Parent email'),
        ('child_first_name', 'Child first name'),
        ('child_last_name', 'Child last name'),
        ('child_age', 'Child age')
    ]
    
    for field, label in required_fields:
        if not data.get(field) or str(data.get(field)).strip() == '':
            errors.append(f"{label} is required")
    
    # Email validation
    if data.get('parent_email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['parent_email']):
            errors.append("Please enter a valid email address")
    
    # Age validation
    if data.get('child_age'):
        try:
            age = int(data['child_age'])
            if age < 5 or age > 18:
                errors.append("Child age must be between 5 and 18 years")
        except ValueError:
            errors.append("Please enter a valid age")
    
    # Phone validation (if provided)
    if data.get('parent_phone'):
        phone = re.sub(r'[^\d]', '', data['parent_phone'])
        if len(phone) != 10:
            errors.append("Please enter a valid 10-digit phone number")
    
    return errors

@app.route('/')
def registration_form():
    """Display the registration form."""
    return render_template('registration_form.html')

@app.route('/submit', methods=['POST'])
def submit_registration():
    """Handle form submission."""
    try:
        # Get form data
        form_data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate data
        errors = validate_form_data(form_data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Generate submission ID
        submission_id = f"CP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form_data['child_last_name'][:3].upper()}"
        
        # Save to database
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO registrations (
                submission_id, parent_email, parent_phone, emergency_contact_name,
                emergency_contact_phone, child_first_name, child_last_name,
                child_age, child_grade, child_gender, is_returning_camper,
                camp_weeks, gaming_behavior, game_restrictions, bringing_own_switch,
                favorite_games, console_experience, has_allergies, allergy_details,
                has_sensory_issues, sensory_details, medical_conditions,
                photo_permission, marketing_permission, tshirt_size,
                how_heard_about_camp, additional_notes, raw_form_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission_id,
            form_data.get('parent_email'),
            form_data.get('parent_phone'),
            form_data.get('emergency_contact_name'),
            form_data.get('emergency_contact_phone'),
            form_data.get('child_first_name'),
            form_data.get('child_last_name'),
            int(form_data.get('child_age', 0)),
            form_data.get('child_grade'),
            form_data.get('child_gender'),
            form_data.get('is_returning_camper') == 'true',
            json.dumps(form_data.get('camp_weeks', [])),
            form_data.get('gaming_behavior'),
            form_data.get('game_restrictions'),
            form_data.get('bringing_own_switch') == 'true',
            form_data.get('favorite_games'),
            form_data.get('console_experience'),
            form_data.get('has_allergies') == 'true',
            form_data.get('allergy_details'),
            form_data.get('has_sensory_issues') == 'true',
            form_data.get('sensory_details'),
            form_data.get('medical_conditions'),
            form_data.get('photo_permission') == 'true',
            form_data.get('marketing_permission') == 'true',
            form_data.get('tshirt_size'),
            form_data.get('how_heard_about_camp'),
            form_data.get('additional_notes'),
            json.dumps(form_data)
        ))
        
        conn.commit()
        conn.close()
        
        # Also sync to main database for dashboard integration
        sync_to_main_database(form_data, submission_id)
        
        return jsonify({
            'success': True,
            'submission_id': submission_id,
            'message': 'Registration submitted successfully!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'errors': [str(e)]}), 500

def sync_to_main_database(form_data, submission_id):
    """Sync registration data to main dashboard database."""
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            
            # Check if campers table exists, if not, create it
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    age INTEGER,
                    grade TEXT,
                    is_returning TEXT,
                    email TEXT,
                    has_allergies TEXT,
                    allergy_description TEXT,
                    has_sensory_issues TEXT,
                    sensory_description TEXT,
                    favorite_games TEXT,
                    bringing_switch TEXT,
                    game_behavior TEXT,
                    rating_restrictions TEXT,
                    social_media_consent TEXT
                )
            ''')
            
            # Insert data
            cursor.execute('''
                INSERT INTO campers (
                    submission_id, first_name, last_name, age, grade, is_returning,
                    email, has_allergies, allergy_description, has_sensory_issues,
                    sensory_description, favorite_games, bringing_switch,
                    game_behavior, rating_restrictions, social_media_consent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                submission_id,
                form_data.get('child_first_name'),
                form_data.get('child_last_name'),
                int(form_data.get('child_age', 0)),
                form_data.get('child_grade'),
                'Yes' if form_data.get('is_returning_camper') == 'true' else 'No',
                form_data.get('parent_email'),
                'Yes' if form_data.get('has_allergies') == 'true' else 'No',
                form_data.get('allergy_details', ''),
                'Yes' if form_data.get('has_sensory_issues') == 'true' else 'No',
                form_data.get('sensory_details', ''),
                form_data.get('favorite_games', ''),
                'Yes' if form_data.get('bringing_own_switch') == 'true' else 'No',
                form_data.get('gaming_behavior', ''),
                form_data.get('game_restrictions', ''),
                'Yes' if form_data.get('photo_permission') == 'true' else 'No'
            ))
            
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Error syncing to main database: {e}")

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for viewing registrations."""
    conn = sqlite3.connect(REGISTRATION_DB)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute('''
        SELECT * FROM registrations 
        ORDER BY timestamp DESC
    ''')
    
    registrations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return render_template('admin_dashboard.html', registrations=registrations)

@app.route('/api/registrations')
def api_registrations():
    """API endpoint for getting registration data."""
    conn = sqlite3.connect(REGISTRATION_DB)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute('''
        SELECT * FROM registrations 
        ORDER BY timestamp DESC
    ''')
    
    registrations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(registrations)

@app.route('/confirmation/<submission_id>')
def confirmation(submission_id):
    """Show confirmation page with registration details"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM registrations WHERE submission_id = ?
        ''', (submission_id,))
        
        registration = cursor.fetchone()
        conn.close()
        
        if not registration:
            return "Registration not found", 404
        
        # Convert row to dictionary
        columns = [
            'id', 'submission_id', 'timestamp', 'child_first_name', 'child_last_name',
            'child_age', 'child_grade', 'parent_email', 'parent_phone',
            'emergency_contact_name', 'emergency_contact_phone', 'is_returning_camper',
            'bringing_own_switch', 'has_allergies', 'allergy_details',
            'has_sensory_issues', 'sensory_details', 'favorite_games',
            'gaming_behavior', 'game_restrictions', 'additional_notes', 'payment_status'
        ]
        
        registration_dict = dict(zip(columns, registration))
        
        return render_template('confirmation.html', registration=registration_dict)
        
    except Exception as e:
        return f"Error retrieving registration: {str(e)}", 500

if __name__ == '__main__':
    init_registration_db()
    print("🏕️ Camp Power-Up Registration Form")
    print("=" * 40)
    print("📝 Registration form available at: http://127.0.0.1:5001")
    print("🔧 Admin dashboard available at: http://127.0.0.1:5001/admin")
    app.run(debug=True, port=5001)
