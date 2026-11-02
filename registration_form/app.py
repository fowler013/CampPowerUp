#!/usr/bin/env python3
"""
EMERGENCY CLEAN VERSION - Camp Power-Up Registration 
==================================================
Ultra-minimal version to get registration working immediately
"""

import os
import re
import secrets
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, time
from zoneinfo import ZoneInfo
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, g, has_request_context
from functools import wraps
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Import the registration app's config in package deployments and direct runs.
if __package__:
    from .admin_support import (
        ConfigurationConflict, configuration_revision, is_checked,
        load_configurations, normalize_registration, registration_identity_error, registration_summary,
        save_configuration, validate_configuration_update,
    )
    from .camp_config import (
        CAMP_CONFIG,
        SESSIONS,
        DEFAULT_SESSION_ID,
        get_camp_title,
        get_camp_subtitle,
        get_pricing_text,
        get_session_config,
        get_session_label,
        get_pricing_text_for,
    )
else:
    from admin_support import (
        ConfigurationConflict, configuration_revision, is_checked,
        load_configurations, normalize_registration, registration_identity_error, registration_summary,
        save_configuration, validate_configuration_update,
    )
    from camp_config import (
        CAMP_CONFIG,
        SESSIONS,
        DEFAULT_SESSION_ID,
        get_camp_title,
        get_camp_subtitle,
        get_pricing_text,
        get_session_config,
        get_session_label,
        get_pricing_text_for,
    )

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


@app.before_request
def load_request_configuration():
    """Read settings per request so every worker uses the same saved configuration."""
    if request.path.startswith((DISCORD_ATTENDANCE_PREFIX, DISCORD_ATTENDANCE_ADMIN_PREFIX,
                                DISCORD_ATTENDANCE_CAMP_DAY_PREFIX)):
        # This API authenticates before opening its database and owns its session scope.
        return None
    try:
        g.active_camp_configs, g.stored_camp_configs = load_configurations(get_database_path())
    except (sqlite3.Error, ValueError, OSError):
        app.logger.exception("Unable to load saved camp configuration")
        return "Camp settings could not be loaded. Please try again or contact the camp administrator.", 503


def get_active_config(session_id=None):
    """Resolve an offered session using saved settings or its code defaults."""
    session_id = session_id or DEFAULT_SESSION_ID
    if has_request_context():
        saved = getattr(g, "active_camp_configs", {}).get(session_id)
        if saved is not None:
            return saved
    return get_session_config(session_id)


def get_config_for_stored_session(camp_session_label):
    """Resolve a stored `camp_session` label to a known session config."""
    if not camp_session_label:
        return None
    if has_request_context():
        saved = getattr(g, "stored_camp_configs", {}).get(camp_session_label)
        if saved is not None:
            return saved
    for config in SESSIONS.values():
        if get_session_label(config) == camp_session_label:
            return config
    return None


def selected_session():
    """Default only the dashboard to the current camp; preserve explicit labels."""
    selection = request.args.get("session")
    if not selection and request.endpoint == "admin_dashboard":
        return get_session_label(get_active_config())
    return selection or "all"


def read_registrations(session_filter="all"):
    """Read non-historical registrations, optionally scoped to an exact session."""
    query = "SELECT * FROM registrations WHERE submission_id NOT GLOB 'HIST_*'"
    parameters = ()
    if session_filter != "all":
        query += " AND camp_session = ?"
        parameters = (session_filter,)
    with closing(sqlite3.connect(get_database_path())) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query + " ORDER BY timestamp DESC", parameters).fetchall()
    return [dict(row) for row in rows]


def admin_url(endpoint="admin_dashboard", **values):
    """Keep the selected session when moving between related admin pages."""
    values.setdefault("session", selected_session())
    return url_for(endpoint, **values)


def admin_csrf_token():
    """Create the session-bound token used by admin mutation forms."""
    if "admin_csrf_token" not in session:
        session["admin_csrf_token"] = secrets.token_urlsafe(32)
    return session["admin_csrf_token"]


@app.context_processor
def admin_template_helpers():
    return {"admin_url": admin_url, "admin_csrf_token": admin_csrf_token}


def require_admin_csrf(function):
    """Reject admin writes without the token issued to the signed-in browser."""
    @wraps(function)
    def protected(*args, **kwargs):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
            expected = session.get("admin_csrf_token", "")
            if not expected or not secrets.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
                app.logger.warning("Rejected admin write with an invalid CSRF token")
                return jsonify(success=False, error="Your form expired. Reload the page and try again."), 400
        return function(*args, **kwargs)
    return protected

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

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_registrations_camp_session_timestamp
            ON registrations (camp_session, timestamp DESC)
        """)
        
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
                                        how_heard_about_camp, additional_comments, camp_session, payment_status
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                                    reg.get('additional_comments'), reg.get('camp_session'),
                                    reg.get('payment_status') or 'pending'
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
        
        session_id = registration_data.get('camp_session_id') or DEFAULT_SESSION_ID
        session_cfg = get_active_config(session_id) or get_active_config()
        tier_key = 'returning_camper' if is_returning else 'new_camper'
        tier = session_cfg['pricing'][tier_key]
        deposit = f"${tier['deposit']}"
        final_payment = f"${tier['final_payment']}"
        total = f"${tier['total']}"
        camp_name_display = session_cfg.get('camp_name', 'Camp Power-Up')
        camp_dates_display = session_cfg.get('camp_dates', '')
        daily_hours_display = session_cfg.get('daily_hours', '10:00 AM - 3:00 PM')
        final_due_display = session_cfg.get('final_payment_due', '')
        
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
                    <p>Welcome to {camp_name_display}</p>
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
                        <p><strong>Camp Dates:</strong> {camp_dates_display}</p>
                        <p><strong>Camp Times:</strong> {daily_hours_display} daily</p>
                    </div>
                    
                    <div class="payment-box">
                        <h2>💳 Payment Information</h2>
                        <p><strong>Total Fee:</strong> {total}</p>
                        <p><strong>Deposit Required Now:</strong> {deposit}</p>
                        <p><strong>Final Payment:</strong> {final_payment} (due before {final_due_display})</p>
                        
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
                            <li>Mark your calendar: {camp_dates_display}</li>
                            <li>Pay final {final_payment} before {final_due_display}</li>
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
                    <p>{camp_name_display} | {camp_dates_display}</p>
                    <p><a href="https://camppowerup-registration.up.railway.app/confirmation/{submission_id}">View Your Confirmation Online</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        {camp_name_display} - Registration Confirmed
        
        Dear {parent_name},
        
        Thank you for registering {child_name} for Camp Power-Up!
        
        REGISTRATION DETAILS:
        Confirmation ID: {submission_id}
        Camper: {child_name}
        Age: {registration_data.get('child_age', 'N/A')}
        Grade: {registration_data.get('child_grade', 'N/A')}
        Camp Dates: {camp_dates_display}
        Camp Times: {daily_hours_display} daily
        
        PAYMENT INFORMATION:
        Total Fee: {total}
        Deposit Required Now: {deposit}
        Final Payment: {final_payment} (due before {final_due_display})
        
        Payment Methods:
        - CashApp: $TevinFowler
        - Venmo: @Tevin-Fowler or @Brandon-Ballard
        
        IMPORTANT: Include "{child_name}" in the payment memo
        
        NEXT STEPS:
        1. Complete your {deposit} deposit payment
        2. Save this email for your records
        3. Mark your calendar: {camp_dates_display}
        4. Pay final {final_payment} before {final_due_display}
        
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
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    print("⚠️ ADMIN_PASSWORD environment variable is not set - admin login is DISABLED. "
          "Set ADMIN_PASSWORD to enable the admin dashboard.")

def require_admin_auth(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.is_json or request.accept_mimetypes.best == "application/json":
                return jsonify(success=False, error="Your admin session expired. Sign in again."), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Keep the old init_db for backward compatibility
def init_db():
    """Legacy database initialization.""" 
    return init_db_with_logging()

@app.route('/debug-all-registrations')
@require_admin_auth
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
        config = get_active_config()
        pricing = get_pricing_text_for(config)
        
        # Use dynamic camp config
        camp_config = {
            'camp_name': config['camp_name'],
            'camp_dates': config.get('camp_dates', ''),
            'camp_times': config.get('daily_hours', ''),
            'pricing': config.get('pricing', {})
        }
        
        return render_template('registration_form.html', 
                             camp_config=camp_config,
                             config=config,
                             camp_title=config['camp_name'] + ' Registration',
                             camp_subtitle=f"Nintendo Switch Gaming Camp - {config.get('camp_dates', '')}",
                             pricing_text='Registration fees listed below',
                             pricing=pricing,
                             camp_session_id=DEFAULT_SESSION_ID,
                             deposit_amount=config['pricing']['new_camper']['deposit'])
    except Exception as e:
        app.logger.exception("Unable to load the registration form")
        return "The registration form could not be loaded. Please try again or contact the camp administrator.", 500


@app.route('/session/july-2026')
def july_2026_registration():
    """Redirect the expired July session URL to current registration."""
    return redirect(url_for('home'))

@app.route('/faq')
def faq():
    """Display the FAQ page."""
    return render_template('faq.html', config=get_active_config())

@app.route('/test-template')
@require_admin_auth
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
@require_admin_auth
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
@require_admin_auth
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
@require_admin_auth
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
@require_admin_auth
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
        
        # Only Railway volume variables are non-secret paths; others (e.g. DATABASE_URL) may hold credentials.
        volume_env_vars = {k: v for k, v in os.environ.items() if k.startswith('RAILWAY_VOLUME_')}
        
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
@require_admin_auth
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
        
        # Method 6: Environment variable names only; values may be secrets.
        results["env_var_names"] = sorted(os.environ)
        
        return jsonify(results)
    except Exception:
        app.logger.exception("Volume search failed")
        return jsonify({"error": "Volume search failed"}), 500

@app.route('/submit', methods=['POST'])
def submit():
    """Handle registration - accepts JSON data."""
    try:
        # Get JSON data from request
        json_data = request.get_json(silent=True)
        if not isinstance(json_data, dict) or not json_data:
            return jsonify({"success": False, "error": "A registration JSON object is required."}), 400
        session_id = json_data.get('camp_session_id') or json_data.get('campSessionId') or DEFAULT_SESSION_ID
        if not isinstance(session_id, str):
            return jsonify(success=False, error="Choose a valid camp session."), 400
        session_cfg = get_active_config(session_id)
        if session_cfg is None:
            return jsonify(success=False, error="This camp session is not available for registration."), 400
        if not session_cfg.get("registration_open", True):
            return jsonify(success=False, error="Registration is closed for this camp session."), 409
        
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
            'allergies_description': json_data.get('allergies_description') or json_data.get('allergiesDescription') or json_data.get('allergy_details', ''),
            'has_medical_conditions': json_data.get('has_medical_conditions', json_data.get('hasMedicalConditions', json_data.get('has_sensory_issues', False))),
            'medical_conditions_description': json_data.get('medical_conditions_description') or json_data.get('medicalConditionsDescription') or json_data.get('sensory_details', ''),
            'is_returning_camper': json_data.get('is_returning_camper', json_data.get('isReturningCamper', False)),
            'returning_years': json_data.get('returning_years') or json_data.get('returningYears') or json_data.get('previous_year', ''),
            'bringing_own_switch': json_data.get('bringing_own_switch', json_data.get('bringingOwnSwitch', False)),
            'how_heard_about_camp': json_data.get('how_heard_about_camp') or json_data.get('howHeardAboutCamp', ''),
            'additional_comments': json_data.get('additional_comments') or json_data.get('additionalComments') or json_data.get('additional_notes', '')
        }
        boolean_fields = {'is_returning_camper', 'bringing_own_switch', 'has_allergies', 'has_medical_conditions'}
        for field, value in data.items():
            if field in boolean_fields:
                data[field] = int(is_checked(value))
            elif field != 'child_age':
                if not isinstance(value, str) or len(value) > 10000:
                    return jsonify(success=False, error=f"Invalid {field.replace('_', ' ')}."), 400
                data[field] = value.strip()
        identity_error = registration_identity_error(data)
        if identity_error:
            return jsonify(success=False, error=identity_error), 400
        data['child_age'] = int(data['child_age'])
        notes = [data['additional_comments']] if data['additional_comments'] else []
        for field, label in (
            ('child_gender', 'Gender'), ('previous_instructor', 'Previous instructors'),
            ('returning_camper_details', 'Previous camp experience'),
            ('gaming_behavior', 'Gaming behavior'), ('game_restrictions', 'Game restrictions'),
            ('favorite_games', 'Favorite games'), ('games_owned', 'Games owned'),
            ('console_experience', 'Console experience'),
        ):
            value = json_data.get(field, '')
            if not isinstance(value, str) or len(value) > 10000:
                return jsonify(success=False, error=f"Invalid {label.lower()}."), 400
            if value.strip():
                notes.append(f"{label}: {value.strip()}")
        for field, label in (('photo_permission', 'Photo permission'), ('marketing_permission', 'Future event updates')):
            if field in json_data:
                notes.append(f"{label}: {'Yes' if is_checked(json_data[field]) else 'No'}")
        data['additional_comments'] = '\n'.join(notes)
        
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
            if not init_db_with_logging():
                return jsonify(success=False, error="Registration storage is unavailable. Please try again."), 503
        
        # Connect to database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Determine which camp session this registration is for. The form
        # posts a hidden `camp_session_id` field; fall back to the current
        # default session.
        current_session = get_session_label(session_cfg)
        print(f"📅 Registration session: {session_id} -> {current_session}")
        
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
            'additional_comments': data['additional_comments'],
            'camp_session_id': session_id,
            'camp_session': current_session,
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
        app.logger.exception("Registration could not be saved")
        return jsonify(success=False, error="Registration could not be saved. Please try again or contact the camp administrator."), 500

@app.route('/confirmation/<submission_id>')
def confirmation(submission_id):
    """Show professional confirmation page with registration details."""
    try:
        with closing(sqlite3.connect(get_database_path())) as connection:
            connection.row_factory = sqlite3.Row
            registration = connection.execute(
                "SELECT * FROM registrations WHERE submission_id = ?", (submission_id,)
            ).fetchone()
        if not registration:
            app.logger.warning("A confirmation was requested for a missing registration")
            return "Registration not found. Check your confirmation link or contact the camp administrator before submitting again.", 404
        registration_data = normalize_registration(registration)
        stored_session_config = get_config_for_stored_session(registration_data.get('camp_session'))
        return render_template(
            'confirmation.html', registration=registration_data,
            config=stored_session_config or get_active_config(),
            session_config_known=stored_session_config is not None,
        )
    except Exception:
        app.logger.exception("Unable to load a registration confirmation")
        return "Your registration details could not be loaded. Please try again or contact the camp administrator.", 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if ADMIN_PASSWORD and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
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
        session_filter = selected_session()
        config = get_active_config()
        
        # Use fresh database path for Railway compatibility
        db_file = get_database_path()
        print(f"📊 Admin dashboard using database: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get list of all unique sessions for the filter dropdown
        cursor.execute('''
            SELECT DISTINCT camp_session FROM registrations 
            WHERE camp_session IS NOT NULL AND camp_session != '' AND submission_id NOT GLOB 'HIST_*'
            ORDER BY camp_session DESC
        ''')
        available_sessions = [row['camp_session'] for row in cursor.fetchall()]
        
        # Current session from config
        current_session = get_session_label(config)
        
        # Add current session if not in list
        if current_session not in available_sessions:
            available_sessions.insert(0, current_session)
        
        conn.close()
        if session_filter != "all" and session_filter not in available_sessions:
            available_sessions.insert(0, session_filter)
        registrations = [normalize_registration(row) for row in read_registrations(session_filter)]
        for reg in registrations:
            stored_config = get_config_for_stored_session(reg.get("camp_session"))
            reg["session_pricing"] = stored_config["pricing"] if stored_config else None
        session_stats = registration_summary(registrations)
        if session_stats["invalid_dates"]:
            app.logger.warning("Dashboard omitted %d invalid registration dates from date summaries", session_stats["invalid_dates"])
            flash("Some registration dates are missing or invalid and are excluded from date totals.", "warning")
        camp_config = {
            'camp_name': config['camp_name'],
            'camp_dates': config.get('camp_dates', ''),
            'camp_times': config.get('daily_hours', '')
        }
        
        return render_template('admin_dashboard.html', 
                             registrations=registrations,
                             session_stats=session_stats,
                             camp_config=camp_config,
                             config=config,
                             available_sessions=available_sessions,
                             current_session=current_session,
                             selected_session=session_filter)
                             
    except Exception as e:
        app.logger.exception("Unable to load the admin dashboard")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return "The registration dashboard could not be loaded. Please try again.", 500


@app.route('/admin/config')
@require_admin_auth
def admin_config():
    """Edit settings shared by all application workers."""
    config = get_active_config()
    return render_template(
        "admin_config.html", config=config, config_revision=configuration_revision(config)
    )


@app.route('/admin/update-config', methods=['POST'])
@require_admin_auth
@require_admin_csrf
def update_config():
    """Save validated settings without rewriting source files or registrations."""
    data = request.get_json(silent=True)
    try:
        current = get_active_config()
        updated = validate_configuration_update(current, data)
        save_configuration(
            get_database_path(), DEFAULT_SESSION_ID, current, updated, data.get("config_revision")
        )
    except ConfigurationConflict as error:
        return jsonify(success=False, error=str(error)), 409
    except ValueError as error:
        return jsonify(success=False, error=str(error)), 400
    except (sqlite3.Error, OSError):
        app.logger.exception("Unable to save camp configuration")
        return jsonify(success=False, error="Settings were not saved. Please try again."), 500
    return jsonify(success=True, message="Settings saved. Existing registration sessions were not changed.")

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
        cursor.execute("SELECT COUNT(*) FROM registrations WHERE submission_id GLOB 'HIST_*'")
        total_hist = cursor.fetchone()[0]
        print(f"🔍 Records with HIST_ prefix: {total_hist}")
        
        # Get only historical records (those with HIST_ prefix)
        cursor.execute("""
            SELECT * FROM registrations 
            WHERE submission_id GLOB 'HIST_*'
            ORDER BY timestamp DESC
        """)
        historical_registrations = [normalize_registration(row) for row in cursor.fetchall()]
        
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
                             stats=stats,
                             hist_count=total_hist,
                             csv_data=[])
                             
    except Exception as e:
        flash(f'Error loading historical data: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/analytics')
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
        
        # Imported history comes from the same database, not a second count of the CSV.
        historical_2025 = []
        if selected_session() == "all":
            with closing(sqlite3.connect(get_database_path())) as history_connection:
                history_connection.row_factory = sqlite3.Row
                historical_2025 = [normalize_registration(row) for row in history_connection.execute(
                    "SELECT * FROM registrations WHERE submission_id GLOB 'HIST_*'"
                )]
        if historical_2025:
            # Parse 2025 data
            ages_2025 = []
            grades_2025 = []
            returning_2025 = 0
            new_2025 = 0
            
            for row in historical_2025:
                # Get age
                age_str = str(row.get('child_age') or '').strip()
                if age_str and age_str.isdigit():
                    ages_2025.append(int(age_str))
                    all_ages.append(int(age_str))
                
                # Get grade
                grade = str(row.get('child_grade') or '').strip()
                if grade:
                    grades_2025.append(grade)
                    all_grades.append(grade)
                
                # Check returning status
                is_returning = row['is_returning_camper']
                if is_returning:
                    returning_2025 += 1
                    total_returning += 1
                else:
                    new_2025 += 1
                    total_new += 1
            
            sessions.append({
                'name': 'Imported historical records',
                'total': len(historical_2025),
                'new_campers': new_2025,
                'returning_campers': returning_2025,
                'avg_age': round(sum(ages_2025) / len(ages_2025), 1) if ages_2025 else 0,
                'revenue': None
            })
        
        # --- Load current registrations from Database ---
        current_registrations = [normalize_registration(row) for row in read_registrations(selected_session())]

        # Parse current registrations by stored camp_session label
        grouped_sessions = {}
        for reg in current_registrations:
            session_label = reg.get('camp_session') or 'Unassigned session'
            if session_label not in grouped_sessions:
                grouped_sessions[session_label] = {
                    'label': session_label,
                    'ages': [],
                    'grades': [],
                    'returning': 0,
                    'new': 0,
                    'total': 0,
                }

            group = grouped_sessions[session_label]
            group['total'] += 1

            # Get age
            age = reg.get('child_age')
            if age:
                try:
                    numeric_age = int(age)
                    group['ages'].append(numeric_age)
                    all_ages.append(numeric_age)
                except (TypeError, ValueError):
                    pass
            
            # Get grade
            grade = reg.get('child_grade', '')
            if grade:
                group['grades'].append(grade)
                all_grades.append(grade)
            
            # Check returning status
            is_returning = reg.get('is_returning_camper')
            if isinstance(is_returning, str):
                is_returning = is_returning.lower() in ['true', '1', 'yes']
            else:
                is_returning = bool(is_returning)
            
            if is_returning:
                group['returning'] += 1
                total_returning += 1
            else:
                group['new'] += 1
                total_new += 1

        for session_label, group in grouped_sessions.items():
            session_cfg = get_config_for_stored_session(session_label)
            revenue = None
            if session_cfg is not None:
                returning_price = session_cfg['pricing']['returning_camper']['total']
                new_price = session_cfg['pricing']['new_camper']['total']
                revenue = (group['returning'] * returning_price) + (group['new'] * new_price)

            sessions.append({
                'name': session_label,
                'total': group['total'],
                'new_campers': group['new'],
                'returning_campers': group['returning'],
                'avg_age': round(sum(group['ages']) / len(group['ages']), 1) if group['ages'] else 0,
                'revenue': revenue
            })
        
        # --- Calculate Aggregated Stats ---
        total_campers = len(historical_2025) + len(current_registrations)
        total_revenue = sum(s['revenue'] for s in sessions if s['revenue'] is not None)
        unpriced_registrations = sum(s['total'] for s in sessions if s['revenue'] is None)
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
            current_registrations=current_registrations,
            config=get_active_config(),
            selected_session=selected_session(),
            unpriced_registrations=unpriced_registrations,
            session_labels=session_labels,
            session_counts=session_counts,
            age_labels=age_labels,
            age_counts=age_counts,
            grade_labels=grade_labels,
            grade_counts=grade_counts,
            total_new=total_new,
            total_returning=total_returning
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error loading metrics: {str(e)}', 'error')
        return redirect(admin_url())

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
        
        claimed_returning = [row for row in read_registrations(selected_session()) if is_checked(row.get('is_returning_camper'))]
        
        # Get all historical campers for lookup
        cursor.execute("""
            SELECT child_first_name, child_last_name, parent_email, timestamp
            FROM registrations 
            WHERE submission_id GLOB 'HIST_*'
        """)
        historical_campers = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Build lookup set of historical campers (name + email)
        historical_lookup = set()
        for h in historical_campers:
            key = (
                str(h['child_first_name'] or '').casefold().strip(),
                str(h['child_last_name'] or '').casefold().strip(),
                str(h['parent_email'] or '').casefold().strip()
            )
            if all(key):
                historical_lookup.add(key)
        
        # Verify each claimed returning camper
        verified_results = []
        for claim in claimed_returning:
            child_first = str(claim.get('child_first_name') or '').casefold().strip()
            child_last = str(claim.get('child_last_name') or '').casefold().strip()
            parent_email = str(claim.get('parent_email') or '').casefold().strip()
            
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
                             stats=stats,
                             selected_session=selected_session())
                             
    except Exception as e:
        flash(f'Error verifying returning campers: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/export-json')
@require_admin_auth
def admin_export_json():
    """Export all registrations as JSON for migration."""
    try:
        registrations = read_registrations(selected_session())
        
        return jsonify({
            "success": True,
            "count": len(registrations),
            "exported_at": datetime.now().isoformat(),
            "selected_session": selected_session(),
            "registrations": registrations
        })
    except Exception as e:
        app.logger.exception("Registration JSON export failed")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/import-json', methods=['POST'])
@require_admin_auth
@require_admin_csrf
def admin_import_json():
    """Import registrations from JSON for migration."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get('registrations'), list):
            return jsonify({"success": False, "error": "Invalid JSON format"}), 400
        
        registrations = data['registrations']
        if not all(isinstance(row, dict) and isinstance(row.get('submission_id'), str) and row['submission_id'].strip() for row in registrations):
            return jsonify(success=False, error="Every registration must have a submission ID."), 400
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
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
                        bringing_own_switch, how_heard_about_camp, additional_comments,
                        camp_session, payment_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    reg.get('additional_comments'), reg.get('camp_session'),
                    reg.get('payment_status') or 'pending'
                ))
                imported_count += 1
            except Exception as e:
                app.logger.exception("Invalid row in registration import")
                error_count += 1
        if error_count:
            conn.rollback()
            conn.close()
            return jsonify(success=False, error=f"Import rolled back: {error_count} invalid rows. No records were imported."), 400
        
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
        
        registrations = read_registrations(selected_session())
        
        if not registrations:
            flash('No registrations to export', 'error')
            return redirect(admin_url())
            
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
        return redirect(admin_url())

@app.route('/admin/edit/<int:registration_id>', methods=['GET', 'POST'])
@require_admin_auth
@require_admin_csrf
def admin_edit(registration_id):
    """Edit a specific registration."""
    db_file = get_database_path()
    
    if request.method == 'POST':
        try:
            print(f"✏️ Edit registration {registration_id} using database: {db_file}")
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            existing = cursor.execute("SELECT * FROM registrations WHERE id = ?", (registration_id,)).fetchone()
            if not existing:
                conn.close()
                return "Registration not found.", 404
            identity_error = registration_identity_error(request.form)
            if identity_error:
                conn.close()
                flash(identity_error, "error")
                return render_template(
                    "edit_registration.html",
                    registration=normalize_registration({**dict(existing), **request.form.to_dict()}),
                ), 400
            
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
            return redirect(admin_url())
            
        except Exception as e:
            flash(f'Update error: {str(e)}', 'error')
            return redirect(admin_url())
    
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
        
        return render_template('edit_registration.html', registration=normalize_registration(registration))
        
    except Exception as e:
        flash(f'Error loading registration: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/import-historical', methods=['POST'])
@require_admin_auth
@require_admin_csrf
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
                        WHERE submission_id GLOB 'HIST_*'
                        AND child_first_name = ? AND child_last_name = ? AND parent_email = ?
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
        flash(f'Import results: {imported_count} imported, {skipped_count} skipped, {error_count} errors.', 'warning' if error_count else 'success')
        return redirect(admin_url('admin_historical'))
        
    except Exception as e:
        flash(f'Import error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/upload-historical', methods=['POST'])
@require_admin_auth
@require_admin_csrf
def upload_historical_data():
    """Upload and import historical camper data from CSV file upload."""
    try:
        import csv
        import io
        
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin_historical'))
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin_historical'))
        
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file', 'error')
            return redirect(url_for('admin_historical'))
        
        # Read the CSV content
        content = file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        
        db_file = get_database_path()
        print(f"📥 Uploading historical data to database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
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
                    WHERE submission_id GLOB 'HIST_*'
                    AND child_first_name = ? AND child_last_name = ? AND parent_email = ?
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
                
                # Generate submission ID with HIST_ prefix for historical data
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
        
        print(f"📊 Upload results - Imported: {imported_count}, Skipped: {skipped_count}, Errors: {error_count}")
        flash(f'Import results: {imported_count} imported, {skipped_count} skipped, {error_count} errors.', 'warning' if error_count else 'success')
        return redirect(admin_url('admin_historical'))
        
    except Exception as e:
        flash(f'Upload error: {str(e)}', 'error')
        return redirect(url_for('admin_historical'))

@app.route('/admin/clear-historical', methods=['POST'])
@require_admin_auth
@require_admin_csrf
def clear_historical_data():
    """Clear all historical (HIST_) records from the database."""
    try:
        db_file = get_database_path()
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Count records to delete
        cursor.execute("SELECT COUNT(*) FROM registrations WHERE submission_id GLOB 'HIST_*'")
        count = cursor.fetchone()[0]
        
        # Delete historical records
        cursor.execute("DELETE FROM registrations WHERE submission_id GLOB 'HIST_*'")
        conn.commit()
        conn.close()
        
        print(f"🗑️ Cleared {count} historical records")
        flash(f'✅ Cleared {count} historical records. You can now reimport.', 'success')
        return redirect(url_for('admin_historical'))
        
    except Exception as e:
        flash(f'Clear error: {str(e)}', 'error')
        return redirect(url_for('admin_historical'))

@app.route('/admin/fix-historical-records', methods=['POST'])
@require_admin_auth
@require_admin_csrf
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
                timestamp = row.get('Timestamp', '').strip()
                if first_name and last_name and email and timestamp:
                    historical_campers.add((first_name.casefold(), last_name.casefold(), email.casefold(), timestamp))
        
        db_file = get_database_path()
        print(f"🔧 Fixing historical records in database: {db_file}")
        print(f"📚 Found {len(historical_campers)} unique campers in CSV")
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Only unassigned legacy imports can be repaired; never relabel a submitted registration.
        cursor.execute("""
            SELECT id, submission_id, child_first_name, child_last_name, parent_email, timestamp
            FROM registrations 
            WHERE submission_id NOT GLOB 'HIST_*'
              AND submission_id NOT GLOB 'REG_*'
              AND (camp_session IS NULL OR camp_session = '')
        """)
        
        all_records = cursor.fetchall()
        print(f"🔍 Found {len(all_records)} records without HIST_ prefix")
        updated_count = 0
        
        for record in all_records:
            record_id, old_submission_id, first_name, last_name, email, timestamp = record
            
            # Check if this record matches a historical camper from CSV
            key = tuple(str(value or '').strip().casefold() for value in (first_name, last_name, email)) + (str(timestamp or '').strip(),)
            if key in historical_campers:
                # Generate new HIST_ ID
                new_submission_id = f"HIST_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
                
                cursor.execute("""
                    UPDATE registrations 
                    SET submission_id = ?
                    WHERE id = ?
                """, (new_submission_id, record_id))
                
                updated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully updated {updated_count} records with HIST_ prefix")
        flash(f'Repaired {updated_count} unassigned legacy records with exact CSV matches. Current session registrations were not changed.', 'success')
        return redirect(admin_url('admin_historical'))
        
    except Exception as e:
        flash(f'Fix error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:registration_id>', methods=['POST'])
@require_admin_auth
@require_admin_csrf
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
            return jsonify(success=False, error="Registration not found."), 404
            
        # Delete the registration
        cursor.execute("DELETE FROM registrations WHERE id = ?", (registration_id,))
        conn.commit()
        conn.close()
        
        if request.accept_mimetypes.best == "application/json":
            return jsonify(success=True, message="Registration deleted.")
        flash('Registration deleted successfully', 'success')
        return redirect(admin_url())
        
    except Exception as e:
        app.logger.exception("Registration deletion failed")
        return jsonify(success=False, error="Registration could not be deleted."), 500

@app.route('/admin/mark-paid/<submission_id>', methods=['POST'])
@require_admin_auth
@require_admin_csrf
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
        changed = cursor.rowcount
        conn.commit()
        conn.close()
        if not changed:
            return jsonify(success=False, error="Registration not found."), 404
        
        return jsonify({'success': True, 'message': 'Payment status updated'})
    except Exception as e:
        app.logger.exception("Payment status update failed")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/send-reminder/<submission_id>', methods=['POST'])
@require_admin_auth
@require_admin_csrf
def send_payment_reminder(submission_id):
    """Send a reminder only when a stored registration has known session pricing."""
    try:
        with closing(sqlite3.connect(get_database_path())) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM registrations WHERE submission_id = ?", (submission_id,)
            ).fetchone()
        if row is None:
            return jsonify(success=False, error="Registration not found."), 404
        registration = normalize_registration(row)
        if registration["payment_status"] == "paid":
            return jsonify(success=False, error="This registration is already marked paid."), 409
        config = get_config_for_stored_session(registration.get("camp_session"))
        if config is None:
            return jsonify(success=False, error="Pricing for this session is unavailable. No reminder was sent."), 409
        if not registration.get("parent_email"):
            return jsonify(success=False, error="This registration has no parent email address."), 400
        html = render_template("payment_reminder.html", registration=registration, config=config)
        if not send_email_notification(
            registration["parent_email"], f"Payment reminder - {config['camp_name']}", html
        ):
            return jsonify(success=False, error="The email provider did not confirm delivery. Check email configuration before trying again."), 502
        return jsonify(success=True, message="Payment reminder sent.")
    except Exception:
        app.logger.exception("Payment reminder failed")
        return jsonify(success=False, error="The reminder could not be sent. Check its status before trying again."), 500

@app.route('/admin/attendance')
@require_admin_auth
def attendance():
    """Daily attendance check-in page for the exact current camp."""
    try:
        current_session = get_session_label(get_active_config())
        db_file = get_database_path()
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM registrations 
            WHERE submission_id NOT GLOB 'HIST_*' AND camp_session = ?
            ORDER BY child_last_name, child_first_name
        """, (current_session,))
        
        registrations = [normalize_registration(row) for row in cursor.fetchall()]
        conn.close()
        
        # Get today's date to highlight current day
        for registration in registrations:
            stored_config = get_config_for_stored_session(registration.get("camp_session"))
            registration["session_pricing"] = stored_config["pricing"] if stored_config else None
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        return render_template('attendance.html', 
                             registrations=registrations,
                             current_session=current_session,
                             today=today,
                             camp_dates=['2026-11-23', '2026-11-24'])
    except Exception as e:
        flash(f'Error loading attendance: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/attendance/check-in', methods=['POST'])
@require_admin_auth
@require_admin_csrf
def check_in():
    """Record attendance check-in."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(success=False, error="Attendance must be a JSON object."), 400
        submission_id = data.get('submission_id')
        date = data.get('date')
        status = data.get('status', 'present')  # present, absent, late
        if not isinstance(submission_id, str) or status not in ('present', 'absent', 'late'):
            return jsonify(success=False, error="Choose a valid registration and attendance status."), 400
        try:
            date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            return jsonify(success=False, error="Choose a valid attendance date."), 400
        
        db_file = get_database_path()
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        if not cursor.execute(
            """SELECT 1 FROM registrations
               WHERE submission_id = ? AND submission_id NOT GLOB 'HIST_*'
                 AND camp_session = ?""",
            (submission_id, get_session_label(get_active_config())),
        ).fetchone():
            conn.close()
            return jsonify(success=False, error="Registration not found."), 404
        
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
        if not cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'attendance'"
        ).fetchone():
            conn.close()
            return jsonify({})
        cursor.execute("""
            SELECT a.submission_id, a.status, a.checked_in_at
            FROM attendance AS a
            JOIN registrations AS r ON r.submission_id = a.submission_id
            WHERE a.date = ? AND r.camp_session = ?
              AND r.submission_id NOT GLOB 'HIST_*'
        """, (date, get_session_label(get_active_config())))
        
        attendance = {row['submission_id']: {
            'status': row['status'],
            'checked_in_at': row['checked_in_at']
        } for row in cursor.fetchall()}
        
        conn.close()
        return jsonify(attendance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────
# Challenge Leaderboard
# ─────────────────────────────────────────────────────────

LEADERBOARD_CHALLENGES = {
    'dk_bannooza': {
        'label': 'Donkey Kong Bananaza',
        'metric': 'Bananas in 10 minutes',
        'score_unit': 'bananas',
        'score_direction': 'desc',
        'show_starting_zone': True,
        'show_level_detail': False,
        'time_window': '10:00am – 11:30am',
        'rules': 'Pick a starting zone. Find as many bananas as possible in 10 minutes. Highest count wins. Tie-break: fastest completion time wins. Winners announced at 2:00pm.'
    },
    'mario_kart_world': {
        'label': 'Mario Kart World - Knockout Tour',
        'metric': 'Final placement / points',
        'score_unit': 'points',
        'score_direction': 'asc',
        'show_starting_zone': False,
        'show_level_detail': False,
        'show_race_round': True,
        'time_window': '11:30am – 1:30pm',
        'rules': 'Each kid gets ONE turn with up to 3 races. Score is cumulative placement points (lower is better). Example: 3rd + 2nd + 1st = 6 points. Tie-break: fastest completion time wins. Winners announced at 2:00pm.'
    },
    'hollow_knight_boss_rush': {
        'label': 'Hollow Knight Boss Rush',
        'metric': 'Bosses defeated',
        'score_unit': 'bosses',
        'score_direction': 'desc',
        'show_starting_zone': False,
        'show_level_detail': True,
        'time_window': '1:30pm – 3:00pm',
        'rules': 'Enter Pantheon mode at your chosen difficulty. Score = bosses defeated before losing all health. Tie-break: fastest completion time wins. Record level/difficulty. Winners announced at 2:00pm.'
    }
}


def ensure_leaderboard_table():
    """Create leaderboard table in the registration DB if it does not already exist."""
    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS challenge_leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camper_name TEXT NOT NULL,
                challenge_key TEXT NOT NULL,
                score INTEGER NOT NULL,
                starting_zone TEXT,
                level_detail TEXT,
                race_round INTEGER,
                completion_time_seconds INTEGER,
                run_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        existing_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(challenge_leaderboard)").fetchall()
        }
        if 'completion_time_seconds' not in existing_cols:
            conn.execute(
                'ALTER TABLE challenge_leaderboard ADD COLUMN completion_time_seconds INTEGER'
            )
        if 'race_round' not in existing_cols:
            conn.execute(
                'ALTER TABLE challenge_leaderboard ADD COLUMN race_round INTEGER'
            )

        conn.commit()
    finally:
        conn.close()


def parse_completion_time_to_seconds(raw_value):
    """Parse completion time as seconds. Accepts '', integer seconds, or mm:ss."""
    if raw_value is None:
        return None

    value = str(raw_value).strip()
    if not value:
        return None

    if re.fullmatch(r'\d+', value):
        seconds = int(value)
        if seconds < 0:
            raise ValueError('Completion time must be 0 or greater.')
        return seconds

    match = re.fullmatch(r'(\d{1,2}):(\d{2})', value)
    if match:
        minutes = int(match.group(1))
        secs = int(match.group(2))
        if secs >= 60:
            raise ValueError('Use mm:ss format with seconds from 00 to 59.')
        return (minutes * 60) + secs

    raise ValueError('Completion time must be seconds (e.g. 95) or mm:ss (e.g. 1:35).')


def parse_completion_hms_to_seconds(hours_raw, minutes_raw, seconds_raw):
    """Parse completion time from hour/minute/second fields."""
    h_val = str(hours_raw or '').strip()
    m_val = str(minutes_raw or '').strip()
    s_val = str(seconds_raw or '').strip()

    if not h_val and not m_val and not s_val:
        return None

    if h_val and not re.fullmatch(r'\d+', h_val):
        raise ValueError('Hours must be a whole number.')
    if m_val and not re.fullmatch(r'\d+', m_val):
        raise ValueError('Minutes must be a whole number.')
    if s_val and not re.fullmatch(r'\d+', s_val):
        raise ValueError('Seconds must be a whole number.')

    hours = int(h_val) if h_val else 0
    minutes = int(m_val) if m_val else 0
    seconds = int(s_val) if s_val else 0

    if minutes >= 60 or seconds >= 60:
        raise ValueError('Minutes and seconds must be between 0 and 59.')

    return (hours * 3600) + (minutes * 60) + seconds


def is_submission_locked_after_2pm():
    """Allow score entry only between 10:00am and 2:00pm America/Chicago."""
    now_cst = datetime.now(ZoneInfo('America/Chicago')).time()
    return not (time(10, 0) <= now_cst < time(14, 0))


def fetch_leaderboard_data():
    """Return ranked leaderboard entries grouped by challenge."""
    ensure_leaderboard_table()
    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        leaderboard = {}
        for challenge_key, challenge_info in LEADERBOARD_CHALLENGES.items():
            rows = conn.execute(
                '''
                SELECT id, camper_name, challenge_key, score, starting_zone, level_detail, race_round, completion_time_seconds, run_notes, created_at
                FROM challenge_leaderboard
                WHERE challenge_key = ?
                ''',
                (challenge_key,)
            ).fetchall()

            if challenge_info.get('show_race_round'):
                summary_map = {}
                for row in rows:
                    camper_key = row['camper_name'].strip().lower()
                    group = summary_map.setdefault(camper_key, {
                        'camper_name': row['camper_name'],
                        'total_score': 0,
                        'total_time_seconds': 0,
                        'time_record_count': 0,
                        'race_count': 0,
                        'race_breakdown': [],
                        'created_at': row['created_at']
                    })
                    group['total_score'] += int(row['score'])
                    if row['completion_time_seconds'] is not None:
                        group['total_time_seconds'] += int(row['completion_time_seconds'])
                        group['time_record_count'] += 1
                    group['race_count'] += 1
                    group['race_breakdown'].append({
                        'id': row['id'],
                        'race_round': row['race_round'],
                        'score': int(row['score']),
                        'completion_time_seconds': row['completion_time_seconds'],
                        'run_notes': row['run_notes'] or '',
                        'created_at': row['created_at']
                    })

                summary_entries = []
                grouped_rows = sorted(
                    summary_map.values(),
                    key=lambda item: (
                        item['total_score'],
                        item['total_time_seconds'] if item['time_record_count'] > 0 else 10**9,
                        item['created_at']
                    )
                )
                for idx, group in enumerate(grouped_rows, start=1):
                    breakdown = sorted(group['race_breakdown'], key=lambda item: item['race_round'] or 0)
                    total_time_seconds = group['total_time_seconds'] if group['time_record_count'] > 0 else None
                    summary_entries.append({
                        'rank': idx,
                        'id': breakdown[-1]['created_at'] if breakdown else idx,
                        'camper_name': group['camper_name'],
                        'challenge_key': challenge_key,
                        'score': group['total_score'],
                        'total_score': group['total_score'],
                        'total_time_seconds': total_time_seconds,
                        'race_count': group['race_count'],
                        'race_breakdown': breakdown,
                        'race_round': breakdown[-1]['race_round'] if breakdown else None,
                        'starting_zone': '',
                        'level_detail': '',
                        'completion_time_seconds': total_time_seconds,
                        'run_notes': '',
                        'created_at': group['created_at']
                    })

                detail_rows = sorted(
                    rows,
                    key=lambda row: (
                        row['camper_name'].lower(),
                        row['race_round'] if row['race_round'] is not None else 99,
                        row['created_at']
                    )
                )
                entries = [
                    {
                        'rank': idx,
                        'id': row['id'],
                        'camper_name': row['camper_name'],
                        'challenge_key': row['challenge_key'],
                        'score': row['score'],
                        'starting_zone': row['starting_zone'] or '',
                        'level_detail': row['level_detail'] or '',
                        'race_round': row['race_round'],
                        'completion_time_seconds': row['completion_time_seconds'],
                        'run_notes': row['run_notes'] or '',
                        'created_at': row['created_at']
                    }
                    for idx, row in enumerate(detail_rows, start=1)
                ]

                leaderboard[challenge_key] = {
                    'challenge': challenge_info,
                    'entries': entries,
                    'summary_entries': summary_entries,
                    'trophy_winner': summary_entries[0] if summary_entries else None
                }
            else:
                reverse_scores = challenge_info.get('score_direction', 'desc') != 'asc'
                sorted_rows = sorted(
                    rows,
                    key=lambda row: (
                        row['score'],
                        row['completion_time_seconds'] if row['completion_time_seconds'] is not None else 10**9,
                        row['created_at']
                    ),
                    reverse=reverse_scores
                )

                if reverse_scores:
                    sorted_rows = sorted(
                        sorted_rows,
                        key=lambda row: row['completion_time_seconds'] if row['completion_time_seconds'] is not None else 10**9
                    )
                    sorted_rows = sorted(
                        sorted_rows,
                        key=lambda row: row['score'],
                        reverse=True
                    )

                entries = [
                    {
                        'rank': idx,
                        'id': row['id'],
                        'camper_name': row['camper_name'],
                        'challenge_key': row['challenge_key'],
                        'score': row['score'],
                        'starting_zone': row['starting_zone'] or '',
                        'level_detail': row['level_detail'] or '',
                        'race_round': row['race_round'],
                        'completion_time_seconds': row['completion_time_seconds'],
                        'run_notes': row['run_notes'] or '',
                        'created_at': row['created_at']
                    }
                    for idx, row in enumerate(sorted_rows, start=1)
                ]

                leaderboard[challenge_key] = {
                    'challenge': challenge_info,
                    'entries': entries,
                    'trophy_winner': entries[0] if entries else None
                }

        return leaderboard
    finally:
        conn.close()


@app.route('/leaderboard')
def leaderboard_page():
    """Render the challenge leaderboard page."""
    return render_template('leaderboard.html')


@app.route('/api/leaderboard/challenges')
def get_leaderboard_challenges():
    """Return configured challenge metadata."""
    return jsonify(LEADERBOARD_CHALLENGES)


@app.route('/api/leaderboard')
def get_leaderboard():
    """Return all leaderboard entries grouped by challenge."""
    return jsonify(fetch_leaderboard_data())


@app.route('/api/leaderboard/submit', methods=['POST'])
def submit_leaderboard_score():
    """Accept one camper score submission."""
    data = request.get_json(silent=True) or {}

    camper_name = str(data.get('camper_name', '')).strip()
    challenge_key = str(data.get('challenge_key', '')).strip()
    starting_zone = str(data.get('starting_zone', '')).strip()
    level_detail = str(data.get('level_detail', '')).strip()
    entry_id_raw = data.get('entry_id', '')
    race_round_raw = data.get('race_round', '')
    completion_time = data.get('completion_time', '')
    completion_hours = data.get('completion_hours', '')
    completion_minutes = data.get('completion_minutes', '')
    completion_seconds_raw = data.get('completion_seconds', '')
    allow_after_deadline = bool(data.get('allow_after_deadline', False))
    run_notes = str(data.get('run_notes', '')).strip()
    entry_id = None
    if str(entry_id_raw).strip():
        try:
            entry_id = int(entry_id_raw)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid entry id.'}), 400

    if not camper_name:
        return jsonify({'error': 'Camper name is required.'}), 400

    if challenge_key not in LEADERBOARD_CHALLENGES:
        return jsonify({'error': 'Invalid challenge selected.'}), 400

    challenge_info = LEADERBOARD_CHALLENGES[challenge_key]
    race_round = None
    if challenge_info.get('show_race_round'):
        try:
            race_round = int(race_round_raw)
        except (TypeError, ValueError):
            return jsonify({'error': 'Race / Heat is required for Mario Kart.'}), 400
        if race_round < 1 or race_round > 3:
            return jsonify({'error': 'Race / Heat must be 1, 2, or 3.'}), 400

    if is_submission_locked_after_2pm() and not allow_after_deadline:
        return jsonify({'error': 'Score entry is allowed from 10:00am to 2:00pm CST. Enable staff override to submit outside this window.'}), 400

    try:
        score = int(data.get('score'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Score must be a whole number.'}), 400

    if score < 0:
        return jsonify({'error': 'Score must be 0 or greater.'}), 400

    try:
        completion_time_seconds = parse_completion_hms_to_seconds(
            completion_hours,
            completion_minutes,
            completion_seconds_raw
        )
        if completion_time_seconds is None:
            completion_time_seconds = parse_completion_time_to_seconds(completion_time)
    except ValueError as err:
        return jsonify({'error': str(err)}), 400

    ensure_leaderboard_table()
    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    try:
        if entry_id is not None:
            exists = conn.execute(
                'SELECT id FROM challenge_leaderboard WHERE id = ?',
                (entry_id,)
            ).fetchone()
            if not exists:
                return jsonify({'error': 'Entry not found for editing.'}), 404

        if race_round is not None:
            if entry_id is not None:
                existing = conn.execute(
                    '''
                    SELECT COUNT(*)
                    FROM challenge_leaderboard
                    WHERE challenge_key = ? AND camper_name = ? AND race_round = ? AND id != ?
                    ''',
                    (challenge_key, camper_name, race_round, entry_id)
                ).fetchone()[0]
            else:
                existing = conn.execute(
                    '''
                    SELECT COUNT(*)
                    FROM challenge_leaderboard
                    WHERE challenge_key = ? AND camper_name = ? AND race_round = ?
                    ''',
                    (challenge_key, camper_name, race_round)
                ).fetchone()[0]
            if existing:
                return jsonify({'error': 'That camper already has a score for this race number.'}), 400

        if entry_id is None:
            conn.execute(
                '''
                INSERT INTO challenge_leaderboard (camper_name, challenge_key, score, starting_zone, level_detail, race_round, completion_time_seconds, run_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    camper_name,
                    challenge_key,
                    score,
                    starting_zone or None,
                    level_detail or None,
                    race_round,
                    completion_time_seconds,
                    run_notes or None
                )
            )
        else:
            conn.execute(
                '''
                UPDATE challenge_leaderboard
                SET camper_name = ?,
                    challenge_key = ?,
                    score = ?,
                    starting_zone = ?,
                    level_detail = ?,
                    race_round = ?,
                    completion_time_seconds = ?,
                    run_notes = ?
                WHERE id = ?
                ''',
                (
                    camper_name,
                    challenge_key,
                    score,
                    starting_zone or None,
                    level_detail or None,
                    race_round,
                    completion_time_seconds,
                    run_notes or None,
                    entry_id
                )
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        'success': True,
        'message': 'Score submitted successfully.',
        'leaderboard': fetch_leaderboard_data()
    })


@app.route('/api/leaderboard/delete/<int:entry_id>', methods=['DELETE'])
@require_admin_auth
def delete_leaderboard_entry(entry_id):
    """Delete one leaderboard score entry by id."""
    ensure_leaderboard_table()
    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.execute(
            'DELETE FROM challenge_leaderboard WHERE id = ?',
            (entry_id,)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry not found.'}), 404
    finally:
        conn.close()

    return jsonify({
        'success': True,
        'message': 'Entry deleted.',
        'leaderboard': fetch_leaderboard_data()
    })


# ─────────────────────────────────────────────────────────
# Challenge Sign-Up Queue
# ─────────────────────────────────────────────────────────

def ensure_signups_table():
    """Create challenge_signups table if it does not already exist."""
    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS challenge_signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camper_name TEXT NOT NULL,
                challenge_key TEXT NOT NULL,
                status TEXT DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    finally:
        conn.close()


def fetch_signup_queues():
    """Return all sign-up queues grouped by challenge, ordered by sign-up time."""
    ensure_signups_table()
    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        queues = {}
        for key, info in LEADERBOARD_CHALLENGES.items():
            rows = conn.execute(
                'SELECT id, camper_name, challenge_key, status, created_at FROM challenge_signups WHERE challenge_key = ? ORDER BY created_at ASC',
                (key,)
            ).fetchall()
            queues[key] = {
                'challenge': info,
                'entries': [dict(r) for r in rows]
            }
        return queues
    finally:
        conn.close()


@app.route('/api/signups')
def get_signups():
    """Return all sign-up queues."""
    return jsonify(fetch_signup_queues())


@app.route('/api/signups/add', methods=['POST'])
def add_signup():
    """Add a camper to a challenge sign-up queue."""
    ensure_signups_table()
    data = request.get_json() or {}
    camper_name = str(data.get('camper_name', '')).strip()
    challenge_key = str(data.get('challenge_key', '')).strip()

    if not camper_name:
        return jsonify({'error': 'Camper name is required.'}), 400
    if challenge_key not in LEADERBOARD_CHALLENGES:
        return jsonify({'error': 'Invalid challenge.'}), 400

    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            'INSERT INTO challenge_signups (camper_name, challenge_key, status) VALUES (?, ?, ?)',
            (camper_name, challenge_key, 'waiting')
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'queues': fetch_signup_queues()})


@app.route('/api/signups/<int:signup_id>/status', methods=['POST'])
def update_signup_status(signup_id):
    """Update a sign-up entry status (waiting → playing → done)."""
    ensure_signups_table()
    data = request.get_json() or {}
    new_status = str(data.get('status', '')).strip()
    if new_status not in ('waiting', 'playing', 'done', 'skipped'):
        return jsonify({'error': 'Invalid status.'}), 400

    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    try:
        conn.execute('UPDATE challenge_signups SET status = ? WHERE id = ?', (new_status, signup_id))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'queues': fetch_signup_queues()})


@app.route('/api/signups/<int:signup_id>/remove', methods=['DELETE'])
def remove_signup(signup_id):
    """Remove a sign-up entry."""
    ensure_signups_table()
    db_file = get_database_path()
    conn = sqlite3.connect(db_file)
    try:
        conn.execute('DELETE FROM challenge_signups WHERE id = ?', (signup_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'queues': fetch_signup_queues()})


if __package__:
    from .discord_attendance import (
        PREFIX as DISCORD_ATTENDANCE_PREFIX,
        ADMIN_PREFIX as DISCORD_ATTENDANCE_ADMIN_PREFIX,
        CAMP_DAY_PREFIX as DISCORD_ATTENDANCE_CAMP_DAY_PREFIX,
        register_discord_attendance,
    )
else:
    from discord_attendance import (
        PREFIX as DISCORD_ATTENDANCE_PREFIX,
        ADMIN_PREFIX as DISCORD_ATTENDANCE_ADMIN_PREFIX,
        CAMP_DAY_PREFIX as DISCORD_ATTENDANCE_CAMP_DAY_PREFIX,
        register_discord_attendance,
    )

register_discord_attendance(
    app, lambda: get_database_path(), require_admin_auth, require_admin_csrf,
    lambda: ADMIN_USERNAME,
)

@app.route(DISCORD_ATTENDANCE_ADMIN_PREFIX, methods=["GET"])
@require_admin_auth
def admin_discord_attendance():
    """Render the private parent-link and authorized-pickup administration page."""
    return render_template("admin_discord_attendance.html", config=get_active_config())

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