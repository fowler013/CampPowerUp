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
- Dynamic session configuration
"""

import os
import sqlite3
import json
import hashlib
import smtplib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from database_config import get_db_connection, init_postgresql_tables, DB_CONFIG
import re
from camp_config import CAMP_CONFIG, get_camp_title, get_camp_subtitle, get_pricing_text, validate_config

# Import requests for SendGrid only if needed
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import email modules after Flask to avoid conflicts
try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
    print("✅ Email functionality available")
except ImportError:
    EMAIL_AVAILABLE = False
    print("⚠️ Email functionality not available - MIMEText/MIMEMultipart imports failed")

app = Flask(__name__, template_folder='./templates')
app.secret_key = os.environ.get('SECRET_KEY', 'camp_power_up_registration_2025_dev_only')

# Admin credentials - loaded from environment variables for security
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'campadmin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'PowerUp2025!')  # Default for dev only

# Email configuration - supports both SMTP and SendGrid
EMAIL_CONFIG = {
    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
    'email_address': os.environ.get('CAMP_EMAIL', 'camppowerup2025@gmail.com'),
    'email_password': os.environ.get('CAMP_EMAIL_PASSWORD', ''),
    'from_name': 'Camp Power-Up Registration',
    'sendgrid_api_key': os.environ.get('SENDGRID_API_KEY', ''),
    'sendgrid_from_email': os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@sendgrid.net'),
    'sendgrid_from_name': os.environ.get('SENDGRID_FROM_NAME', 'Camp Power-Up Registration'),
    'sendgrid_reply_to': os.environ.get('SENDGRID_REPLY_TO', 'fowler0613@gmail.com'),
    'use_sendgrid': bool(os.environ.get('SENDGRID_API_KEY', ''))
}

def check_admin_auth():
    """Check if user is authenticated as admin."""
    return session.get('admin_authenticated', False)

def require_admin_auth(f):
    """Decorator to require admin authentication."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_admin_auth():
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'camp.db')
DB_PATH = '../camp_power_up.db'  # Connect to main database
REGISTRATION_DB = os.path.join(os.path.dirname(__file__), 'registration_submissions.db')

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
            previous_year TEXT,  -- When they last attended
            previous_instructor TEXT,  -- Staff they remember
            returning_camper_details TEXT,  -- Memories/activities from previous years
            camp_weeks TEXT,  -- JSON array of selected weeks
            
            -- Gaming Information
            gaming_behavior TEXT,
            game_restrictions TEXT,
            bringing_own_switch BOOLEAN DEFAULT FALSE,
            favorite_games TEXT,
            games_owned TEXT,  -- New field for explicit game ownership
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

def send_email_via_sendgrid(to_email, subject, html_content):
    """Send email using SendGrid API."""
    if not REQUESTS_AVAILABLE:
        print("❌ Requests library not available for SendGrid")
        return False
        
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {EMAIL_CONFIG['sendgrid_api_key']}",
        "Content-Type": "application/json"
    }
    
    data = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": subject
        }],
        "from": {
            "email": EMAIL_CONFIG['sendgrid_from_email'],
            "name": EMAIL_CONFIG['sendgrid_from_name']
        },
        "reply_to": {
            "email": EMAIL_CONFIG['sendgrid_reply_to']
        },
        "content": [{
            "type": "text/html",
            "value": html_content
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"SendGrid response status: {response.status_code}")
        if response.status_code != 202:
            print(f"SendGrid error response: {response.text}")
        return response.status_code == 202
    except Exception as e:
        print(f"SendGrid request failed: {e}")
        return False

def send_confirmation_email(registration_data):
    """Send confirmation email to parent after registration."""
    if not EMAIL_AVAILABLE:
        print(f"⚠️ Email not available - would send confirmation to {registration_data['parent_email']}")
        return False
    
    try:
        subject = f"Registration Confirmed - Camp Power-Up 2025 - {registration_data['child_first_name']} {registration_data['child_last_name']}"
        
        # Use SendGrid if available (better for Railway), fallback to SMTP
        if EMAIL_CONFIG['use_sendgrid']:
            return send_via_sendgrid(registration_data, subject)
        else:
            return send_via_smtp(registration_data, subject)
            
    except Exception as e:
        print(f"❌ Failed to send confirmation email: {e}")
        return False

def send_admin_notification(registration_data):
    """Send notification to camp admin about new registration."""
    admin_email = "camppowerup2025@gmail.com"
    subject = f"🏕️ NEW REGISTRATION - {registration_data['child_first_name']} {registration_data['child_last_name']}"
    
    html_content = f"""
    <h2>🏕️ New Camp Power-Up Registration</h2>
    <p><strong>Child:</strong> {registration_data['child_first_name']} {registration_data['child_last_name']} (Age: {registration_data['child_age']})</p>
    <p><strong>Parent:</strong> {registration_data['parent_first_name']} {registration_data['parent_last_name']}</p>
    <p><strong>Email:</strong> {registration_data['parent_email']}</p>
    <p><strong>Phone:</strong> {registration_data.get('parent_phone', 'Not provided')}</p>
    <p><strong>Switch:</strong> {'Bringing own' if registration_data.get('bringing_own_switch') else 'Needs camp switch'}</p>
    <p><strong>Type:</strong> {'Returning camper' if registration_data.get('is_returning_camper') else 'New camper'}</p>
    <p><strong>Submission ID:</strong> {registration_data['submission_id']}</p>
    
    <div style="background: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <h3>💰 Payment Expected: $180</h3>
        <p>Watch for Zelle payment from {registration_data['parent_email']}</p>
        <p>Payment memo should include: "{registration_data['child_first_name']} {registration_data['child_last_name']}"</p>
    </div>
    """
    
    try:
        if EMAIL_CONFIG['use_sendgrid']:
            result = send_email_via_sendgrid(admin_email, subject, html_content)
            if result:
                print(f"✅ Admin notification sent to {admin_email}")
            else:
                print(f"❌ Admin notification failed to {admin_email}")
            return result
        else:
            print(f"⚠️ SMTP mode - admin notification not implemented yet")
            return False
    except Exception as e:
        print(f"❌ Failed to send admin notification: {e}")
        return False

def send_via_sendgrid(registration_data, subject):
    """Send email using SendGrid API (Railway-compatible)."""
    print(f"🔄 Attempting SendGrid email to {registration_data['parent_email']}")
    print(f"📧 SendGrid config: API key length={len(EMAIL_CONFIG['sendgrid_api_key'])}, from={EMAIL_CONFIG['sendgrid_from_email']}")
    
    # Create email content
    html_content = create_email_html_content(registration_data)
    
    try:
        result = send_email_via_sendgrid(
            registration_data['parent_email'],
            subject,
            html_content
        )
        if result:
            print(f"✅ SendGrid email sent successfully to {registration_data['parent_email']}")
            return True
        else:
            print(f"❌ SendGrid email failed to {registration_data['parent_email']} - falling back to SMTP")
            # Fall back to SMTP if SendGrid fails
            if EMAIL_CONFIG['email_password']:
                print(f"🔄 Falling back to SMTP for {registration_data['parent_email']}")
                return send_via_smtp(registration_data, subject)
            else:
                print(f"❌ No SMTP password available for fallback")
                return False
    except Exception as e:
        print(f"❌ SendGrid error: {e}")
        return False

def create_email_html_content(registration_data):
    """Create HTML email content."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .content {{ padding: 30px; }}
            .confirmation-id {{ background: #f8f9fa; border: 2px solid #28a745; border-radius: 10px; padding: 20px; margin: 20px 0; text-align: center; }}
            .confirmation-id h2 {{ color: #28a745; margin: 0 0 10px 0; }}
            .confirmation-id .id {{ font-size: 24px; font-weight: bold; color: #333; }}
            .summary {{ background: #f8f9fa; border-radius: 10px; padding: 20px; margin: 20px 0; }}
            .summary-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
            .summary-row:last-child {{ border-bottom: none; }}
            .label {{ font-weight: bold; color: #333; }}
            .value {{ color: #666; }}
            .next-steps {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
                <h1>Registration Confirmed!</h1>
                <p>Thank you for registering for Camp Power-Up 2025</p>
            </div>
            
            <div class="content">
                <div class="confirmation-id">
                    <h2>Confirmation ID</h2>
                    <div class="id">{registration_data['submission_id']}</div>
                    <p>Please save this ID for your records</p>
                </div>
                
                <div class="summary">
                    <h3>📋 Registration Summary</h3>
                    <div class="summary-row">
                        <span class="label">Camper Name:</span>
                        <span class="value">{registration_data['child_first_name']} {registration_data['child_last_name']}</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Age:</span>
                        <span class="value">{registration_data['child_age']} years old</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Contact Email:</span>
                        <span class="value">{registration_data['parent_email']}</span>
                    </div>
                </div>
                
                <div class="next-steps">
                    <h3>📝 Next Steps</h3>
                    <ol>
                        <li><strong>Payment:</strong> Complete registration by sending $180 via Zelle to <strong>fowler0613@gmail.com</strong></li>
                        <li><strong>Include your child's name</strong> in payment memo: "{registration_data['child_first_name']} {registration_data['child_last_name']}"</li>
                        <li><strong>Confirmation:</strong> Payment confirmation within 24 hours</li>
                    </ol>
                </div>
            </div>
            
            <div class="footer">
                <p>Camp Power-Up 2025 | Gaming & Technology Camp</p>
                <p>Questions? Contact us at <strong>fowler0613@gmail.com</strong></p>
            </div>
        </div>
    </body>
    </html>
    """

def send_via_smtp(registration_data, subject):
    """Send email using SMTP (local development)."""
    try:
        # Create email content
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email_address']}>"
        msg['To'] = registration_data['parent_email']
        
        # Create email content
        html_content = create_email_html_content(registration_data)
        text_content = f"""
        Registration Confirmed - Camp Power-Up 2025
        
        Confirmation ID: {registration_data['submission_id']}
        Camper: {registration_data['child_first_name']} {registration_data['child_last_name']}
        
        Next Steps:
        1. Send $180 via Zelle to fowler0613@gmail.com
        2. Include "{registration_data['child_first_name']} {registration_data['child_last_name']}" in memo
        
        Questions? Contact fowler0613@gmail.com
        """
        
        # Attach both versions
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send via SMTP
        if EMAIL_CONFIG['email_password']:
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['email_address'], EMAIL_CONFIG['email_password'])
            server.send_message(msg)
            server.quit()
            print(f"✅ SMTP email sent to {registration_data['parent_email']}")
            return True
        else:
            print(f"⚠️ No SMTP password configured")
            return False
            
    except Exception as e:
        print(f"❌ SMTP email failed: {e}")
        return False

def check_returning_camper_validity(child_first_name, child_last_name, parent_email):
    """Check if a camper claiming to be returning actually has past registrations."""
    import csv
    
    # First check current registration database
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
    cursor = conn.cursor()
    
    # Check for exact name and email match in current registrations
    # Look for registrations from previous years/seasons (more than 30 days ago)
    cursor.execute('''
        SELECT COUNT(*) FROM registrations 
        WHERE LOWER(child_first_name) = LOWER(?) 
        AND LOWER(child_last_name) = LOWER(?) 
        AND LOWER(parent_email) = LOWER(?)
        AND timestamp < datetime('now', '-30 days')  -- Must be from a previous camp session
    ''', (child_first_name.strip(), child_last_name.strip(), parent_email.strip()))
    
    exact_matches_db = cursor.fetchone()[0]
    
    # Also check for just name match in current registrations (in case email changed)
    cursor.execute('''
        SELECT COUNT(*) FROM registrations 
        WHERE LOWER(child_first_name) = LOWER(?) 
        AND LOWER(child_last_name) = LOWER(?)
        AND timestamp < datetime('now', '-30 days')  -- Must be from a previous camp session
    ''', (child_first_name.strip(), child_last_name.strip()))
    
    name_matches_db = cursor.fetchone()[0]
    conn.close()
    
    # Now check historical CSV data
    historical_csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'Camp_Power_Up_past_forms - Sheet1.csv')
    exact_matches_csv = 0
    name_matches_csv = 0
    
    try:
        with open(historical_csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Get the field names (handling possible variations)
                first_name_field = None
                last_name_field = None
                email_field = None
                
                for field in row.keys():
                    if 'first name' in field.lower() or 'childs first' in field.lower():
                        first_name_field = field
                    elif 'last name' in field.lower() or 'childs last' in field.lower():
                        last_name_field = field
                    elif 'email' in field.lower():
                        email_field = field
                
                if first_name_field and last_name_field and email_field:
                    csv_first = row.get(first_name_field, '').strip()
                    csv_last = row.get(last_name_field, '').strip()
                    csv_email = row.get(email_field, '').strip()
                    
                    # Check for exact match (name + email)
                    if (csv_first.lower() == child_first_name.strip().lower() and 
                        csv_last.lower() == child_last_name.strip().lower() and 
                        csv_email.lower() == parent_email.strip().lower()):
                        exact_matches_csv += 1
                    
                    # Check for name-only match
                    elif (csv_first.lower() == child_first_name.strip().lower() and 
                          csv_last.lower() == child_last_name.strip().lower()):
                        name_matches_csv += 1
                        
    except (FileNotFoundError, Exception) as e:
        # If we can't read the historical data, just log it but don't fail
        print(f"Warning: Could not read historical camper data: {e}")
    
    # Combine results from both sources
    total_exact_matches = exact_matches_db + exact_matches_csv
    total_name_matches = name_matches_db + name_matches_csv
    
    return {
        'exact_matches': total_exact_matches,
        'name_matches': total_name_matches,
        'exact_matches_current': exact_matches_db,
        'name_matches_current': name_matches_db,
        'exact_matches_historical': exact_matches_csv,
        'name_matches_historical': name_matches_csv,
        'is_likely_returning': total_exact_matches > 0 or total_name_matches > 0
    }

def validate_form_data(data):
    """Validate form submission data."""
    errors = []
    warnings = []
    
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
    
    # Returning camper validation
    if data.get('is_returning_camper') == 'true':
        # Require verification fields for returning campers
        if not data.get('previous_year') or str(data.get('previous_year')).strip() == '':
            errors.append("Please specify when your child last attended Camp Power-Up.")
        
        # Check against database
        if data.get('child_first_name') and data.get('child_last_name') and data.get('parent_email'):
            validation_result = check_returning_camper_validity(
                data['child_first_name'], 
                data['child_last_name'], 
                data['parent_email']
            )
            
            if not validation_result['is_likely_returning']:
                errors.append("⚠️ VALIDATION ERROR: No previous registration found for this camper. Please select 'No - This is my child's first time' if this is their first time at Camp Power-Up. If you believe this is an error, please contact us directly.")
    
    return errors, warnings

@app.route('/')
def registration_form():
    """Display the registration form with dynamic configuration."""
    try:
        validate_config()
        pricing = get_pricing_text()
        
        return render_template('registration_form.html', 
                             camp_title=get_camp_title(),
                             camp_subtitle=get_camp_subtitle(),
                             pricing=pricing,
                             config=CAMP_CONFIG)
    except ValueError as e:
        return f"Configuration Error: {e}", 500

@app.route('/submit', methods=['POST'])
def submit_registration():
    """Handle form submission."""
    try:
        # Get form data
        form_data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate data
        errors, warnings = validate_form_data(form_data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Generate submission ID
        submission_id = f"CP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form_data['child_last_name'][:3].upper()}"
        
        # Save to database
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO registrations (
                submission_id, status, payment_status, parent_email, parent_phone, emergency_contact_name,
                emergency_contact_phone, child_first_name, child_last_name,
                child_age, child_grade, child_gender, is_returning_camper,
                previous_year, previous_instructor, returning_camper_details,
                camp_weeks, gaming_behavior, game_restrictions, bringing_own_switch,
                favorite_games, games_owned, console_experience, has_allergies, allergy_details,
                has_sensory_issues, sensory_details, medical_conditions,
                photo_permission, marketing_permission, tshirt_size,
                how_heard_about_camp, additional_notes, raw_form_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission_id,
            'pending',  # status
            'pending',  # payment_status
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
            form_data.get('previous_year') if form_data.get('is_returning_camper') == 'true' else None,
            form_data.get('previous_instructor') if form_data.get('is_returning_camper') == 'true' else None,
            form_data.get('returning_camper_details') if form_data.get('is_returning_camper') == 'true' else None,
            json.dumps(form_data.get('camp_weeks', [])),
            form_data.get('gaming_behavior'),
            form_data.get('game_restrictions'),
            form_data.get('bringing_own_switch') == 'true',
            form_data.get('favorite_games'),
            form_data.get('games_owned'),  # New field
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
        
        # Send confirmation email asynchronously to avoid timeout
        email_data = form_data.copy()
        email_data['submission_id'] = submission_id
        email_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Start email sending in background thread
        import threading
        
        def send_all_emails(registration_data):
            """Send both confirmation and admin notification emails."""
            send_confirmation_email(registration_data)  # To parent
            send_admin_notification(registration_data)  # To admin
        
        email_thread = threading.Thread(target=send_all_emails, args=(email_data,))
        email_thread.daemon = True
        email_thread.start()
        
        # Return success immediately - don't wait for email
        return jsonify({
            'success': True,
            'submission_id': submission_id,
            'message': 'Registration submitted successfully! A confirmation email will be sent shortly.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'errors': [str(e)]}), 500

@app.route('/submit_fast', methods=['POST'])
def submit_registration_fast():
    """Fast submission without email - backup endpoint."""
    try:
        # Get form data
        form_data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate data
        errors, warnings = validate_form_data(form_data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Generate submission ID
        submission_id = f"CP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form_data['child_last_name'][:3].upper()}"
        
        # Save to database (same as main route but no email)
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO registrations (
                submission_id, status, payment_status, parent_email, parent_phone, emergency_contact_name,
                emergency_contact_phone, child_first_name, child_last_name,
                child_age, child_grade, child_gender, is_returning_camper,
                previous_year, previous_instructor, returning_camper_details,
                camp_weeks, gaming_behavior, game_restrictions, bringing_own_switch,
                favorite_games, games_owned, console_experience, has_allergies, allergy_details,
                has_sensory_issues, sensory_details, medical_conditions,
                photo_permission, marketing_permission, tshirt_size,
                how_heard_about_camp, additional_notes, raw_form_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission_id, 'pending', 'pending',
            form_data.get('parent_email'), form_data.get('parent_phone'),
            form_data.get('emergency_contact_name'), form_data.get('emergency_contact_phone'),
            form_data.get('child_first_name'), form_data.get('child_last_name'),
            int(form_data.get('child_age', 0)), form_data.get('child_grade'), form_data.get('child_gender'),
            form_data.get('is_returning_camper') == 'true',
            form_data.get('previous_year') if form_data.get('is_returning_camper') == 'true' else None,
            form_data.get('previous_instructor') if form_data.get('is_returning_camper') == 'true' else None,
            form_data.get('returning_camper_details') if form_data.get('is_returning_camper') == 'true' else None,
            json.dumps(form_data.get('camp_weeks', [])), form_data.get('gaming_behavior'),
            form_data.get('game_restrictions'), form_data.get('bringing_own_switch') == 'true',
            form_data.get('favorite_games'), form_data.get('games_owned'), form_data.get('console_experience'),
            form_data.get('has_allergies') == 'true', form_data.get('allergy_details'),
            form_data.get('has_sensory_issues') == 'true', form_data.get('sensory_details'),
            form_data.get('medical_conditions'), form_data.get('photo_permission') == 'true',
            form_data.get('marketing_permission') == 'true', form_data.get('tshirt_size'),
            form_data.get('how_heard_about_camp'), form_data.get('additional_notes'),
            json.dumps(form_data)
        ))
        
        conn.commit()
        conn.close()
        
        # Sync to main database
        sync_to_main_database(form_data, submission_id)
        
        # Return success immediately - no email attempt
        return jsonify({
            'success': True,
            'submission_id': submission_id,
            'message': 'Registration submitted successfully! Email confirmation will be sent manually within 24 hours.'
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
            
            # Insert camper data
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
            
            # Get the camper_id for game library integration
            camper_id = cursor.lastrowid
            
            # Process game data for game library integration
            process_camper_games_for_library(cursor, camper_id, form_data, submission_id)
            
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Error syncing to main database: {e}")

def process_camper_games_for_library(cursor, camper_id, form_data, submission_id):
    """Process and add camper's games to the game library system."""
    try:
        # Ensure game library tables exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                total_owned INTEGER DEFAULT 0,
                available INTEGER DEFAULT 0,
                checked_out INTEGER DEFAULT 0,
                category TEXT DEFAULT 'Unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camper_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camper_id INTEGER,
                game_id INTEGER,
                submission_id TEXT,
                source TEXT DEFAULT 'registration',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (camper_id) REFERENCES campers (id),
                FOREIGN KEY (game_id) REFERENCES games (id),
                UNIQUE(camper_id, game_id)
            )
        ''')
        
        # Extract games from both games_owned and favorite_games fields
        games_owned = form_data.get('games_owned', '')
        favorite_games = form_data.get('favorite_games', '')
        console_experience = form_data.get('console_experience', '')
        
        # Prioritize explicit games_owned field, then supplement with other fields
        primary_game_text = games_owned.strip()
        supplementary_text = f"{favorite_games} {console_experience}".strip()
        
        games = []
        
        # Process explicit games_owned field first (higher confidence)
        if primary_game_text:
            owned_games = extract_games_from_text(primary_game_text, high_confidence=True)
            games.extend(owned_games)
            print(f"🎮 Found {len(owned_games)} games from 'games_owned' field")
        
        # Then process other fields (lower confidence, avoid duplicates)
        if supplementary_text:
            additional_games = extract_games_from_text(supplementary_text, high_confidence=False)
            # Only add games not already found
            new_games = [g for g in additional_games if g not in games]
            games.extend(new_games)
            print(f"🎯 Found {len(new_games)} additional games from other fields")
            
            for game_name in games:
                # Insert or update game in games table
                cursor.execute('''
                    INSERT OR IGNORE INTO games (name, total_owned, available) 
                    VALUES (?, 1, 1)
                ''', (game_name,))
                
                # Update count if game already exists
                cursor.execute('''
                    UPDATE games 
                    SET total_owned = total_owned + 1, available = available + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ? AND id NOT IN (
                        SELECT game_id FROM camper_games WHERE camper_id = ?
                    )
                ''', (game_name, camper_id))
                
                # Get game_id
                cursor.execute('SELECT id FROM games WHERE name = ?', (game_name,))
                game_result = cursor.fetchone()
                if game_result:
                    game_id = game_result[0]
                    
                    # Link camper to game
                    cursor.execute('''
                        INSERT OR IGNORE INTO camper_games 
                        (camper_id, game_id, submission_id, source) 
                        VALUES (?, ?, ?, 'registration')
                    ''', (camper_id, game_id, submission_id))
                    
        print(f"✅ Processed games for camper {camper_id}: {len(games) if 'games' in locals() else 0} games found")
        
    except Exception as e:
        print(f"❌ Error processing games for library: {e}")

def extract_games_from_text(text, high_confidence=True):
    """Extract game names from free-form text input."""
    if not text:
        return []
    
    # Common game names and patterns
    known_games = [
        'Minecraft', 'Fortnite', 'Roblox', 'Among Us', 'Fall Guys',
        'Super Mario', 'Pokemon', 'Zelda', 'Smash Bros', 'Mario Kart',
        'Overwatch', 'Rocket League', 'Splatoon', 'Animal Crossing',
        'Stardew Valley', 'Terraria', 'Valorant', 'Apex Legends',
        'Destiny', 'Call of Duty', 'FIFA', 'NBA 2K', 'Madden',
        'Monopoly', 'Scrabble', 'Chess', 'Checkers', 'UNO',
        'Settlers of Catan', 'Catan', 'Risk', 'Clue', 'Sorry',
        'Yahtzee', 'Battleship', 'Connect 4', 'Jenga', 'Twister',
        'Pictionary', 'Trivial Pursuit', 'Life', 'Apples to Apples',
        'Cards Against Humanity', 'Exploding Kittens', 'Ticket to Ride'
    ]
    
    games_found = []
    text_lower = text.lower()
    
    # Look for known games first (high confidence)
    for game in known_games:
        if game.lower() in text_lower:
            games_found.append(game)
    
    if high_confidence:
        # For explicit "games owned" field, be more aggressive in extraction
        # Split by common separators
        import re
        
        # Split by commas, newlines, semicolons
        potential_games = re.split(r'[,\n;]+', text)
        
        for item in potential_games:
            item = item.strip()
            if len(item) > 2 and item not in games_found:
                # Clean up the game name
                cleaned = re.sub(r'^\W+|\W+$', '', item)  # Remove leading/trailing punctuation
                if len(cleaned) > 2:
                    games_found.append(cleaned.title())  # Title case for consistency
    else:
        # For other fields, be more conservative
        potential_games = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
        
        # Filter out common non-game words
        exclude_words = ['Yes', 'No', 'The', 'And', 'Or', 'But', 'Very', 'Really', 'Pretty', 'Good', 'Bad', 'Fun', 'Great', 'Love', 'Like', 'Play', 'Game', 'Games', 'Nintendo', 'Switch', 'Xbox', 'PlayStation']
        
        for potential in potential_games:
            if (potential not in exclude_words and 
                len(potential) > 3 and 
                potential not in games_found):
                games_found.append(potential)
    
    return list(set(games_found))  # Remove duplicates

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            session.permanent = True
            flash('Successfully logged in as admin', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_authenticated', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@require_admin_auth
def admin_dashboard():
    """Admin dashboard for viewing registrations with live session tracking."""
    try:
        conn = sqlite3.connect(REGISTRATION_DB)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('''
            SELECT * FROM registrations 
            ORDER BY timestamp DESC
        ''')
        
        registrations = [dict(row) for row in cursor.fetchall()]
        
        # Calculate live session statistics
        total_registrations = len(registrations)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Today's registrations
        todays_registrations = [r for r in registrations if r['timestamp'] and r['timestamp'].startswith(today)]
        
        # Week's registrations
        from datetime import timedelta
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        weeks_registrations = [r for r in registrations if r['timestamp'] and r['timestamp'] >= week_start]
        
        # Payment status tracking
        paid_count = len([r for r in registrations if r['payment_status'] == 'paid'])
        pending_payment = len([r for r in registrations if r['payment_status'] == 'pending'])
        
        # Camper type breakdown
        returning_campers = len([r for r in registrations if r['is_returning_camper']])
        new_campers = total_registrations - returning_campers
        
        # Switch tracking
        bringing_switch = len([r for r in registrations if r['bringing_own_switch']])
        
        # Special needs tracking
        has_allergies = len([r for r in registrations if r['has_allergies']])
        has_sensory_issues = len([r for r in registrations if r['has_sensory_issues']])
        
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
        print(f"❌ Admin dashboard error: {str(e)}")
        return f"Admin dashboard error: {str(e)}", 500

@app.route('/admin/historical')
@require_admin_auth
def admin_historical():
    """Admin page for viewing historical registrations for verification."""
    # Get historical data from main database
    historical_data = []
    main_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'camp_power_up.db')
    
    if os.path.exists(main_db_path):
        try:
            conn = sqlite3.connect(main_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT childs_first_name as first_name, 
                       childs_last_name as last_name, 
                       email_address as email, 
                       age, 
                       grade, 
                       has_your_child_attended_camp_power_up_before as is_returning,
                       allergies as has_allergies, 
                       will_your_child_be_bringing_their_own_personal_switch as bringing_switch,
                       what_games_do_they_enjoy_playing as favorite_games,
                       timestamp
                FROM registrations 
                ORDER BY childs_first_name, childs_last_name
            ''')
            historical_data = [dict(row) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Error accessing main database: {e}")
            historical_data = []
    
    # Also get CSV data
    csv_data = []
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'Camp_Power_Up_past_forms - Sheet1.csv')
    
    if os.path.exists(csv_path):
        import csv
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Extract relevant fields
                    first_name = ''
                    last_name = ''
                    email = ''
                    
                    for field, value in row.items():
                        if 'first name' in field.lower() or 'childs first' in field.lower():
                            first_name = value.strip()
                        elif 'last name' in field.lower() or 'childs last' in field.lower():
                            last_name = value.strip()
                        elif 'email' in field.lower():
                            email = value.strip()
                    
                    if first_name and last_name:
                        csv_data.append({
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'source': 'CSV'
                        })
        except Exception as e:
            print(f"Error reading CSV: {e}")
    
    # Check if we have any historical data
    total_historical = len(historical_data) + len(csv_data)
    
    return render_template('admin_historical.html', 
                         historical_data=historical_data, 
                         csv_data=csv_data,
                         has_historical_data=total_historical > 0,
                         total_historical_count=total_historical)

@app.route('/admin/config')
@require_admin_auth
def admin_config():
    """Admin interface for updating camp configuration."""
    try:
        validate_config()
        return render_template('admin_config.html', config=CAMP_CONFIG)
    except ValueError as e:
        return f"Configuration error: {e}", 500

@app.route('/admin/update-config', methods=['POST'])
@require_admin_auth
def update_config():
    """Update the camp configuration."""
    try:
        data = request.get_json()
        
        # Update CAMP_CONFIG with new values
        CAMP_CONFIG["camp_name"] = data.get("camp_name", CAMP_CONFIG["camp_name"])
        CAMP_CONFIG["camp_subtitle"] = data.get("camp_subtitle", CAMP_CONFIG["camp_subtitle"])
        CAMP_CONFIG["camp_dates"] = data.get("camp_dates", CAMP_CONFIG["camp_dates"])
        CAMP_CONFIG["camp_days"] = int(data.get("camp_days", CAMP_CONFIG["camp_days"]))
        CAMP_CONFIG["daily_hours"] = data.get("daily_hours", CAMP_CONFIG["daily_hours"])
        CAMP_CONFIG["final_payment_due"] = data.get("final_payment_due", CAMP_CONFIG["final_payment_due"])
        
        # Update pricing
        CAMP_CONFIG["pricing"]["returning_camper"]["deposit"] = int(data.get("returning_deposit", 50))
        CAMP_CONFIG["pricing"]["returning_camper"]["final_payment"] = int(data.get("returning_final", 130))
        CAMP_CONFIG["pricing"]["returning_camper"]["total"] = (
            CAMP_CONFIG["pricing"]["returning_camper"]["deposit"] + 
            CAMP_CONFIG["pricing"]["returning_camper"]["final_payment"]
        )
        
        CAMP_CONFIG["pricing"]["new_camper"]["deposit"] = int(data.get("new_deposit", 50))
        CAMP_CONFIG["pricing"]["new_camper"]["final_payment"] = int(data.get("new_final", 150))
        CAMP_CONFIG["pricing"]["new_camper"]["total"] = (
            CAMP_CONFIG["pricing"]["new_camper"]["deposit"] + 
            CAMP_CONFIG["pricing"]["new_camper"]["final_payment"]
        )
        
        # Write updated config back to file
        update_config_file()
        
        validate_config()
        
        return jsonify({"success": True, "message": "Configuration updated successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def update_config_file():
    """Write the current CAMP_CONFIG back to the camp_config.py file."""
    import json
    
    config_content = f'''#!/usr/bin/env python3
"""
Camp Power-Up Session Configuration
==================================

This file contains the dynamic camp session information that changes
between different camp offerings throughout the year.

Update this file for each new camp session rather than modifying templates.
LAST UPDATED: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from datetime import datetime

# Current Camp Session Configuration
CAMP_CONFIG = {json.dumps(CAMP_CONFIG, indent=4)}

# Dynamic text generation functions
def get_camp_title():
    """Get the formatted camp title."""
    return CAMP_CONFIG["camp_name"]

def get_camp_subtitle():
    """Get the camp subtitle/description."""
    return CAMP_CONFIG["camp_subtitle"]

def get_pricing_text():
    """Generate the pricing information text."""
    returning = CAMP_CONFIG["pricing"]["returning_camper"]
    new = CAMP_CONFIG["pricing"]["new_camper"]
    
    return {{
        "returning_text": f"Returning Campers: ${{returning['deposit']}} deposit + ${{returning['final_payment']}} final payment = ${{returning['total']}} total",
        "new_text": f"New Campers: ${{new['deposit']}} deposit + ${{new['final_payment']}} final payment = ${{new['total']}} total",
        "payment_deadline": f"Final payment due before {{CAMP_CONFIG['final_payment_due']}}. Camp runs {{CAMP_CONFIG['camp_dates']}}, {{CAMP_CONFIG['daily_hours']}} daily."
    }}

def get_session_summary():
    """Get a complete session summary for admin reference."""
    pricing = get_pricing_text()
    return {{
        "title": get_camp_title(),
        "subtitle": get_camp_subtitle(),
        "dates": CAMP_CONFIG["camp_dates"],
        "duration": f"{{CAMP_CONFIG['camp_days']}} days",
        "daily_schedule": CAMP_CONFIG["daily_hours"],
        "pricing": pricing,
        "features": CAMP_CONFIG.get("special_features", []),
        "status": "Open" if CAMP_CONFIG.get("registration_open", True) else "Closed"
    }}

def validate_config():
    """Validate that all required config fields are present."""
    required_fields = ["camp_name", "camp_dates", "camp_days", "daily_hours", "pricing"]
    missing_fields = []
    
    for field in required_fields:
        if field not in CAMP_CONFIG or not CAMP_CONFIG[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required config fields: {{missing_fields}}")
    
    # Validate pricing structure
    for camper_type in ["returning_camper", "new_camper"]:
        pricing = CAMP_CONFIG["pricing"][camper_type]
        total = pricing["deposit"] + pricing["final_payment"]
        if total != pricing["total"]:
            raise ValueError(f"Pricing calculation error for {{camper_type}}: {{total}} != {{pricing['total']}}")
    
    return True
'''
    
    with open('camp_config.py', 'w') as f:
        f.write(config_content)

# Edit and Delete Camper Routes
@app.route('/admin/edit/<int:registration_id>')
@require_admin_auth
def edit_camper(registration_id):
    """Show edit form for a camper registration."""
    try:
        conn = sqlite3.connect(REGISTRATION_DB)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('''
            SELECT * FROM registrations WHERE id = ?
        ''', (registration_id,))
        
        registration = cursor.fetchone()
        conn.close()
        
        if not registration:
            flash('Registration not found', 'error')
            return redirect(url_for('admin_dashboard'))
        
        registration_dict = dict(registration)
        
        return render_template('admin_edit_camper.html', registration=registration_dict)
        
    except Exception as e:
        flash(f'Error loading registration: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/update/<int:registration_id>', methods=['POST'])
@require_admin_auth
def update_camper(registration_id):
    """Update a camper registration."""
    try:
        form_data = request.form.to_dict()
        
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        # Update registration with new data
        cursor.execute('''
            UPDATE registrations SET
                parent_email = ?, parent_phone = ?, emergency_contact_name = ?, emergency_contact_phone = ?,
                child_first_name = ?, child_last_name = ?, child_age = ?, child_grade = ?, child_gender = ?,
                is_returning_camper = ?, gaming_behavior = ?, game_restrictions = ?, bringing_own_switch = ?,
                favorite_games = ?, console_experience = ?, has_allergies = ?, allergy_details = ?,
                has_sensory_issues = ?, sensory_details = ?, medical_conditions = ?, photo_permission = ?,
                marketing_permission = ?, tshirt_size = ?, how_heard_about_camp = ?, additional_notes = ?,
                payment_status = ?, status = ?
            WHERE id = ?
        ''', (
            form_data.get('parent_email'),
            form_data.get('parent_phone'),
            form_data.get('emergency_contact_name'),
            form_data.get('emergency_contact_phone'),
            form_data.get('child_first_name'),
            form_data.get('child_last_name'),
            int(form_data.get('child_age', 0)),
            form_data.get('child_grade'),
            form_data.get('child_gender'),
            form_data.get('is_returning_camper') == 'on',
            form_data.get('gaming_behavior'),
            form_data.get('game_restrictions'),
            form_data.get('bringing_own_switch') == 'on',
            form_data.get('favorite_games'),
            form_data.get('console_experience'),
            form_data.get('has_allergies') == 'on',
            form_data.get('allergy_details'),
            form_data.get('has_sensory_issues') == 'on',
            form_data.get('sensory_details'),
            form_data.get('medical_conditions'),
            form_data.get('photo_permission') == 'on',
            form_data.get('marketing_permission') == 'on',
            form_data.get('tshirt_size'),
            form_data.get('how_heard_about_camp'),
            form_data.get('additional_notes'),
            form_data.get('payment_status', 'pending'),
            form_data.get('status', 'pending'),
            registration_id
        ))
        
        conn.commit()
        conn.close()
        
        flash('Registration updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        flash(f'Error updating registration: {str(e)}', 'error')
        return redirect(url_for('edit_camper', registration_id=registration_id))

@app.route('/admin/delete/<int:registration_id>', methods=['POST'])
@require_admin_auth
def delete_camper(registration_id):
    """Delete a camper registration."""
    try:
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        # Get camper info for confirmation message
        cursor.execute('SELECT child_first_name, child_last_name FROM registrations WHERE id = ?', (registration_id,))
        camper = cursor.fetchone()
        
        if camper:
            cursor.execute('DELETE FROM registrations WHERE id = ?', (registration_id,))
            conn.commit()
            flash(f'Registration for {camper[0]} {camper[1]} has been deleted.', 'success')
        else:
            flash('Registration not found.', 'error')
        
        conn.close()
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        flash(f'Error deleting registration: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

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
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM registrations WHERE submission_id = ?
        ''', (submission_id,))
        
        registration = cursor.fetchone()
        conn.close()
        
        if not registration:
            return "Registration not found", 404
        
        # Convert row to dictionary - must match database schema order
        columns = [
            'id', 'submission_id', 'timestamp', 'status', 'payment_status',
            'parent_email', 'parent_phone', 'emergency_contact_name', 'emergency_contact_phone',
            'child_first_name', 'child_last_name', 'child_age', 'child_grade', 'child_gender',
            'is_returning_camper', 'camp_weeks', 'gaming_behavior', 'game_restrictions',
            'bringing_own_switch', 'favorite_games', 'console_experience', 'has_allergies',
            'allergy_details', 'has_sensory_issues', 'sensory_details', 'medical_conditions',
            'photo_permission', 'marketing_permission', 'tshirt_size', 'how_heard_about_camp',
            'additional_notes', 'raw_form_data', 'games_owned', 'previous_year',
            'previous_instructor', 'returning_camper_details'
        ]
        
        registration_dict = dict(zip(columns, registration))
        
        return render_template('confirmation.html', registration=registration_dict)
        
    except Exception as e:
        return f"Error retrieving registration: {str(e)}", 500

@app.route('/admin/verify-returning-campers')
@require_admin_auth
def verify_returning_campers():
    """Admin tool to review returning camper claims."""
    conn = sqlite3.connect(REGISTRATION_DB)
    cursor = conn.cursor()
    
    # Get all registrations claiming to be returning campers
    cursor.execute('''
        SELECT 
            id, submission_id, child_first_name, child_last_name, parent_email,
            previous_year, previous_instructor, returning_camper_details,
            timestamp
        FROM registrations 
        WHERE is_returning_camper = 1
        ORDER BY timestamp DESC
    ''')
    
    returning_campers = cursor.fetchall()
    verified_campers = []
    
    for camper in returning_campers:
        # Check if this camper has previous registrations
        validation_result = check_returning_camper_validity(
            camper[2], camper[3], camper[4]  # first_name, last_name, email
        )
        
        verified_campers.append({
            'id': camper[0],
            'submission_id': camper[1],
            'name': f"{camper[2]} {camper[3]}",
            'email': camper[4],
            'previous_year': camper[5],
            'previous_instructor': camper[6],
            'details': camper[7],
            'timestamp': camper[8],
            'validation': validation_result,
            'verified': validation_result['is_likely_returning']
        })
    
    conn.close()
    
    # Create simple HTML response
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Returning Camper Verification</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .verified { background: #d4edda; border-left: 4px solid #28a745; }
            .unverified { background: #f8d7da; border-left: 4px solid #dc3545; }
            .camper { padding: 15px; margin: 10px 0; border-radius: 5px; }
            .warning { color: #721c24; font-weight: bold; }
            .details { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 3px; }
            .back-btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🔍 Returning Camper Verification Report</h1>
        <a href="/admin" class="back-btn">← Back to Admin Panel</a>
        <p>This report shows all registrations claiming returning camper status and their verification status.</p>
    '''
    
    if not verified_campers:
        html += '<p><em>No returning camper registrations found.</em></p>'
    
    for camper in verified_campers:
        status_class = 'verified' if camper['verified'] else 'unverified'
        status_text = '✅ VERIFIED' if camper['verified'] else '⚠️ NEEDS REVIEW'
        
        html += f'''
        <div class="camper {status_class}">
            <h3>{camper['name']} - {status_text}</h3>
            <p><strong>Email:</strong> {camper['email']}</p>
            <p><strong>Registration ID:</strong> {camper['submission_id']}</p>
            <p><strong>Submitted:</strong> {camper['timestamp']}</p>
            
            <div class="details">
                <p><strong>Previous Year Claimed:</strong> {camper['previous_year'] or 'Not provided'}</p>
                <p><strong>Staff Remembered:</strong> {camper['previous_instructor'] or 'Not provided'}</p>
                <p><strong>Previous Experience:</strong> {camper['details'] or 'Not provided'}</p>
            </div>
            
            <p><strong>Database Check:</strong> 
                {camper['validation']['exact_matches']} exact matches, 
                {camper['validation']['name_matches']} name matches
            </p>
            
            {f'<p class="warning">⚠️ ACTION REQUIRED: Contact this family to verify attendance or request additional payment.</p>' if not camper['verified'] else ''}
        </div>
        '''
    
    html += '''
        <div style="margin-top: 30px; padding: 20px; background: #e7f3ff; border-radius: 5px;">
            <h3>📋 Action Items for Unverified Claims:</h3>
            <ol>
                <li>Contact the family directly to verify previous attendance</li>
                <li>Check with previous year staff if names are provided</li>
                <li>Request payment adjustment if claim is invalid</li>
                <li>Update registration record with verification status</li>
            </ol>
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/admin/analytics')
@require_admin_auth
def admin_analytics():
    """Admin analytics dashboard showing registration statistics and trends."""
    conn = sqlite3.connect(REGISTRATION_DB)
    conn.row_factory = sqlite3.Row
    
    # Get current registrations
    cursor = conn.execute('''
        SELECT * FROM registrations 
        ORDER BY timestamp DESC
    ''')
    registrations = [dict(row) for row in cursor.fetchall()]
    
    # Calculate analytics
    total_registrations = len(registrations)
    returning_campers = len([r for r in registrations if r['is_returning_camper']])
    new_campers = total_registrations - returning_campers
    bringing_switch = len([r for r in registrations if r.get('bringing_own_switch')])
    
    # Age distribution
    age_groups = {}
    for reg in registrations:
        age = reg.get('child_age', 0)
        if age:
            if age < 6:
                age_groups['5 and under'] = age_groups.get('5 and under', 0) + 1
            elif age <= 8:
                age_groups['6-8 years'] = age_groups.get('6-8 years', 0) + 1
            elif age <= 10:
                age_groups['9-10 years'] = age_groups.get('9-10 years', 0) + 1
            elif age <= 12:
                age_groups['11-12 years'] = age_groups.get('11-12 years', 0) + 1
            else:
                age_groups['13+ years'] = age_groups.get('13+ years', 0) + 1
    
    # Registration timeline (last 30 days)
    from datetime import datetime, timedelta
    timeline = {}
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    for reg in registrations:
        reg_date = datetime.strptime(reg['timestamp'][:10], '%Y-%m-%d')
        if reg_date >= thirty_days_ago:
            date_str = reg_date.strftime('%Y-%m-%d')
            timeline[date_str] = timeline.get(date_str, 0) + 1
    
    conn.close()
    
    analytics_data = {
        'total_registrations': total_registrations,
        'returning_campers': returning_campers,
        'new_campers': new_campers,
        'bringing_switch': bringing_switch,
        'age_groups': age_groups,
        'timeline': timeline,
        'registrations': registrations
    }
    
    return render_template('admin_analytics.html', **analytics_data)

@app.route('/admin/registration-stats')
@require_admin_auth
def registration_stats():
    """Show registration statistics including pricing breakdown."""
    conn = sqlite3.connect(REGISTRATION_DB)
    cursor = conn.cursor()
    
    # Get counts
    cursor.execute('SELECT COUNT(*) FROM registrations WHERE is_returning_camper = 1')
    returning_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM registrations WHERE is_returning_camper = 0')
    new_count = cursor.fetchone()[0]
    
    # Calculate potential revenue impact
    new_price = CAMP_CONFIG['pricing']['new_camper']['total']
    returning_price = CAMP_CONFIG['pricing']['returning_camper']['total']
    
    total_registrations = returning_count + new_count
    current_revenue = (returning_count * returning_price) + (new_count * new_price)
    if_all_new_revenue = total_registrations * new_price
    potential_lost_revenue = if_all_new_revenue - current_revenue
    
    return jsonify({
        'total_registrations': total_registrations,
        'returning_campers': returning_count,
        'new_campers': new_count,
        'pricing': {
            'new_camper_price': new_price,
            'returning_camper_price': returning_price,
            'discount_amount': new_price - returning_price
        },
        'revenue': {
            'current_total': current_revenue,
            'potential_if_all_new': if_all_new_revenue,
            'potential_lost': potential_lost_revenue
        }
    })

@app.route('/admin/send-reminder/<submission_id>', methods=['POST'])
@require_admin_auth
def send_reminder(submission_id):
    """Send payment reminder email."""
    try:
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT child_first_name, child_last_name, parent_email, payment_status 
            FROM registrations WHERE submission_id = ?
        ''', (submission_id,))
        
        registration = cursor.fetchone()
        if not registration:
            return jsonify({'status': 'error', 'message': 'Registration not found'}), 404
            
        child_name = f"{registration[0]} {registration[1]}"
        parent_email = registration[2]
        payment_status = registration[3]
        
        if payment_status == 'paid':
            return jsonify({'status': 'error', 'message': 'Registration is already marked as paid'})
        
        # Send email if email is configured
        if EMAIL_AVAILABLE and EMAIL_CONFIG['email_password']:
            subject = "Camp Power-Up Payment Reminder"
            body = f"""
Dear Parent/Guardian,

This is a friendly reminder that payment is due for {child_name}'s registration at Camp Power-Up.

Please submit your $50 deposit at your earliest convenience to secure your spot.

Payment methods:
- Venmo: @YourVenmoHandle
- Cash: Bring to camp or mail to address
- Check: Make payable to "Camp Power-Up"

Please include "{child_name}" in your payment memo.

If you have already paid, please disregard this message.

Thank you!
Camp Power-Up Team

Submission ID: {submission_id}
"""
            
            if send_confirmation_email(parent_email, subject, body):
                conn.close()
                return jsonify({'status': 'success', 'message': 'Reminder email sent successfully'})
            else:
                conn.close()
                return jsonify({'status': 'error', 'message': 'Failed to send email'})
        else:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Email not configured'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/mark-paid/<submission_id>', methods=['POST'])
@require_admin_auth
def mark_paid(submission_id):
    """Mark a registration as paid."""
    try:
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE registrations SET payment_status = ? WHERE submission_id = ?', 
                      ('paid', submission_id))
        
        if cursor.rowcount == 0:
            return jsonify({'status': 'error', 'message': 'Registration not found'}), 404
            
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Registration marked as paid'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/export', methods=['GET'])
@require_admin_auth
def export_registrations():
    """Export registration data as CSV."""
    import csv
    from flask import Response
    import io
    
    try:
        conn = sqlite3.connect(REGISTRATION_DB)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT submission_id, timestamp, child_first_name, child_last_name, 
                   child_age, parent_first_name, parent_last_name, parent_email,
                   parent_phone, emergency_contact_name, emergency_contact_phone,
                   has_allergies, allergies_description, has_medical_conditions,
                   medical_conditions_description, is_returning_camper,
                   returning_years, how_heard_about_camp, additional_comments
            FROM registrations 
            ORDER BY timestamp DESC
        ''')
        
        registrations = cursor.fetchall()
        conn.close()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Submission ID', 'Registration Date', 'Child First Name', 'Child Last Name',
            'Age', 'Parent First Name', 'Parent Last Name', 'Parent Email',
            'Parent Phone', 'Emergency Contact', 'Emergency Phone',
            'Has Allergies', 'Allergies', 'Has Medical Conditions', 'Medical Conditions',
            'Returning Camper', 'Previous Years', 'How Heard About Camp', 'Comments'
        ])
        
        # Write data rows
        for reg in registrations:
            writer.writerow([
                reg['submission_id'], reg['timestamp'], reg['child_first_name'], reg['child_last_name'],
                reg['child_age'], reg['parent_first_name'], reg['parent_last_name'], reg['parent_email'],
                reg['parent_phone'], reg['emergency_contact_name'], reg['emergency_contact_phone'],
                'Yes' if reg['has_allergies'] else 'No', reg['allergies_description'] or '',
                'Yes' if reg['has_medical_conditions'] else 'No', reg['medical_conditions_description'] or '',
                'Yes' if reg['is_returning_camper'] else 'No', reg['returning_years'] or '',
                reg['how_heard_about_camp'] or '', reg['additional_comments'] or ''
            ])
        
        output.seek(0)
        
        # Create response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=camp_registrations_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
        return response
        
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/database-info')
@require_admin_auth
def database_info():
    """Show database configuration and migration options."""
    return jsonify({
        'database_type': 'PostgreSQL' if DB_CONFIG['is_production'] else 'SQLite',
        'is_production': DB_CONFIG['is_production'],
        'database_url_set': bool(DB_CONFIG.get('database_url')),
        'persistence': 'Persistent (PostgreSQL)' if DB_CONFIG['is_production'] else 'Ephemeral (SQLite)',
        'note': 'Data persists across deployments' if DB_CONFIG['is_production'] else 'Data is lost on deployment'
    })

@app.route('/debug/email-config')
def email_config_public_debug():
    """Public debug endpoint for email configuration (temporary for troubleshooting)."""
    camp_email = os.environ.get('CAMP_EMAIL', 'NOT SET')
    camp_password = os.environ.get('CAMP_EMAIL_PASSWORD', 'NOT SET')
    smtp_server = os.environ.get('SMTP_SERVER', 'NOT SET')
    
    # Check SendGrid configuration
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY', '')
    sendgrid_from_email = os.environ.get('SENDGRID_FROM_EMAIL', '')
    sendgrid_from_name = os.environ.get('SENDGRID_FROM_NAME', '')
    has_sendgrid = bool(sendgrid_api_key)
    
    response = {
        'camp_email': camp_email,
        'email_available': EMAIL_AVAILABLE,
        'environment': 'production' if DB_CONFIG['is_production'] else 'development',
        'email_method': 'sendgrid' if has_sendgrid else 'smtp'
    }
    
    if has_sendgrid:
        response.update({
            'sendgrid_configured': True,
            'sendgrid_from_email': sendgrid_from_email,
            'sendgrid_from_name': sendgrid_from_name,
            'sendgrid_api_key_length': len(sendgrid_api_key),
            'email_vars_found': len([k for k in os.environ.keys() if 'SENDGRID' in k])
        })
    else:
        response.update({
            'sendgrid_configured': False,
            'has_password': 'YES' if camp_password and camp_password != 'NOT SET' else 'NO',
            'password_length': len(camp_password) if camp_password and camp_password != 'NOT SET' else 0,
            'smtp_server': smtp_server,
            'email_vars_found': len([k for k in os.environ.keys() if 'CAMP' in k or 'SMTP' in k])
        })
    
    return jsonify(response)

@app.route('/admin/email-debug')
@require_admin_auth
def email_debug():
    """Debug email configuration without exposing sensitive data."""
    camp_email = os.environ.get('CAMP_EMAIL', 'NOT SET')
    camp_password = os.environ.get('CAMP_EMAIL_PASSWORD', 'NOT SET')
    smtp_server = os.environ.get('SMTP_SERVER', 'NOT SET')
    
    return jsonify({
        'camp_email': camp_email,
        'has_password': 'YES' if camp_password and camp_password != 'NOT SET' else 'NO',
        'password_length': len(camp_password) if camp_password and camp_password != 'NOT SET' else 0,
        'smtp_server': smtp_server,
        'email_vars_found': len([k for k in os.environ.keys() if 'CAMP' in k or 'SMTP' in k]),
        'all_env_vars_count': len(os.environ)
    })

@app.route('/admin/test-email-send/<test_email>')
@require_admin_auth
def test_email_send(test_email):
    """Test email sending functionality."""
    try:
        # Create test registration data
        test_registration = {
            'child_first_name': 'Test',
            'child_last_name': 'Child',
            'parent_email': test_email,
            'submission_id': 'TEST_12345',
            'child_age': '8',
            'parent_name': 'Test Parent',
            'is_returning_camper': 0
        }
        
        # Use the same email sending logic as registration confirmations
        result = send_confirmation_email(test_registration)
        return jsonify({
            'success': True,
            'message': f'Test email sent to {test_email}',
            'email_result': str(result)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/test/admin-notification')
def test_admin_notification_endpoint():
    """Test admin notification email sending."""
    try:
        # Create test registration data
        test_data = {
            'child_first_name': 'TestAdmin',
            'child_last_name': 'Notification',
            'child_age': 10,
            'parent_first_name': 'Test',
            'parent_last_name': 'Parent',
            'parent_email': 'fowler0613@gmail.com',
            'parent_phone': '555-123-4567',
            'bringing_own_switch': True,
            'is_returning_camper': False,
            'submission_id': 'TEST_ADMIN_001'
        }
        
        print("🧪 Testing admin notification...")
        result = send_admin_notification(test_data)
        
        return jsonify({
            'success': True,
            'admin_notification_sent': result,
            'test_data': test_data,
            'admin_email': 'camppowerup2025@gmail.com',
            'message': 'Check camppowerup2025@gmail.com for admin notification'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

if __name__ == '__main__':
    # Initialize database (PostgreSQL on Railway, SQLite locally)
    if DB_CONFIG['is_production']:
        print("🚀 Initializing PostgreSQL database...")
        init_postgresql_tables()
    else:
        print("🔧 Initializing SQLite database...")
        init_registration_db()
        
    print("🏕️ Camp Power-Up Registration Form")
    print("=" * 40)
    print(f"📊 Database: {'PostgreSQL (Production)' if DB_CONFIG['is_production'] else 'SQLite (Local)'}")
    
    # Use PORT environment variable for Railway, fallback to 5001 for local development
    port = int(os.environ.get('PORT', 5001))
    host = '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1'
    
    print(f"📝 Registration form available at: http://{host}:{port}")
    print(f"🔧 Admin dashboard available at: http://{host}:{port}/admin")
    app.run(debug=False, host=host, port=port)
else:
    # When imported by gunicorn, initialize the appropriate database
    try:
        if DB_CONFIG['is_production']:
            print("🚀 Initializing PostgreSQL for production...")
            init_postgresql_tables()
            print("✅ PostgreSQL database initialized")
        else:
            init_registration_db()
            print("✅ SQLite database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        # Continue anyway - don't crash the app
