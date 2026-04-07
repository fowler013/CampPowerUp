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
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Import camp configuration
try:
    from camp_config import CAMP_CONFIG, get_camp_title, get_camp_subtitle, get_pricing_text
except ImportError:
    # Fallback config if camp_config.py is not available
    CAMP_CONFIG = {
        'camp_name': 'Camp Power-Up 2026',
        'camp_dates': 'March 26th-27th',
        'camp_days': 2,
        'daily_hours': '10:00am-3:00pm',
        'pricing': {
            'new_camper': {'total': 100, 'deposit': 50, 'final_payment': 50},
            'returning_camper': {'total': 80, 'deposit': 50, 'final_payment': 30}
        }
    }
    def get_camp_title(): return CAMP_CONFIG['camp_name']
    def get_camp_subtitle(): return 'Nintendo Switch Gaming Camp Registration'
    def get_pricing_text():
        return {
            'returning_text': f"Returning Campers: ${CAMP_CONFIG['pricing']['returning_camper']['deposit']} deposit + ${CAMP_CONFIG['pricing']['returning_camper']['final_payment']} final = ${CAMP_CONFIG['pricing']['returning_camper']['total']} total",
            'new_text': f"New Campers: ${CAMP_CONFIG['pricing']['new_camper']['deposit']} deposit + ${CAMP_CONFIG['pricing']['new_camper']['final_payment']} final = ${CAMP_CONFIG['pricing']['new_camper']['total']} total",
            'payment_deadline': f"Camp runs {CAMP_CONFIG['camp_dates']}, {CAMP_CONFIG['daily_hours']} daily."
        }

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Configure pricing in Flask config for templates (from camp_config)
app.config['pricing'] = CAMP_CONFIG.get('pricing', {
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
})

# Railway-aware database setup for persistent data  
def get_database_path():
    """Get the appropriate database path based on environment."""
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("🚀 Railway environment detected - finding database path...")
        
        # Check if RAILWAY_VOLUME_MOUNT_PATH is set
        volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if volume_mount_path:
            print(f"📌 RAILWAY_VOLUME_MOUNT_PATH is set to: {volume_mount_path}")
            
            # Remove trailing slash if present
            volume_mount_path = volume_mount_path.rstrip('/')
            
            # First, try the RAILWAY_VOLUME_MOUNT_PATH directly
            if os.path.exists(volume_mount_path):
                print(f"✅ Volume directory exists at: {volume_mount_path}")
                
                # Check permissions
                import stat
                try:
                    st = os.stat(volume_mount_path)
                    print(f"📊 Volume permissions: {oct(st.st_mode)}, Owner UID: {st.st_uid}, Group GID: {st.st_gid}")
                    print(f"📊 Current process UID: {os.getuid()}, GID: {os.getgid()}")
                except Exception as perm_error:
                    print(f"⚠️ Could not check permissions: {perm_error}")
                
                # Try to fix permissions if needed
                try:
                    # Create a subdirectory that we can control
                    app_data_dir = os.path.join(volume_mount_path, 'app_data')
                    os.makedirs(app_data_dir, exist_ok=True)
                    
                    # Test if subdirectory is writable
                    test_file = os.path.join(app_data_dir, '.write_test')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    
                    db_path = os.path.join(app_data_dir, 'registration_submissions.db')
                    print(f"✅ Created writable subdirectory: {app_data_dir}")
                    print(f"✅ Using persistent database: {db_path}")
                    return db_path
                    
                except Exception as subdir_error:
                    print(f"⚠️ Could not create subdirectory: {subdir_error}")
                    
                    # Last resort: try to write directly to /data
                    try:
                        test_file = os.path.join(volume_mount_path, '.write_test')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        db_path = os.path.join(volume_mount_path, 'registration_submissions.db')
                        print(f"✅ Volume is writable - using persistent database: {db_path}")
                        return db_path
                    except Exception as write_error:
                        print(f"❌ Volume not writable: {write_error}")
                        print("🔧 This is a permissions issue - the volume exists but your app can't write to it")
            else:
                print(f"⚠️ RAILWAY_VOLUME_MOUNT_PATH set but directory doesn't exist: {volume_mount_path}")
        else:
            print("⚠️ RAILWAY_VOLUME_MOUNT_PATH environment variable is NOT set")
        
        # Try common volume locations
        print("🔍 Checking common Railway volume locations...")
        common_paths = ['/data', '/mnt/data', '/volume', '/mnt/volume']
        for path in common_paths:
            if os.path.exists(path):
                try:
                    test_file = os.path.join(path, '.write_test')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    db_path = os.path.join(path, 'registration_submissions.db')
                    print(f"✅ Found writable volume at {path}")
                    print(f"✅ Using persistent database: {db_path}")
                    return db_path
                except Exception as e:
                    print(f"⚠️ Path {path} exists but not writable: {e}")
        
        # Check for Railway bind mounts (legacy/advanced detection)
        bind_mount_base = '/var/lib/containers/railwayapp/bind-mounts'
        if os.path.exists(bind_mount_base):
            try:
                print(f"🔍 Checking Railway bind mounts at {bind_mount_base}")
                for project_dir in os.listdir(bind_mount_base):
                    project_path = os.path.join(bind_mount_base, project_dir)
                    print(f"📁 Found project directory: {project_path}")
                    if os.path.isdir(project_path):
                        for vol_dir in os.listdir(project_path):
                            if vol_dir.startswith('vol_'):
                                volume_path = os.path.join(project_path, vol_dir)
                                try:
                                    test_file = os.path.join(volume_path, '.write_test')
                                    with open(test_file, 'w') as f:
                                        f.write('test')
                                    os.remove(test_file)
                                    db_path = os.path.join(volume_path, 'registration_submissions.db')
                                    print(f"✅ Found Railway bind mount at {volume_path}")
                                    print(f"✅ Volume is writable - using persistent database: {db_path}")
                                    return db_path
                                except Exception as write_error:
                                    print(f"⚠️ Volume at {volume_path} not writable: {write_error}")
            except Exception as e:
                print(f"Volume discovery error: {e}")
        
        # Fallback to Railway app directory (ephemeral but functional)
        app_path = '/app/registration_submissions.db'
        print("⚠️ WARNING: No persistent volume found - using ephemeral storage")
        print("Database will reset on each deployment until persistent volume is configured")
        print(f"Using ephemeral database: {app_path}")
        
        # Ensure the /app directory is writable
        try:
            os.makedirs('/app', exist_ok=True)
            print("📁 Ensured /app directory exists")
        except Exception as e:
            print(f"⚠️ Could not create /app directory: {e}")
            
        return app_path
    else:
        # Local development - use relative path
        local_path = 'registration_submissions.db'
        print(f"💻 Local development - using: {local_path}")
        return local_path

# Get database path dynamically (not cached to ensure Railway detection works)
def get_db_file():
    """Get current database file path - called fresh each time."""
    return get_database_path()

# For backward compatibility, set initial value but allow dynamic updates
DB_FILE = get_database_path()

# Initialize database on startup
def init_db_with_logging():
    """Initialize database with logging for Railway debugging."""
    try:
        db_file = get_database_path()
        print(f"Initializing database at: {db_file}")
        print(f"Database file exists: {os.path.exists(db_file)}")
        
        conn = sqlite3.connect(db_file)
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
                additional_comments TEXT,
                payment_status TEXT DEFAULT 'pending'
            )
        """)
        
        # Migrate existing database to add payment_status column if it doesn't exist
        cursor.execute("PRAGMA table_info(registrations)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'payment_status' not in columns:
            print("🔧 Migrating database: Adding payment_status column...")
            cursor.execute("ALTER TABLE registrations ADD COLUMN payment_status TEXT DEFAULT 'pending'")
            print("✅ Migration complete: payment_status column added")
        
        # Add camp_session column for tracking which camp session each registration belongs to
        if 'camp_session' not in columns:
            print("🔧 Migrating database: Adding camp_session column...")
            cursor.execute("ALTER TABLE registrations ADD COLUMN camp_session TEXT")
            # Update existing records with a default session
            cursor.execute("UPDATE registrations SET camp_session = 'Camp Power-Up 2025 - November 24th-26th' WHERE camp_session IS NULL")
            print("✅ Migration complete: camp_session column added")
        
        conn.commit()
        
        # Check existing data
        cursor.execute("SELECT COUNT(*) FROM registrations")
        count = cursor.fetchone()[0]
        print(f"Database initialized with {count} existing registrations")
        
        # Auto-restore from backup if database is empty and backup exists
        if count == 0:
            backup_file = os.path.join(os.path.dirname(__file__), 'registrations_backup.json')
            if os.path.exists(backup_file):
                try:
                    print(f"📦 Found backup file, attempting auto-restore...")
                    import json
                    with open(backup_file, 'r') as f:
                        backup_data = json.load(f)
                    
                    if 'registrations' in backup_data:
                        registrations = backup_data['registrations']
                        restored_count = 0
                        
                        for reg in registrations:
                            try:
                                # Insert registration
                                cursor.execute("""
                                    INSERT OR IGNORE INTO registrations (
                                        submission_id, timestamp, child_first_name, child_last_name, 
                                        child_age, child_grade, parent_first_name, parent_last_name,
                                        parent_email, parent_phone, emergency_contact_name, 
                                        emergency_contact_phone, has_allergies, allergies_description,
                                        has_medical_conditions, medical_conditions_description,
                                        is_returning_camper, returning_years, bringing_own_switch,
                                        how_heard_about_camp, additional_comments
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
                                restored_count += 1
                            except Exception as restore_error:
                                print(f"⚠️ Could not restore registration {reg.get('submission_id')}: {restore_error}")
                        
                        conn.commit()
                        print(f"✅ Auto-restored {restored_count} registrations from backup")
                except Exception as backup_error:
                    print(f"⚠️ Auto-restore failed: {backup_error}")
        
        # Update global DB_FILE to current path
        global DB_FILE
        DB_FILE = db_file
        
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

# Email notification functions
def send_email_notification(to_email, subject, html_content, text_content=None):
    """Send email via SendGrid."""
    try:
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            print("⚠️ SENDGRID_API_KEY not set - email not sent")
            return False
        
        from_email = Email(
            os.environ.get('SENDGRID_FROM_EMAIL', 'camppowerup2025@gmail.com'),
            os.environ.get('SENDGRID_FROM_NAME', 'Camp Power-Up Registration')
        )
        to_email_obj = To(to_email)
        
        # Use HTML content as primary, fallback to text
        if text_content:
            content = Content("text/plain", text_content)
        else:
            content = Content("text/html", html_content)
        
        mail = Mail(from_email, to_email_obj, subject, content)
        
        # If HTML content provided, add it
        if html_content and text_content:
            mail.add_content(Content("text/html", html_content))
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(mail)
        
        print(f"✅ Email sent to {to_email}: {subject} (Status: {response.status_code})")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        return False

def send_parent_confirmation_email(registration_data):
    """Send confirmation email to parent/guardian."""
    try:
        parent_email = registration_data.get('parent_email')
        if not parent_email:
            print("⚠️ No parent email provided")
            return False
        
        child_name = f"{registration_data.get('child_first_name', '')} {registration_data.get('child_last_name', '')}"
        parent_name = f"{registration_data.get('parent_first_name', '')} {registration_data.get('parent_last_name', '')}"
        submission_id = registration_data.get('submission_id', 'N/A')
        
        # Determine pricing - Handle string "true"/"false" from old database records
        is_returning_raw = registration_data.get('is_returning_camper', False)
        
        # Convert string "true"/"false" or integer 1/0 to proper boolean
        if isinstance(is_returning_raw, str):
            is_returning = is_returning_raw.lower() in ['true', '1', 'yes']
        else:
            is_returning = bool(is_returning_raw)
        
        # Debug: Print the actual value
        print(f"💰 Email pricing debug - raw value: {is_returning_raw} (type: {type(is_returning_raw)})")
        print(f"💰 Email pricing debug - converted to: {is_returning} (type: {type(is_returning)})")
        
        deposit = "$50"
        final_payment = "$130" if is_returning else "$150"
        total = "$180" if is_returning else "$200"
        
        print(f"💰 Calculated prices - Deposit: {deposit}, Final: {final_payment}, Total: {total}")
        
        subject = f"✅ Camp Power-Up Registration Confirmed - {child_name}"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; }}
                .confirmation-box {{ background: white; border: 2px solid #28a745; border-radius: 10px; padding: 20px; margin: 20px 0; }}
                .payment-box {{ background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .important {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 0.9em; }}
                .button {{ display: inline-block; background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                h2 {{ color: #2c3e50; }}
                .success-icon {{ font-size: 3em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="success-icon">✅</div>
                    <h1>Registration Confirmed!</h1>
                    <p>Welcome to Camp Power-Up Summer 2026</p>
                </div>
                
                <div class="content">
                    <p>Dear {parent_name},</p>
                    
                    <p>Thank you for registering <strong>{child_name}</strong> for Camp Power-Up! We're excited to have them join us for an amazing Nintendo Switch gaming experience.</p>
                    
                    <div class="confirmation-box">
                        <h2>📋 Registration Details</h2>
                        <p><strong>Confirmation ID:</strong> <code>{submission_id}</code></p>
                        <p><strong>Camper:</strong> {child_name}</p>
                        <p><strong>Age:</strong> {registration_data.get('child_age', 'N/A')}</p>
                        <p><strong>Grade:</strong> {registration_data.get('child_grade', 'N/A')}</p>
                        <p><strong>Camp Dates:</strong> June 15-19, 2026</p>
                        <p><strong>Camp Times:</strong> 10:00 AM - 3:00 PM daily</p>
                    </div>
                    
                    <div class="payment-box">
                        <h2>💳 Payment Information</h2>
                        <p><strong>Total Fee:</strong> {total}</p>
                        <p><strong>Deposit Required Now:</strong> {deposit}</p>
                        <p><strong>Final Payment:</strong> {final_payment} (due before June 1st)</p>
                        
                        <p><strong>Payment Methods:</strong></p>
                        <ul>
                            <li><strong>CashApp:</strong> $TevinFowler</li>
                            <li><strong>Venmo:</strong> @Tevin-Fowler or @Brandon-Ballard</li>
                        </ul>
                        
                        <p>⚠️ <strong>Important:</strong> Include "{child_name}" or "{submission_id}" in the payment memo</p>
                    </div>
                    
                    <div class="important">
                        <h3>📝 Next Steps</h3>
                        <ol>
                            <li>Complete your {deposit} deposit payment via CashApp or Venmo</li>
                            <li>Save this confirmation email for your records</li>
                            <li>Mark your calendar: June 15-19, 2026</li>
                            <li>Pay final {final_payment} before June 1st</li>
                        </ol>
                    </div>
                    
                    <h3>❓ Questions or Need to Make Changes?</h3>
                    <p>Email us at: <a href="mailto:camppowerup2026@gmail.com">camppowerup2026@gmail.com</a></p>
                    <p>Include your confirmation ID: <code>{submission_id}</code></p>
                    
                    <p style="margin-top: 30px;">We can't wait to see {child_name.split()[0]} at camp!</p>
                    
                    <p><strong>The Camp Power-Up Team</strong><br>
                    Nintendo Switch Gaming Camp</p>
                </div>
                
                <div class="footer">
                    <p>Camp Power-Up Summer 2026 | June 15-19, 2026</p>
                    <p><a href="https://camppowerup-registration.up.railway.app/confirmation/{submission_id}">View Your Confirmation Online</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Camp Power-Up Summer 2026 - Registration Confirmed
        
        Dear {parent_name},
        
        Thank you for registering {child_name} for Camp Power-Up!
        
        REGISTRATION DETAILS:
        Confirmation ID: {submission_id}
        Camper: {child_name}
        Age: {registration_data.get('child_age', 'N/A')}
        Grade: {registration_data.get('child_grade', 'N/A')}
        Camp Dates: June 15-19, 2026
        Camp Times: 10:00 AM - 3:00 PM daily
        
        PAYMENT INFORMATION:
        Total Fee: {total}
        Deposit Required Now: {deposit}
        Final Payment: {final_payment} (due before June 1st)
        
        Payment Methods:
        - CashApp: $TevinFowler
        - Venmo: @Tevin-Fowler or @Brandon-Ballard
        
        IMPORTANT: Include "{child_name}" in the payment memo
        
        NEXT STEPS:
        1. Complete your {deposit} deposit payment
        2. Save this email for your records
        3. Mark your calendar: June 15-19, 2026
        4. Pay final {final_payment} before June 1st
        
        Questions? Email: camppowerup2026@gmail.com
        Include your confirmation ID: {submission_id}
        
        View online: https://camppowerup-registration.up.railway.app/confirmation/{submission_id}
        
        The Camp Power-Up Team
        """
        
        return send_email_notification(parent_email, subject, html_content, text_content)
        
    except Exception as e:
        print(f"❌ Parent email error: {str(e)}")
        return False

def send_admin_notification_email(registration_data):
    """Send notification email to admin about new registration."""
    try:
        admin_email = os.environ.get('CAMP_EMAIL', 'camppowerup2025@gmail.com')
        
        child_name = f"{registration_data.get('child_first_name', '')} {registration_data.get('child_last_name', '')}"
        parent_name = f"{registration_data.get('parent_first_name', '')} {registration_data.get('parent_last_name', '')}"
        submission_id = registration_data.get('submission_id', 'N/A')
        
        subject = f"🎮 New Registration: {child_name}"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 20px; }}
                .info-box {{ background: white; border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                td:first-child {{ font-weight: bold; width: 40%; }}
                .button {{ display: inline-block; background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎮 New Camp Registration</h1>
                    <p>{child_name}</p>
                </div>
                
                <div class="content">
                    <div class="info-box">
                        <p><strong>Confirmation ID:</strong> {submission_id}</p>
                        <p><strong>Registration Time:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                    
                    <h2>Camper Information</h2>
                    <table>
                        <tr><td>Name</td><td>{child_name}</td></tr>
                        <tr><td>Age</td><td>{registration_data.get('child_age', 'N/A')}</td></tr>
                        <tr><td>Grade</td><td>{registration_data.get('child_grade', 'N/A')}</td></tr>
                    </table>
                    
                    <h2>Parent/Guardian Information</h2>
                    <table>
                        <tr><td>Name</td><td>{parent_name}</td></tr>
                        <tr><td>Email</td><td>{registration_data.get('parent_email', 'N/A')}</td></tr>
                        <tr><td>Phone</td><td>{registration_data.get('parent_phone', 'N/A')}</td></tr>
                    </table>
                    
                    <h2>Emergency Contact</h2>
                    <table>
                        <tr><td>Name</td><td>{registration_data.get('emergency_contact_name', 'N/A')}</td></tr>
                        <tr><td>Phone</td><td>{registration_data.get('emergency_contact_phone', 'N/A')}</td></tr>
                    </table>
                    
                    <h2>Special Notes</h2>
                    <table>
                        <tr><td>Allergies</td><td>{"YES: " + registration_data.get('allergies_description', '') if registration_data.get('has_allergies') else "None reported"}</td></tr>
                        <tr><td>Medical Conditions</td><td>{"YES: " + registration_data.get('medical_conditions_description', '') if registration_data.get('has_medical_conditions') else "None reported"}</td></tr>
                        <tr><td>Returning Camper</td><td>{"Yes" if registration_data.get('is_returning_camper') else "No"}</td></tr>
                        <tr><td>Bringing Switch</td><td>{"Yes" if registration_data.get('bringing_own_switch') else "No"}</td></tr>
                    </table>
                    
                    {f'<h2>Additional Comments</h2><p>{registration_data.get("additional_comments", "")}</p>' if registration_data.get('additional_comments') else ''}
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="https://camppowerup-registration.up.railway.app/admin" class="button">View in Admin Dashboard</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        NEW CAMP REGISTRATION
        
        Confirmation ID: {submission_id}
        Time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
        
        CAMPER INFORMATION:
        Name: {child_name}
        Age: {registration_data.get('child_age', 'N/A')}
        Grade: {registration_data.get('child_grade', 'N/A')}
        
        PARENT/GUARDIAN:
        Name: {parent_name}
        Email: {registration_data.get('parent_email', 'N/A')}
        Phone: {registration_data.get('parent_phone', 'N/A')}
        
        EMERGENCY CONTACT:
        Name: {registration_data.get('emergency_contact_name', 'N/A')}
        Phone: {registration_data.get('emergency_contact_phone', 'N/A')}
        
        SPECIAL NOTES:
        Allergies: {"YES: " + registration_data.get('allergies_description', '') if registration_data.get('has_allergies') else "None"}
        Medical: {"YES: " + registration_data.get('medical_conditions_description', '') if registration_data.get('has_medical_conditions') else "None"}
        Returning Camper: {"Yes" if registration_data.get('is_returning_camper') else "No"}
        Bringing Switch: {"Yes" if registration_data.get('bringing_own_switch') else "No"}
        
        View full details: https://camppowerup-registration.up.railway.app/admin
        """
        
        return send_email_notification(admin_email, subject, html_content, text_content)
        
    except Exception as e:
        print(f"❌ Admin email error: {str(e)}")
        return False

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'campadmin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'PowerUp2026!')

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

@app.route('/debug-all-registrations')
def debug_all_registrations():
    """Show all registrations with full details for debugging."""
    try:
        db_file = get_database_path()
        print(f"🔍 Debug all registrations using database: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC LIMIT 10")
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            "database_file": db_file,
            "total_count": len(registrations),
            "registrations": registrations
        })
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/')
def home():
    """Main registration form."""
    try:
        # Use dynamic pricing from camp_config
        pricing = get_pricing_text()
        
        # Use dynamic camp config
        camp_config = {
            'camp_name': get_camp_title(),
            'camp_dates': CAMP_CONFIG.get('camp_dates', 'March 26th-27th'),
            'camp_times': CAMP_CONFIG.get('daily_hours', '10:00am-3:00pm'),
            'pricing': CAMP_CONFIG.get('pricing', {})
        }
        
        return render_template('registration_form.html', 
                             camp_config=camp_config,
                             config=CAMP_CONFIG,
                             camp_title=get_camp_title() + ' Registration',
                             camp_subtitle=f"Nintendo Switch Gaming Camp - {CAMP_CONFIG.get('camp_dates', 'March 26th-27th')}",
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

@app.route('/faq')
def faq():
    """Display the FAQ page."""
    return render_template('faq.html', config=CAMP_CONFIG)

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
        db_file = get_database_path()
        print(f"🧪 Test-db using database: {db_file}")
        conn = sqlite3.connect(db_file)
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
            "database_file": db_file,
            "cached_db_file": DB_FILE,
            "database_exists": os.path.exists(db_file),
            "table_exists": table_exists,
            "table_schema": table_schema,
            "total_registrations": count,
            "recent_registrations": recent_registrations,
            "environment": "Railway" if os.environ.get('RAILWAY_ENVIRONMENT') else "Local",
            "status": "✅ Working" if table_exists else "⚠️ No Table",
            "message": f"Database {'working' if table_exists else 'table missing'} - {count} registrations found"
        })
    except Exception as e:
        db_file = get_database_path()
        return jsonify({
            "error": str(e), 
            "status": "❌ Error",
            "database_file": db_file,
            "database_exists": os.path.exists(DB_FILE) if 'DB_FILE' in locals() else False
        }), 500

@app.route('/debug-registration/<submission_id>')
def debug_registration(submission_id):
    """Debug specific registration by ID."""
    try:
        db_file = get_database_path()
        print(f"🔍 Debug-registration using database: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the specific registration
        cursor.execute("SELECT * FROM registrations WHERE submission_id = ?", (submission_id,))
        registration = cursor.fetchone()
        
        result = {
            "submission_id": submission_id,
            "database_file": db_file,
            "cached_db_file": DB_FILE,
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

@app.route('/test-submit')
def test_submit():
    """Test submission endpoint with sample data."""
    try:
        # Sample registration data for testing
        test_data = {
            "childFirstName": "Test",
            "childLastName": "Camper", 
            "childAge": "8",
            "childGrade": "3rd",
            "parentFirstName": "Test",
            "parentLastName": "Parent",
            "parentEmail": "test@example.com",
            "parentPhone": "555-1234",
            "emergencyContactName": "Emergency Contact",
            "emergencyContactPhone": "555-5678",
            "hasAllergies": False,
            "allergiesDescription": "",
            "hasMedicalConditions": False,
            "medicalConditionsDescription": "",
            "isReturningCamper": False,
            "returningYears": "",
            "bringingOwnSwitch": False,
            "howHeardAboutCamp": "Testing",
            "additionalComments": "Test submission"
        }
        
        # Test database connection and table structure
        db_file = get_database_path()
        print(f"🧪 Test-submit using database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(registrations)")
        schema = cursor.fetchall()
        
        # Test if we can insert
        submission_id = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
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
            submission_id, test_data['childFirstName'], test_data['childLastName'],
            test_data['childAge'], test_data['childGrade'],
            test_data['parentFirstName'], test_data['parentLastName'],
            test_data['parentEmail'], test_data['parentPhone'],
            test_data['emergencyContactName'], test_data['emergencyContactPhone'],
            test_data['hasAllergies'], test_data['allergiesDescription'],
            test_data['hasMedicalConditions'], test_data['medicalConditionsDescription'],
            test_data['isReturningCamper'], test_data['returningYears'],
            test_data['bringingOwnSwitch'], test_data['howHeardAboutCamp'],
            test_data['additionalComments']
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Test submission successful",
            "test_submission_id": submission_id,
            "database_file": DB_FILE,
            "table_schema": schema,
            "database_exists": os.path.exists(DB_FILE)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "database_file": DB_FILE
        }), 500

@app.route('/railway-status')
def railway_status():
    """Check Railway configuration and provide setup instructions."""
    try:
        # Get fresh database path
        current_db_path = get_database_path()
        
        # Check all possible volume locations with write test
        volume_checks = {}
        test_paths = ['/data', '/mnt/data', '/volume', '/mnt/volume', '/app', 
                     '/var/lib/containers/railwayapp/bind-mounts']
        
        for path in test_paths:
            exists = os.path.exists(path)
            writable = False
            is_symlink = False
            real_path = None
            if exists:
                is_symlink = os.path.islink(path)
                if is_symlink:
                    try:
                        real_path = os.path.realpath(path)
                    except:
                        real_path = "Unable to resolve"
                try:
                    test_file = os.path.join(path, '.status_write_test')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    writable = True
                except Exception as e:
                    pass
            volume_checks[path] = {
                "exists": exists,
                "writable": writable,
                "is_symlink": is_symlink,
                "real_path": real_path
            }
        
        # Deep filesystem exploration - find ALL writable directories
        writable_dirs = []
        search_paths = ['/', '/mnt', '/var', '/opt', '/usr/local']
        for base in search_paths:
            if os.path.exists(base):
                try:
                    for item in os.listdir(base):
                        item_path = os.path.join(base, item)
                        if os.path.isdir(item_path):
                            try:
                                test_file = os.path.join(item_path, '.explore_write_test')
                                with open(test_file, 'w') as f:
                                    f.write('test')
                                os.remove(test_file)
                                writable_dirs.append(item_path)
                            except:
                                pass
                except:
                    pass
        
        # List bind mount contents if they exist
        bind_mount_contents = []
        bind_mount_base = '/var/lib/containers/railwayapp/bind-mounts'
        if os.path.exists(bind_mount_base):
            try:
                for project_dir in os.listdir(bind_mount_base):
                    project_path = os.path.join(bind_mount_base, project_dir)
                    if os.path.isdir(project_path):
                        volumes = [vol for vol in os.listdir(project_path) if vol.startswith('vol_')]
                        bind_mount_contents.append({
                            "project": project_dir,
                            "volumes": volumes,
                            "full_paths": [os.path.join(project_path, vol) for vol in volumes]
                        })
            except Exception as e:
                bind_mount_contents.append({"error": str(e)})
        
        # Get all environment variables related to volumes
        volume_env_vars = {k: v for k, v in os.environ.items() 
                          if any(word in k.lower() for word in ['volume', 'mount', 'data', 'persist'])}
        
        # Determine if using persistent storage
        is_persistent = '/app' not in current_db_path
        
        status = {
            "environment": "Railway" if os.environ.get('RAILWAY_ENVIRONMENT') else "Local",
            "railway_volume_mount_path_env": os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', 'NOT SET'),
            "database_file_cached": DB_FILE,
            "database_file_current": current_db_path,
            "database_exists": os.path.exists(current_db_path),
            "using_persistent_storage": is_persistent,
            "volume_checks": volume_checks,
            "writable_directories_found": writable_dirs,
            "bind_mount_contents": bind_mount_contents,
            "volume_related_env_vars": volume_env_vars,
            "current_storage_type": "persistent" if is_persistent else "ephemeral",
            "data_persistence": "✅ Data survives deployments" if is_persistent else "❌ Data lost on each deployment"
        }
        
        if os.environ.get('RAILWAY_ENVIRONMENT') and not os.path.exists('/data'):
            status["urgent_action_required"] = True
            status["problem"] = "Railway RAILWAY_VOLUME_MOUNT_PATH is set, but /data directory does NOT exist"
            status["impact"] = "Environment variable exists but actual volume is not mounted"
            status["diagnosis"] = {
                "env_var_set": os.environ.get('RAILWAY_VOLUME_MOUNT_PATH') is not None,
                "env_var_value": os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', 'NOT SET'),
                "directory_exists": os.path.exists('/data'),
                "issue": "You need to create an ACTUAL volume in Railway dashboard, not just the environment variable"
            }
            status["solution"] = {
                "step1": "Go to Railway Dashboard -> Your project -> Click on your service",
                "step2": "Go to Settings tab (not Variables)",
                "step3": "Scroll down to 'Volumes' section",
                "step4": "Click '+ New Volume'",
                "step5": "Mount Path: /data (must match RAILWAY_VOLUME_MOUNT_PATH)",
                "step6": "Size: 1 GB",
                "step7": "Click 'Add' - Railway will auto-redeploy and mount the volume"
            }
        else:
            status["urgent_action_required"] = False
            
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/find-volumes')
def find_volumes():
    """Aggressively search the entire filesystem for Railway volumes."""
    try:
        import subprocess
        
        results = {
            "search_method": "comprehensive filesystem scan",
            "timestamp": datetime.now().isoformat()
        }
        
        # Method 1: Check mount points
        try:
            mount_output = subprocess.check_output(['mount'], text=True)
            results["mount_points"] = mount_output.split('\n')
        except:
            results["mount_points"] = "Unable to execute mount command"
        
        # Method 2: Check df for filesystem usage
        try:
            df_output = subprocess.check_output(['df', '-h'], text=True)
            results["disk_usage"] = df_output.split('\n')
        except:
            results["disk_usage"] = "Unable to execute df command"
        
        # Method 3: Find all directories containing 'vol_' or 'railway'
        suspicious_dirs = []
        search_bases = ['/', '/mnt', '/var', '/opt', '/usr', '/home']
        for base in search_bases:
            if os.path.exists(base):
                try:
                    # Use find command for faster search
                    find_cmd = f"find {base} -maxdepth 3 -type d \\( -name '*vol_*' -o -name '*railway*' -o -name '*volume*' \\) 2>/dev/null"
                    find_output = subprocess.check_output(find_cmd, shell=True, text=True, timeout=5)
                    if find_output.strip():
                        suspicious_dirs.extend(find_output.strip().split('\n'))
                except:
                    pass
        
        results["suspicious_directories"] = suspicious_dirs
        
        # Method 4: Check what's in root directory
        try:
            root_contents = os.listdir('/')
            root_dirs = [item for item in root_contents if os.path.isdir(f'/{item}')]
            results["root_directories"] = root_dirs
        except Exception as e:
            results["root_directories"] = f"Error: {str(e)}"
        
        # Method 5: Test write to common volume locations
        test_locations = {}
        for path in ['/data', '/mnt/data', '/volume', '/mnt/volume', '/var/data', '/opt/data']:
            if os.path.exists(path):
                try:
                    test_file = os.path.join(path, '.volume_test')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    test_locations[path] = "✅ WRITABLE"
                except Exception as e:
                    test_locations[path] = f"❌ Not writable: {str(e)}"
            else:
                test_locations[path] = "Does not exist"
        
        results["volume_write_tests"] = test_locations
        
        # Method 6: All environment variables
        results["all_env_vars"] = dict(os.environ)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e), "traceback": str(e.__traceback__)}), 500

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
        
        # Get form data from JSON - accept both camelCase AND snake_case for compatibility
        data = {
            'child_first_name': json_data.get('child_first_name') or json_data.get('childFirstName', ''),
            'child_last_name': json_data.get('child_last_name') or json_data.get('childLastName', ''),
            'child_age': json_data.get('child_age') or json_data.get('childAge', ''),
            'child_grade': json_data.get('child_grade') or json_data.get('childGrade', ''),
            'parent_first_name': json_data.get('parent_first_name') or json_data.get('parentFirstName', ''),
            'parent_last_name': json_data.get('parent_last_name') or json_data.get('parentLastName', ''),
            'parent_email': json_data.get('parent_email') or json_data.get('parentEmail', ''),
            'parent_phone': json_data.get('parent_phone') or json_data.get('parentPhone', ''),
            'emergency_contact_name': json_data.get('emergency_contact_name') or json_data.get('emergencyContactName', ''),
            'emergency_contact_phone': json_data.get('emergency_contact_phone') or json_data.get('emergencyContactPhone', ''),
            'has_allergies': json_data.get('has_allergies', json_data.get('hasAllergies', False)),
            'allergies_description': json_data.get('allergies_description') or json_data.get('allergiesDescription', ''),
            'has_medical_conditions': json_data.get('has_medical_conditions', json_data.get('hasMedicalConditions', False)),
            'medical_conditions_description': json_data.get('medical_conditions_description') or json_data.get('medicalConditionsDescription', ''),
            'is_returning_camper': json_data.get('is_returning_camper', json_data.get('isReturningCamper', False)),
            'returning_years': json_data.get('returning_years') or json_data.get('returningYears', ''),
            'bringing_own_switch': json_data.get('bringing_own_switch', json_data.get('bringingOwnSwitch', False)),
            'how_heard_about_camp': json_data.get('how_heard_about_camp') or json_data.get('howHeardAboutCamp', ''),
            'additional_comments': json_data.get('additional_comments') or json_data.get('additionalComments', '')
        }
        
        # Convert string "true"/"false" to boolean for is_returning_camper
        if isinstance(data['is_returning_camper'], str):
            data['is_returning_camper'] = data['is_returning_camper'].lower() in ['true', '1', 'yes']
        
        # Convert to integer for database (SQLite uses 0/1 for boolean)
        data['is_returning_camper'] = 1 if data['is_returning_camper'] else 0
        
        # Debug logging
        print(f"📝 Form data received:")
        print(f"   child_first_name: '{data['child_first_name']}'")
        print(f"   child_last_name: '{data['child_last_name']}'")
        print(f"   parent_email: '{data['parent_email']}'")
        print(f"   is_returning_camper: {data['is_returning_camper']}")
        
        # Save to database - get fresh path for Railway compatibility
        db_file = get_database_path()
        print(f"🔄 Using database path: {db_file}")
        
        # Ensure database directory exists and is writable
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                print(f"📁 Created database directory: {db_dir}")
            except Exception as e:
                print(f"⚠️ Could not create database directory: {e}")
        
        # Initialize database if it doesn't exist
        if not os.path.exists(db_file):
            print(f"🆕 Database doesn't exist, initializing: {db_file}")
            try:
                # Create and initialize the database
                conn = sqlite3.connect(db_file)
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
                        additional_comments TEXT,
                        payment_status TEXT DEFAULT 'pending'
                    )
                """)
                conn.commit()
                conn.close()
                print(f"✅ Database initialized successfully: {db_file}")
            except Exception as init_error:
                print(f"❌ Database initialization failed: {init_error}")
                raise init_error
        
        # Connect to database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get current camp session
        current_session = f"{CAMP_CONFIG.get('camp_name', 'Camp Power-Up')} - {CAMP_CONFIG.get('camp_dates', 'Unknown')}"
        
        cursor.execute("""
            INSERT INTO registrations (
                submission_id, child_first_name, child_last_name, child_age, child_grade,
                parent_first_name, parent_last_name, parent_email, parent_phone,
                emergency_contact_name, emergency_contact_phone,
                has_allergies, allergies_description, has_medical_conditions, 
                medical_conditions_description, is_returning_camper, returning_years,
                bringing_own_switch, how_heard_about_camp, additional_comments, camp_session
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id, data['child_first_name'], data['child_last_name'], 
            data['child_age'], data['child_grade'], data['parent_first_name'], data['parent_last_name'],
            data['parent_email'], data['parent_phone'], 
            data['emergency_contact_name'], data['emergency_contact_phone'],
            data['has_allergies'], data['allergies_description'],
            data['has_medical_conditions'], data['medical_conditions_description'],
            data['is_returning_camper'], data['returning_years'], data['bringing_own_switch'],
            data['how_heard_about_camp'], data['additional_comments'], current_session
        ))
        conn.commit()
        conn.close()
        
        # Auto-backup to JSON file after each registration (for ephemeral storage protection)
        try:
            backup_file = os.path.join(os.path.dirname(__file__), 'registrations_backup.json')
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM registrations ORDER BY timestamp ASC")
            all_registrations = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            import json
            with open(backup_file, 'w') as f:
                json.dump({
                    "success": True,
                    "count": len(all_registrations),
                    "last_backup": datetime.now().isoformat(),
                    "source_database": db_file,
                    "registrations": all_registrations
                }, f, indent=2, default=str)
            
            print(f"💾 Auto-backup created: {len(all_registrations)} registrations saved to {backup_file}")
        except Exception as backup_error:
            print(f"⚠️ Auto-backup failed (non-critical): {backup_error}")
        
        # Send email notifications
        email_status = {
            "parent_email_sent": False,
            "admin_email_sent": False
        }
        
        # Prepare registration data for emails
        email_data = {
            'submission_id': submission_id,
            'child_first_name': data['child_first_name'],
            'child_last_name': data['child_last_name'],
            'child_age': data['child_age'],
            'child_grade': data['child_grade'],
            'parent_first_name': data['parent_first_name'],
            'parent_last_name': data['parent_last_name'],
            'parent_email': data['parent_email'],
            'parent_phone': data['parent_phone'],
            'emergency_contact_name': data['emergency_contact_name'],
            'emergency_contact_phone': data['emergency_contact_phone'],
            'has_allergies': data['has_allergies'],
            'allergies_description': data['allergies_description'],
            'has_medical_conditions': data['has_medical_conditions'],
            'medical_conditions_description': data['medical_conditions_description'],
            'is_returning_camper': data['is_returning_camper'],
            'returning_years': data['returning_years'],
            'bringing_own_switch': data['bringing_own_switch'],
            'how_heard_about_camp': data['how_heard_about_camp'],
            'additional_comments': data['additional_comments']
        }
        
        # Send parent confirmation email
        try:
            parent_email_sent = send_parent_confirmation_email(email_data)
            email_status["parent_email_sent"] = parent_email_sent
            if parent_email_sent:
                print(f"✅ Parent confirmation email sent to {data['parent_email']}")
            else:
                print(f"⚠️ Parent confirmation email failed for {data['parent_email']}")
        except Exception as email_error:
            print(f"❌ Parent email exception: {str(email_error)}")
        
        # Send admin notification email
        try:
            admin_email_sent = send_admin_notification_email(email_data)
            email_status["admin_email_sent"] = admin_email_sent
            if admin_email_sent:
                print(f"✅ Admin notification email sent")
            else:
                print(f"⚠️ Admin notification email failed")
        except Exception as email_error:
            print(f"❌ Admin email exception: {str(email_error)}")
        
        # Return JSON success response
        return jsonify({
            "success": True,
            "submission_id": submission_id,
            "message": f"Registration successful for {data['child_first_name']} {data['child_last_name']}",
            "email_notifications": email_status
        })
        
    except Exception as e:
        # Enhanced error logging for debugging submission failures
        import traceback
        # Get fresh database path for error reporting
        current_db_file = get_database_path()
        error_details = {
            "success": False, 
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "database_file": current_db_file,
            "cached_db_file": DB_FILE,
            "submission_id": submission_id if 'submission_id' in locals() else 'not_generated',
            "database_exists": os.path.exists(current_db_file),
            "railway_env": os.environ.get('RAILWAY_ENVIRONMENT', 'Not set'),
            "working_directory": os.getcwd()
        }
        print(f"❌ Registration submission error: {error_details}")
        return jsonify(error_details), 500

@app.route('/confirmation/<submission_id>')
def confirmation(submission_id):
    """Show professional confirmation page with registration details."""
    try:
        # Fetch registration details from database - use fresh path for Railway compatibility
        db_file = get_database_path()
        print(f"🔍 Confirmation page using database: {db_file}")
        print(f"🔍 Looking for submission_id: {submission_id}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First check if the registration exists
        cursor.execute("SELECT COUNT(*) FROM registrations WHERE submission_id = ?", (submission_id,))
        count = cursor.fetchone()[0]
        print(f"🔍 Found {count} matching registrations")
        
        cursor.execute("SELECT * FROM registrations WHERE submission_id = ?", (submission_id,))
        registration = cursor.fetchone()
        
        if registration:
            print(f"✅ Registration found!")
            print(f"   child_first_name: '{registration['child_first_name']}'")
            print(f"   child_last_name: '{registration['child_last_name']}'")
            print(f"   child_age: '{registration['child_age']}'")
            print(f"   parent_email: '{registration['parent_email']}'")
        else:
            print(f"❌ No registration found for {submission_id}")
        
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
                            <p><strong>Camp Dates:</strong> November 24-25, 2025</p>
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
    """Professional admin dashboard with statistics and session filtering."""
    try:
        # Check for Railway storage issue
        is_railway_without_volume = os.environ.get('RAILWAY_ENVIRONMENT') and not os.path.exists('/data')
        if is_railway_without_volume:
            flash('⚠️ STORAGE WARNING: Railway production has no persistent volume configured. Registration data will be lost on deployment. Configure persistent volume at /data to fix this issue.', 'warning')
        
        # Get session filter from query string
        session_filter = request.args.get('session', 'all')
        
        # Use fresh database path for Railway compatibility
        db_file = get_database_path()
        print(f"📊 Admin dashboard using database: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get list of all unique sessions for the filter dropdown
        cursor.execute('''
            SELECT DISTINCT camp_session FROM registrations 
            WHERE camp_session IS NOT NULL AND camp_session != '' AND submission_id NOT LIKE 'HIST_%'
            ORDER BY camp_session DESC
        ''')
        available_sessions = [row['camp_session'] for row in cursor.fetchall()]
        
        # Current session from config
        current_session = f"{CAMP_CONFIG.get('camp_name', 'Camp Power-Up')} - {CAMP_CONFIG.get('camp_dates', 'Unknown')}"
        
        # Add current session if not in list
        if current_session not in available_sessions:
            available_sessions.insert(0, current_session)
        
        # Filter registrations by session if specified (exclude HIST_ historical records)
        if session_filter and session_filter != 'all':
            cursor.execute('''
                SELECT * FROM registrations 
                WHERE camp_session = ? AND submission_id NOT LIKE 'HIST_%'
                ORDER BY timestamp DESC
            ''', (session_filter,))
        else:
            cursor.execute("SELECT * FROM registrations WHERE submission_id NOT LIKE 'HIST_%' ORDER BY timestamp DESC")
        
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
        
        # Mock camp config for template - use dynamic config
        camp_config = {
            'camp_name': get_camp_title(),
            'camp_dates': CAMP_CONFIG.get('camp_dates', 'March 26th-27th'),
            'camp_times': CAMP_CONFIG.get('daily_hours', '10:00am-3:00pm')
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
                             camp_config=camp_config,
                             config=CAMP_CONFIG,
                             available_sessions=available_sessions,
                             current_session=current_session,
                             selected_session=session_filter)
                             
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/historical')
@require_admin_auth
def admin_historical():
    """View historical camper registrations (imported from CSV)."""
    try:
        db_file = get_database_path()
        print(f"📚 Historical data using database: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Debug: Check total records
        cursor.execute("SELECT COUNT(*) FROM registrations")
        total_all = cursor.fetchone()[0]
        print(f"🔍 Total records in database: {total_all}")
        
        # Debug: Check HIST_ records
        cursor.execute("SELECT COUNT(*) FROM registrations WHERE submission_id LIKE 'HIST_%'")
        total_hist = cursor.fetchone()[0]
        print(f"🔍 Records with HIST_ prefix: {total_hist}")
        
        # Debug: Check submission_id patterns
        cursor.execute("SELECT submission_id, child_first_name, child_last_name FROM registrations LIMIT 10")
        sample = cursor.fetchall()
        print(f"🔍 Sample records:")
        for s in sample:
            print(f"   - {s[0]}: {s[1]} {s[2]}")
        
        # Get only historical records (those with HIST_ prefix)
        cursor.execute("""
            SELECT * FROM registrations 
            WHERE submission_id LIKE 'HIST_%'
            ORDER BY timestamp DESC
        """)
        historical_registrations = [dict(row) for row in cursor.fetchall()]
        
        # Get statistics
        total_historical = len(historical_registrations)
        returning_from_history = len([r for r in historical_registrations if r.get('is_returning_camper')])
        
        conn.close()
        
        stats = {
            'total_historical': total_historical,
            'returning_from_history': returning_from_history,
            'new_from_history': total_historical - returning_from_history
        }
        
        # Map database field names to template field names
        historical_data = []
        for reg in historical_registrations:
            historical_data.append({
                'first_name': reg.get('child_first_name'),
                'last_name': reg.get('child_last_name'),
                'age': reg.get('child_age'),
                'grade': reg.get('child_grade'),
                'email': reg.get('parent_email'),
                'is_returning': 'Yes' if reg.get('is_returning_camper') else 'No',
                'favorite_games': reg.get('additional_comments', ''),
                'has_allergies': 'Yes' if reg.get('has_allergies') else 'No',
                'bringing_switch': 'Yes' if reg.get('bringing_own_switch') else 'No'
            })
        
        return render_template('admin_historical.html', 
                             historical_data=historical_data,
                             registrations=historical_registrations,
                             stats=stats)
                             
    except Exception as e:
        flash(f'Error loading historical data: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/metrics')
@require_admin_auth
def admin_metrics():
    """View metrics dashboard with session comparisons."""
    import csv
    import json
    from collections import Counter
    
    try:
        sessions = []
        all_ages = []
        all_grades = []
        total_new = 0
        total_returning = 0
        
        # --- Load 2025 Historical Data from CSV ---
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Camp_Power_Up_past_forms - Sheet1.csv')
        historical_2025 = []
        
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    historical_2025.append(row)
            
            # Parse 2025 data
            ages_2025 = []
            grades_2025 = []
            returning_2025 = 0
            new_2025 = 0
            
            for row in historical_2025:
                # Get age
                age_str = row.get('Age?', '').strip()
                if age_str and age_str.isdigit():
                    ages_2025.append(int(age_str))
                    all_ages.append(int(age_str))
                
                # Get grade
                grade = row.get('Grade?', '').strip()
                if grade:
                    grades_2025.append(grade)
                    all_grades.append(grade)
                
                # Check returning status
                is_returning = row.get('Has your Child attended Camp Power-Up before?', '').lower() == 'yes'
                if is_returning:
                    returning_2025 += 1
                    total_returning += 1
                else:
                    new_2025 += 1
                    total_new += 1
            
            # Calculate revenue for 2025 (old pricing: $80 returning, $100 new)
            revenue_2025 = (returning_2025 * 80) + (new_2025 * 100)
            
            sessions.append({
                'name': '2025 Sessions (Historical)',
                'total': len(historical_2025),
                'new_campers': new_2025,
                'returning_campers': returning_2025,
                'avg_age': round(sum(ages_2025) / len(ages_2025), 1) if ages_2025 else 0,
                'revenue': revenue_2025
            })
        
        # --- Load 2026 Data from Database ---
        db_file = get_database_path()
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all 2026 registrations (non-historical)
        cursor.execute("""
            SELECT * FROM registrations 
            WHERE submission_id NOT LIKE 'HIST_%'
            ORDER BY timestamp DESC
        """)
        registrations_2026 = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse 2026 data
        ages_2026 = []
        grades_2026 = []
        returning_2026 = 0
        new_2026 = 0
        
        for reg in registrations_2026:
            # Get age
            age = reg.get('child_age')
            if age:
                ages_2026.append(int(age))
                all_ages.append(int(age))
            
            # Get grade
            grade = reg.get('child_grade', '')
            if grade:
                grades_2026.append(grade)
                all_grades.append(grade)
            
            # Check returning status
            is_returning = reg.get('is_returning_camper')
            if isinstance(is_returning, str):
                is_returning = is_returning.lower() in ['true', '1', 'yes']
            else:
                is_returning = bool(is_returning)
            
            if is_returning:
                returning_2026 += 1
                total_returning += 1
            else:
                new_2026 += 1
                total_new += 1
        
        # Calculate revenue for 2026 ($180 returning, $200 new)
        revenue_2026 = (returning_2026 * 180) + (new_2026 * 200)
        
        sessions.append({
            'name': 'Summer 2026',
            'total': len(registrations_2026),
            'new_campers': new_2026,
            'returning_campers': returning_2026,
            'avg_age': round(sum(ages_2026) / len(ages_2026), 1) if ages_2026 else 0,
            'revenue': revenue_2026
        })
        
        # --- Calculate Aggregated Stats ---
        total_campers = len(historical_2025) + len(registrations_2026)
        total_revenue = sum(s['revenue'] for s in sessions)
        returning_rate = round((total_returning / total_campers * 100), 1) if total_campers > 0 else 0
        
        # Age distribution
        age_counter = Counter(all_ages)
        age_groups = {
            '5-7 years': sum(age_counter.get(a, 0) for a in range(5, 8)),
            '8-10 years': sum(age_counter.get(a, 0) for a in range(8, 11)),
            '11-13 years': sum(age_counter.get(a, 0) for a in range(11, 14)),
            '14+ years': sum(age_counter.get(a, 0) for a in range(14, 20))
        }
        age_labels = list(age_groups.keys())
        age_counts = list(age_groups.values())
        
        # Grade distribution
        grade_counter = Counter(all_grades)
        # Normalize grades
        normalized_grades = Counter()
        for grade, count in grade_counter.items():
            grade_lower = grade.lower().strip()
            if 'k' in grade_lower or 'kindergarten' in grade_lower:
                normalized_grades['Kindergarten'] += count
            elif '1' in grade_lower and 'rising' not in grade_lower:
                normalized_grades['1st Grade'] += count
            elif '2' in grade_lower:
                normalized_grades['2nd Grade'] += count
            elif '3' in grade_lower:
                normalized_grades['3rd Grade'] += count
            elif '4' in grade_lower:
                normalized_grades['4th Grade'] += count
            elif '5' in grade_lower:
                normalized_grades['5th Grade'] += count
            elif '6' in grade_lower:
                normalized_grades['6th Grade'] += count
            elif '7' in grade_lower:
                normalized_grades['7th Grade'] += count
            elif '8' in grade_lower:
                normalized_grades['8th Grade'] += count
            else:
                normalized_grades['Other'] += count
        
        # Sort grades
        grade_order = ['Kindergarten', '1st Grade', '2nd Grade', '3rd Grade', '4th Grade', 
                      '5th Grade', '6th Grade', '7th Grade', '8th Grade', 'Other']
        grade_labels = [g for g in grade_order if normalized_grades.get(g, 0) > 0]
        grade_counts = [normalized_grades.get(g, 0) for g in grade_labels]
        
        # Session labels and counts for chart
        session_labels = [s['name'] for s in sessions]
        session_counts = [s['total'] for s in sessions]
        
        return render_template('metrics_dashboard.html',
            total_campers=total_campers,
            returning_rate=returning_rate,
            total_sessions=len(sessions),
            total_revenue=total_revenue,
            sessions=sessions,
            current_registrations=registrations_2026,
            session_labels=json.dumps(session_labels),
            session_counts=json.dumps(session_counts),
            age_labels=json.dumps(age_labels),
            age_counts=json.dumps(age_counts),
            grade_labels=json.dumps(grade_labels),
            grade_counts=json.dumps(grade_counts),
            total_new=total_new,
            total_returning=total_returning
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error loading metrics: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/verify-returning-campers')
@require_admin_auth
def verify_returning_campers():
    """Verify returning camper claims against historical database."""
    try:
        db_file = get_database_path()
        print(f"🔍 Verifying returning campers using database: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get current registrations that claim to be returning campers
        cursor.execute("""
            SELECT * FROM registrations 
            WHERE submission_id NOT LIKE 'HIST_%'
            AND is_returning_camper = 1
            ORDER BY timestamp DESC
        """)
        claimed_returning = [dict(row) for row in cursor.fetchall()]
        
        # Get all historical campers for lookup
        cursor.execute("""
            SELECT child_first_name, child_last_name, parent_email, timestamp
            FROM registrations 
            WHERE submission_id LIKE 'HIST_%'
        """)
        historical_campers = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Build lookup set of historical campers (name + email)
        historical_lookup = set()
        for h in historical_campers:
            key = (
                h['child_first_name'].lower().strip(),
                h['child_last_name'].lower().strip(),
                h['parent_email'].lower().strip()
            )
            historical_lookup.add(key)
        
        # Verify each claimed returning camper
        verified_results = []
        for claim in claimed_returning:
            child_first = claim.get('child_first_name', '').lower().strip()
            child_last = claim.get('child_last_name', '').lower().strip()
            parent_email = claim.get('parent_email', '').lower().strip()
            
            key = (child_first, child_last, parent_email)
            is_verified = key in historical_lookup
            
            verified_results.append({
                'id': claim.get('id'),
                'submission_id': claim.get('submission_id'),
                'child_first_name': claim.get('child_first_name'),
                'child_last_name': claim.get('child_last_name'),
                'parent_email': claim.get('parent_email'),
                'timestamp': claim.get('timestamp'),
                'is_verified': is_verified,
                'status': '✅ VERIFIED' if is_verified else '⚠️ UNVERIFIED'
            })
        
        # Calculate stats
        total_claims = len(verified_results)
        verified_count = len([r for r in verified_results if r['is_verified']])
        unverified_count = total_claims - verified_count
        
        stats = {
            'total_claims': total_claims,
            'verified_count': verified_count,
            'unverified_count': unverified_count,
            'fraud_rate': round((unverified_count / total_claims * 100) if total_claims > 0 else 0, 1)
        }
        
        return render_template('verify_returning_campers.html',
                             results=verified_results,
                             stats=stats)
                             
    except Exception as e:
        flash(f'Error verifying returning campers: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/export-json')
def admin_export_json():
    """Export all registrations as JSON for migration."""
    try:
        db_file = get_database_path()
        print(f"💾 Export JSON using database: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Only export current registrations (exclude HIST_ historical records)
        cursor.execute("SELECT * FROM registrations WHERE submission_id NOT LIKE 'HIST_%' ORDER BY timestamp ASC")
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            "success": True,
            "count": len(registrations),
            "exported_at": datetime.now().isoformat(),
            "source_database": db_file,
            "cached_db_file": DB_FILE,
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
        
        db_file = get_database_path()
        print(f"💾 Import JSON using database: {db_file}")
        conn = sqlite3.connect(db_file)
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
        
        db_file = get_database_path()
        print(f"💾 Export CSV using database: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Only export current registrations (exclude HIST_ historical records)
        cursor.execute("SELECT * FROM registrations WHERE submission_id NOT LIKE 'HIST_%' ORDER BY timestamp DESC")
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

@app.route('/admin/edit/<int:registration_id>', methods=['GET', 'POST'])
@require_admin_auth
def admin_edit(registration_id):
    """Edit a specific registration."""
    db_file = get_database_path()
    
    if request.method == 'POST':
        try:
            print(f"✏️ Edit registration {registration_id} using database: {db_file}")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Update the registration
            cursor.execute("""
                UPDATE registrations SET
                    child_first_name = ?,
                    child_last_name = ?,
                    child_age = ?,
                    child_grade = ?,
                    parent_first_name = ?,
                    parent_last_name = ?,
                    parent_email = ?,
                    parent_phone = ?,
                    emergency_contact_name = ?,
                    emergency_contact_phone = ?,
                    has_allergies = ?,
                    allergies_description = ?,
                    has_medical_conditions = ?,
                    medical_conditions_description = ?,
                    is_returning_camper = ?,
                    returning_years = ?,
                    bringing_own_switch = ?,
                    how_heard_about_camp = ?,
                    additional_comments = ?
                WHERE id = ?
            """, (
                request.form.get('child_first_name'),
                request.form.get('child_last_name'),
                request.form.get('child_age'),
                request.form.get('child_grade'),
                request.form.get('parent_first_name'),
                request.form.get('parent_last_name'),
                request.form.get('parent_email'),
                request.form.get('parent_phone'),
                request.form.get('emergency_contact_name'),
                request.form.get('emergency_contact_phone'),
                1 if request.form.get('has_allergies') == 'on' else 0,
                request.form.get('allergies_description', ''),
                1 if request.form.get('has_medical_conditions') == 'on' else 0,
                request.form.get('medical_conditions_description', ''),
                1 if request.form.get('is_returning_camper') == 'on' else 0,
                request.form.get('returning_years', ''),
                1 if request.form.get('bringing_own_switch') == 'on' else 0,
                request.form.get('how_heard_about_camp', ''),
                request.form.get('additional_comments', ''),
                registration_id
            ))
            
            conn.commit()
            conn.close()
            
            flash('Registration updated successfully', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Update error: {str(e)}', 'error')
            return redirect(url_for('admin_dashboard'))
    
    # GET request - show edit form
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM registrations WHERE id = ?", (registration_id,))
        registration = cursor.fetchone()
        conn.close()
        
        if not registration:
            flash('Registration not found', 'error')
            return redirect(url_for('admin_dashboard'))
        
        return render_template('edit_registration.html', registration=registration)
        
    except Exception as e:
        flash(f'Error loading registration: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/import-historical', methods=['POST'])
@require_admin_auth
def import_historical_data():
    """Import historical camper data from CSV file."""
    try:
        import csv
        
        # Try multiple possible paths for Railway compatibility
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'Camp_Power_Up_past_forms - Sheet1.csv'),
            os.path.join('/app', 'data', 'Camp_Power_Up_past_forms - Sheet1.csv'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'Camp_Power_Up_past_forms - Sheet1.csv')
        ]
        
        csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break
        
        if not csv_path:
            flash(f'Historical data file not found. Tried paths: {", ".join(possible_paths)}', 'error')
            return redirect(url_for('admin_dashboard'))
        
        db_file = get_database_path()
        print(f"📥 Importing historical data from: {csv_path}")
        print(f"📥 Using database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Extract data from CSV columns
                    child_first_name = row.get('Childs First Name?', '').strip()
                    child_last_name = row.get('Childs Last Name?', '').strip()
                    parent_email = row.get('Email Address', '').strip()
                    
                    # Skip rows without basic info
                    if not child_first_name or not child_last_name:
                        skipped_count += 1
                        continue
                    
                    # Check if already imported (by email + child name)
                    cursor.execute("""
                        SELECT id FROM registrations 
                        WHERE child_first_name = ? AND child_last_name = ? AND parent_email = ?
                    """, (child_first_name, child_last_name, parent_email))
                    
                    if cursor.fetchone():
                        skipped_count += 1
                        continue
                    
                    # Parse and map CSV fields to database schema
                    age = row.get('Age?', '').strip()
                    grade = row.get('Grade?', '').strip()
                    is_returning = row.get('Has your Child attended Camp Power-Up before?', '').strip().lower() == 'yes'
                    bringing_switch = row.get('Will your child be bringing their own personal Switch?', '').strip().lower() == 'yes'
                    
                    # Medical info
                    has_allergies_text = row.get('allergies?', '').strip().lower()
                    has_allergies = has_allergies_text in ['yes', 'y']
                    allergies_desc = row.get('If yes, please list any medical conditions or allergies', '').strip()
                    
                    has_sensory = row.get('any sensory issues?', '').strip().lower() in ['yes', 'y']
                    sensory_desc = row.get('If yes please describe?  ', '').strip()
                    
                    # Combine medical info
                    medical_desc = []
                    if sensory_desc:
                        medical_desc.append(f"Sensory: {sensory_desc}")
                    medical_conditions_text = ' | '.join(medical_desc) if medical_desc else ''
                    
                    # Additional info
                    gaming_behavior = row.get('Can you describe what your child is like playing video games around others? Are they good at taking turns? Are they a good sport?', '').strip()
                    game_restrictions = row.get('Is there a rating of games your child is not allowed to play?', '').strip()
                    favorite_games = row.get('What games do they enjoy playing?', '').strip()
                    
                    # Combine into additional comments
                    comments = []
                    if gaming_behavior:
                        comments.append(f"Gaming Behavior: {gaming_behavior}")
                    if game_restrictions:
                        comments.append(f"Game Restrictions: {game_restrictions}")
                    if favorite_games:
                        comments.append(f"Favorite Games: {favorite_games}")
                    additional_comments = ' | '.join(comments)
                    
                    # Generate submission ID
                    timestamp = row.get('Timestamp', datetime.now().strftime('%m/%d/%Y %H:%M:%S'))
                    submission_id = f"HIST_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
                    
                    # Insert into database
                    cursor.execute("""
                        INSERT INTO registrations (
                            submission_id, timestamp, child_first_name, child_last_name, 
                            child_age, child_grade, parent_email,
                            has_allergies, allergies_description, 
                            has_medical_conditions, medical_conditions_description,
                            is_returning_camper, bringing_own_switch, additional_comments
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        submission_id, timestamp, child_first_name, child_last_name,
                        age, grade, parent_email,
                        has_allergies, allergies_desc,
                        has_sensory, medical_conditions_text,
                        is_returning, bringing_switch, additional_comments
                    ))
                    
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Error importing row: {e}")
                    error_count += 1
                    continue
        
        conn.commit()
        conn.close()
        
        print(f"📊 Import results - Imported: {imported_count}, Skipped: {skipped_count}, Errors: {error_count}")
        flash(f'✅ Import complete! Imported: {imported_count}, Skipped (duplicates): {skipped_count}, Errors: {error_count}', 'success')
        return redirect(url_for('admin_historical'))
        
    except Exception as e:
        flash(f'Import error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/fix-historical-records', methods=['POST'])
@require_admin_auth
def fix_historical_records():
    """One-time fix: Add HIST_ prefix to imported historical records by matching against CSV."""
    try:
        import csv
        
        # First, load all names/emails from CSV
        csv_path = None
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'Camp_Power_Up_past_forms - Sheet1.csv'),
            os.path.join('/app', 'data', 'Camp_Power_Up_past_forms - Sheet1.csv'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'Camp_Power_Up_past_forms - Sheet1.csv')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break
        
        if not csv_path:
            flash('CSV file not found for verification', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Build set of historical campers from CSV
        historical_campers = set()
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                first_name = row.get('Childs First Name?', '').strip()
                last_name = row.get('Childs Last Name?', '').strip()
                email = row.get('Email Address', '').strip()
                if first_name and last_name:
                    historical_campers.add((first_name.lower(), last_name.lower(), email.lower()))
        
        db_file = get_database_path()
        print(f"🔧 Fixing historical records in database: {db_file}")
        print(f"📚 Found {len(historical_campers)} unique campers in CSV")
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Find ALL records without HIST_ prefix
        cursor.execute("""
            SELECT id, submission_id, child_first_name, child_last_name, parent_email
            FROM registrations 
            WHERE submission_id NOT LIKE 'HIST_%'
        """)
        
        all_records = cursor.fetchall()
        print(f"🔍 Found {len(all_records)} records without HIST_ prefix")
        updated_count = 0
        
        for record in all_records:
            record_id, old_submission_id, first_name, last_name, email = record
            
            # Check if this record matches a historical camper from CSV
            key = (first_name.lower(), last_name.lower(), email.lower())
            if key in historical_campers:
                # Generate new HIST_ ID
                new_submission_id = f"HIST_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
                
                cursor.execute("""
                    UPDATE registrations 
                    SET submission_id = ?
                    WHERE id = ?
                """, (new_submission_id, record_id))
                
                updated_count += 1
                print(f"✅ Updated: {first_name} {last_name} ({email}) - {old_submission_id} → {new_submission_id}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully updated {updated_count} records with HIST_ prefix")
        flash(f'✅ Fixed {updated_count} historical records with HIST_ prefix', 'success')
        return redirect(url_for('admin_historical'))
        
    except Exception as e:
        flash(f'Fix error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:registration_id>', methods=['POST'])
@require_admin_auth
def admin_delete(registration_id):
    """Delete a specific registration."""
    try:
        db_file = get_database_path()
        print(f"🗑️ Delete using database: {db_file}")
        conn = sqlite3.connect(db_file)
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

@app.route('/admin/mark-paid/<submission_id>', methods=['POST'])
@require_admin_auth
def mark_paid(submission_id):
    """Mark a registration as paid."""
    try:
        db_file = get_database_path()
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE registrations 
            SET payment_status = 'paid' 
            WHERE submission_id = ?
        """, (submission_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Payment status updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/attendance')
@require_admin_auth
def attendance():
    """Daily attendance check-in page."""
    try:
        db_file = get_database_path()
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all active registrations (not historical)
        cursor.execute("""
            SELECT * FROM registrations 
            WHERE submission_id NOT LIKE 'HIST_%'
            ORDER BY child_last_name, child_first_name
        """)
        
        registrations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Get today's date to highlight current day
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        return render_template('attendance.html', 
                             registrations=registrations,
                             today=today,
                             camp_dates=['2025-11-24', '2025-11-25'])
    except Exception as e:
        flash(f'Error loading attendance: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/attendance/check-in', methods=['POST'])
@require_admin_auth
def check_in():
    """Record attendance check-in."""
    try:
        data = request.get_json()
        submission_id = data.get('submission_id')
        date = data.get('date')
        status = data.get('status', 'present')  # present, absent, late
        
        db_file = get_database_path()
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create attendance table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(submission_id, date)
            )
        """)
        
        # Insert or update attendance
        cursor.execute("""
            INSERT INTO attendance (submission_id, date, status)
            VALUES (?, ?, ?)
            ON CONFLICT(submission_id, date) 
            DO UPDATE SET status = ?, checked_in_at = CURRENT_TIMESTAMP
        """, (submission_id, date, status, status))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/attendance/status/<date>')
@require_admin_auth
def get_attendance_status(date):
    """Get attendance status for a specific date."""
    try:
        db_file = get_database_path()
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT submission_id, status, checked_in_at
            FROM attendance
            WHERE date = ?
        """, (date,))
        
        attendance = {row['submission_id']: {
            'status': row['status'],
            'checked_in_at': row['checked_in_at']
        } for row in cursor.fetchall()}
        
        conn.close()
        return jsonify(attendance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database on module load (Railway compatibility)
print("🔧 Initializing database on startup...")
init_db_with_logging()
print(f"📁 Database configured at: {DB_FILE}")
print(f"🗄️ Database exists: {os.path.exists(DB_FILE)}")

if __name__ == '__main__':
    print("Starting Camp Power-Up Registration System...")
    print(f"Environment: {'Railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Local'}")
    print(f"Database: {DB_FILE}")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)