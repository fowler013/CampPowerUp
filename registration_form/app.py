#!/usr/bin/env python3
"""
Camp Power-Up Registration Form Application - Clean Version
=========================================================
Restored admin functionality with PostgreSQL database
"""

import os
import sqlite3
import uuid
import hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from database_config import get_db_connection, init_postgresql_tables, DB_CONFIG
from camp_config import CAMP_CONFIG, get_camp_title, get_camp_subtitle, get_pricing_text
from functools import wraps

# Import email modules
try:
    import smtplib
    import requests
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
    print("✅ Email functionality available")
except ImportError:
    EMAIL_AVAILABLE = False
    print("⚠️ Email functionality not available")

# Email configuration
EMAIL_CONFIG = {
    'use_sendgrid': True,
    'sendgrid_api_key': os.environ.get('SENDGRID_API_KEY', ''),
    'sendgrid_from_email': os.environ.get('SENDGRID_FROM_EMAIL', 'camppowerup2025@gmail.com'),
    'sendgrid_from_name': 'Camp Power-Up 2025',
    'sendgrid_reply_to': 'camppowerup2025@gmail.com',
    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
    'email_address': os.environ.get('CAMP_EMAIL', 'camppowerup2025@gmail.com'),
    'email_password': os.environ.get('CAMP_EMAIL_PASSWORD', '')
}

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'camp_power_up_registration_2025_dev_only')

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

def send_email_via_sendgrid(to_email, subject, html_content):
    """Send email using SendGrid API."""
    if not EMAIL_CONFIG['sendgrid_api_key']:
        print("❌ SendGrid API key not configured")
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
        return response.status_code == 202
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False

def send_confirmation_email(registration_data):
    """Send confirmation email to parent."""
    if not EMAIL_AVAILABLE:
        print(f"⚠️ Email not available - would send confirmation to {registration_data['parent_email']}")
        return False
    
    subject = f"Registration Confirmed - Camp Power-Up 2025 - {registration_data['child_first_name']} {registration_data['child_last_name']}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">Welcome to Camp Power-Up 2025!</h2>
        
        <p>Dear {registration_data['parent_first_name']},</p>
        
        <p>Thank you for registering <strong>{registration_data['child_first_name']} {registration_data['child_last_name']}</strong> for Camp Power-Up 2025!</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>Registration Details:</h3>
            <p><strong>Child:</strong> {registration_data['child_first_name']} {registration_data['child_last_name']} (Age {registration_data['child_age']})</p>
            <p><strong>Submission ID:</strong> {registration_data['submission_id']}</p>
            <p><strong>Registration Type:</strong> {'Returning Camper' if registration_data.get('is_returning_camper') else 'New Camper'}</p>
        </div>
        
        <div style="background: #fff3cd; padding: 20px; border-radius: 5px; border-left: 4px solid #ffc107;">
            <h3>Payment Information:</h3>
            <p><strong>Total Cost:</strong> {'$80' if registration_data.get('is_returning_camper') else '$100'}</p>
            <p><strong>Deposit:</strong> $50 (due now)</p>
            <p><strong>Final Payment:</strong> {'$30' if registration_data.get('is_returning_camper') else '$50'} (due before November 24th)</p>
            <p><strong>Payment:</strong> CashApp or Venmo to camppowerup2025@gmail.com</p>
            <p><strong>Include in memo:</strong> {registration_data['child_first_name']} {registration_data['child_last_name']}</p>
        </div>
        
        <div style="background: #d1ecf1; padding: 20px; border-radius: 5px; border-left: 4px solid #17a2b8;">
            <h3>Camp Details:</h3>
            <p><strong>Dates:</strong> November 24th-26th, 2025</p>
            <p><strong>Time:</strong> 10am-3pm daily</p>
            <p><strong>Location:</strong> Details will be sent closer to camp date</p>
        </div>
        
        <p>We're excited to have {registration_data['child_first_name']} join us for an amazing gaming experience!</p>
        
        <p>Best regards,<br>Camp Power-Up Team</p>
    </div>
    """
    
    try:
        result = send_email_via_sendgrid(registration_data['parent_email'], subject, html_content)
        if result:
            print(f"✅ Confirmation email sent to {registration_data['parent_email']}")
        else:
            print(f"❌ Failed to send confirmation email to {registration_data['parent_email']}")
        return result
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def init_registration_db():
    """Initialize the registration database."""
    try:
        # Use SQLite for Railway deployment - simpler and more reliable
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
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
        print(f"Database init error: {e}")
        # Don't crash the app if DB init fails

@app.route('/')
def index():
    """Main registration form."""
    # Create pricing object that template expects
    pricing = {
        'returning_text': 'Returning Campers: $50 deposit + $30 final payment = $80 total',
        'new_text': 'New Campers: $50 deposit + $50 final payment = $100 total', 
        'payment_deadline': 'Final payment due before November 24th. Camp runs November 24th-26th, 10am-3pm daily.'
    }
    
    return render_template('registration_form.html', 
                         camp_config=CAMP_CONFIG,
                         camp_title=get_camp_title(),
                         camp_subtitle=get_camp_subtitle(),
                         pricing_text=get_pricing_text(),
                         pricing=pricing)

@app.route('/register')
def register():
    """Registration form (alternative route)."""
    return redirect(url_for('index'))

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
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
        cursor = conn.cursor()
        
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
        
        # Add submission_id to data for email
        data['submission_id'] = submission_id
        
        # Send confirmation email
        try:
            send_confirmation_email(data)
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        return render_template('confirmation.html', 
                             submission_id=submission_id,
                             child_name=f"{data['child_first_name']} {data['child_last_name']}",
                             camp_config=CAMP_CONFIG)
                             
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
    """Admin dashboard with all registrations."""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        
        # Get registrations as dictionaries
        registrations = [dict(row) for row in cursor.fetchall()]
        
        # Calculate statistics
        total_registrations = len(registrations)
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        todays_registrations = [r for r in registrations if r['timestamp'].date() == today]
        weeks_registrations = [r for r in registrations if r['timestamp'].date() >= week_ago]
        
        paid_count = len([r for r in registrations if r['payment_status'] == 'paid'])
        pending_payment = len([r for r in registrations if r['payment_status'] == 'pending'])
        
        returning_campers = len([r for r in registrations if r['is_returning_camper']])
        new_campers = total_registrations - returning_campers
        
        bringing_switch = len([r for r in registrations if r.get('bringing_own_switch')])
        has_allergies = len([r for r in registrations if r['has_allergies']])
        has_sensory_issues = len([r for r in registrations if r.get('has_sensory_issues')])
        
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
        print(f"Admin dashboard error: {str(e)}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('admin_login'))

@app.route('/test-db')
def test_db():
    """Test database connection."""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
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

@app.route('/test-registration')
def test_registration():
    """Create a test registration to verify database functionality."""
    try:
        # Generate test submission ID
        submission_id = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}_DEMO"
        
        # Test data
        test_data = {
            'child_first_name': 'Test',
            'child_last_name': 'Camper',
            'child_age': 12,
            'parent_first_name': 'Test',
            'parent_last_name': 'Parent',
            'parent_email': 'test@example.com',
            'parent_phone': '555-123-4567',
            'emergency_contact_name': 'Emergency Contact',
            'emergency_contact_phone': '555-987-6543',
            'has_allergies': False,
            'allergies_description': '',
            'has_medical_conditions': False,
            'medical_conditions_description': '',
            'is_returning_camper': False,
            'returning_years': '',
            'how_heard_about_camp': 'Test submission',
            'additional_comments': 'This is a test registration',
            'bringing_own_switch': True,
            'has_sensory_issues': False
        }
        
        # Save to database
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
        cursor = conn.cursor()
        
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
            submission_id, test_data['child_first_name'], test_data['child_last_name'], 
            test_data['child_age'], test_data['parent_first_name'], test_data['parent_last_name'],
            test_data['parent_email'], test_data['parent_phone'], 
            test_data['emergency_contact_name'], test_data['emergency_contact_phone'],
            test_data['has_allergies'], test_data['allergies_description'],
            test_data['has_medical_conditions'], test_data['medical_conditions_description'],
            test_data['is_returning_camper'], test_data['returning_years'],
            test_data['how_heard_about_camp'], test_data['additional_comments'],
            test_data['bringing_own_switch'], test_data['has_sensory_issues']
        ))
        conn.commit()
        conn.close()
        
        # Test email functionality
        test_data['submission_id'] = submission_id
        email_sent = False
        try:
            email_sent = send_confirmation_email(test_data)
        except Exception as e:
            print(f"Email test failed: {e}")
        
        return jsonify({
            "success": True,
            "message": "Test registration created successfully!",
            "submission_id": submission_id,
            "email_sent": email_sent,
            "child_name": f"{test_data['child_first_name']} {test_data['child_last_name']}",
            "admin_url": "/admin"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/admin/debug-login')
def debug_login():
    """Debug admin login credentials."""
    return jsonify({
        "admin_username": ADMIN_USERNAME,
        "admin_password_set": "Yes" if ADMIN_PASSWORD else "No",
        "admin_password_length": len(ADMIN_PASSWORD),
        "session_logged_in": session.get('admin_logged_in', False),
        "message": "Use username: campadmin, password: PowerUp2025!"
    })

@app.route('/admin/export')
@require_admin_auth
def admin_export():
    """Export registrations as CSV."""
    try:
        import io
        import csv
        from flask import make_response
        
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=registrations[0].keys() if registrations else [])
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

@app.route('/admin/analytics')
@require_admin_auth
def admin_analytics():
    """Admin analytics page."""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Basic analytics
        total_count = len(registrations)
        returning_count = len([r for r in registrations if r.get('is_returning_camper')])
        new_count = total_count - returning_count
        
        analytics = {
            'total_registrations': total_count,
            'returning_campers': returning_count,
            'new_campers': new_count,
            'registrations': registrations
        }
        
        return render_template('admin_analytics.html', analytics=analytics, camp_config=CAMP_CONFIG)
        
    except Exception as e:
        flash(f'Analytics error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/config')
@require_admin_auth 
def admin_config():
    """Admin configuration page."""
    return render_template('admin_config.html', 
                         camp_config=CAMP_CONFIG,
                         config=app.config)

if __name__ == '__main__':
    init_registration_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)