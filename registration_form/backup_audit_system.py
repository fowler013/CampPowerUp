#!/usr/bin/env python3
"""
Camp Power-Up Registration Backup & Audit System
Daily cronjob to backup registrations and track changes
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from database_config import get_db_connection, DB_CONFIG
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("⚠️ SendGrid not installed. Email reports will be disabled.")

# Configuration
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
AUDIT_LOG_DIR = os.path.join(os.path.dirname(__file__), 'audit_logs')
ADMIN_EMAIL = "fowler0613@gmail.com"
CAMP_EMAIL = "camppowerup2025@gmail.com"
CAMP_EMAIL_PASSWORD = os.environ.get('CAMP_EMAIL_PASSWORD', 'rtwpafmyjnjwylic')

def ensure_directories():
    """Create backup and audit directories if they don't exist."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(AUDIT_LOG_DIR, exist_ok=True)

def get_registration_data_hash(registration):
    """Generate a hash for registration data to detect changes."""
    # Remove timestamp and ID fields for comparison
    data_for_hash = {k: v for k, v in registration.items() 
                     if k not in ['id', 'timestamp', 'last_modified']}
    data_string = json.dumps(data_for_hash, sort_keys=True)
    return hashlib.md5(data_string.encode()).hexdigest()

def get_current_registrations():
    """Fetch all current registrations from the database."""
    registrations = []
    try:
        with get_db_connection('registration') as conn:
            cursor = conn.cursor()
            
            if DB_CONFIG['is_production']:  # PostgreSQL
                cursor.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                registrations = [dict(zip(columns, row)) for row in rows]
            else:  # SQLite
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM registrations ORDER BY timestamp DESC")
                registrations = [dict(row) for row in cursor.fetchall()]
                
        # Convert datetime objects to strings for JSON serialization
        for reg in registrations:
            for key, value in reg.items():
                if hasattr(value, 'isoformat'):  # datetime object
                    reg[key] = value.isoformat()
                    
        return registrations
    except Exception as e:
        print(f"Error fetching registrations: {e}")
        return []

def create_daily_backup():
    """Create a daily backup of all registrations."""
    today = datetime.now().strftime('%Y-%m-%d')
    backup_file = os.path.join(BACKUP_DIR, f"registrations_backup_{today}.json")
    
    registrations = get_current_registrations()
    
    backup_data = {
        'backup_date': datetime.now().isoformat(),
        'total_registrations': len(registrations),
        'database_type': 'PostgreSQL' if DB_CONFIG['is_production'] else 'SQLite',
        'registrations': registrations
    }
    
    try:
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"✅ Daily backup created: {backup_file}")
        print(f"📊 Total registrations backed up: {len(registrations)}")
        return backup_file, len(registrations)
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None, 0

def load_previous_backup():
    """Load the most recent previous backup for comparison."""
    yesterday = datetime.now() - timedelta(days=1)
    backup_file = os.path.join(BACKUP_DIR, f"registrations_backup_{yesterday.strftime('%Y-%m-%d')}.json")
    
    if os.path.exists(backup_file):
        try:
            with open(backup_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading previous backup: {e}")
    
    return None

def detect_changes():
    """Compare current registrations with previous backup to detect changes."""
    current_registrations = get_current_registrations()
    previous_backup = load_previous_backup()
    
    if not previous_backup:
        return {
            'new_registrations': current_registrations,
            'modified_registrations': [],
            'deleted_registrations': [],
            'summary': f"First backup - {len(current_registrations)} total registrations"
        }
    
    previous_registrations = previous_backup.get('registrations', [])
    
    # Create lookup dictionaries
    current_by_id = {reg['submission_id']: reg for reg in current_registrations}
    previous_by_id = {reg['submission_id']: reg for reg in previous_registrations}
    
    # Detect new registrations
    new_registrations = []
    for reg_id, reg in current_by_id.items():
        if reg_id not in previous_by_id:
            new_registrations.append(reg)
    
    # Detect deleted registrations
    deleted_registrations = []
    for reg_id, reg in previous_by_id.items():
        if reg_id not in current_by_id:
            deleted_registrations.append(reg)
    
    # Detect modified registrations
    modified_registrations = []
    for reg_id, current_reg in current_by_id.items():
        if reg_id in previous_by_id:
            previous_reg = previous_by_id[reg_id]
            current_hash = get_registration_data_hash(current_reg)
            previous_hash = get_registration_data_hash(previous_reg)
            
            if current_hash != previous_hash:
                modified_registrations.append({
                    'registration_id': reg_id,
                    'current_data': current_reg,
                    'previous_data': previous_reg
                })
    
    return {
        'new_registrations': new_registrations,
        'modified_registrations': modified_registrations,
        'deleted_registrations': deleted_registrations,
        'summary': f"New: {len(new_registrations)}, Modified: {len(modified_registrations)}, Deleted: {len(deleted_registrations)}"
    }

def create_audit_log(changes):
    """Create an audit log entry for detected changes."""
    today = datetime.now().strftime('%Y-%m-%d')
    audit_file = os.path.join(AUDIT_LOG_DIR, f"audit_log_{today}.json")
    
    audit_data = {
        'audit_date': datetime.now().isoformat(),
        'changes_detected': len(changes['new_registrations']) + len(changes['modified_registrations']) + len(changes['deleted_registrations']) > 0,
        'summary': changes['summary'],
        'new_registrations_count': len(changes['new_registrations']),
        'modified_registrations_count': len(changes['modified_registrations']),
        'deleted_registrations_count': len(changes['deleted_registrations']),
        'details': changes
    }
    
    try:
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f, indent=2, default=str)
        
        print(f"📋 Audit log created: {audit_file}")
        return audit_file
    except Exception as e:
        print(f"❌ Error creating audit log: {e}")
        return None

def send_daily_report(backup_file, audit_file, changes):
    """Send daily email report to admin."""
    try:
        # Create email content
        subject = f"Camp Power-Up Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        html_content = f"""
        <h2>🏕️ Camp Power-Up Daily Registration Report</h2>
        <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3>📊 Summary</h3>
            <p>{changes['summary']}</p>
        </div>
        
        <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3>✅ Backup Status</h3>
            <p>Daily backup completed successfully</p>
            <p><strong>Total registrations:</strong> {len(changes['new_registrations']) if 'new_registrations' in changes else 'N/A'}</p>
        </div>
        """
        
        if changes['new_registrations']:
            html_content += f"""
            <div style="background: #cce5ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>🆕 New Registrations ({len(changes['new_registrations'])})</h3>
                <ul>
            """
            for reg in changes['new_registrations']:
                html_content += f"<li>{reg['child_first_name']} {reg['child_last_name']} - {reg['parent_email']}</li>"
            html_content += "</ul></div>"
        
        if changes['modified_registrations']:
            html_content += f"""
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>✏️ Modified Registrations ({len(changes['modified_registrations'])})</h3>
                <ul>
            """
            for mod in changes['modified_registrations']:
                reg = mod['current_data']
                html_content += f"<li>{reg['child_first_name']} {reg['child_last_name']} - {mod['registration_id']}</li>"
            html_content += "</ul></div>"
        
        if changes['deleted_registrations']:
            html_content += f"""
            <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>🗑️ Deleted Registrations ({len(changes['deleted_registrations'])})</h3>
                <ul>
            """
            for reg in changes['deleted_registrations']:
                html_content += f"<li>{reg['child_first_name']} {reg['child_last_name']} - {reg['submission_id']}</li>"
            html_content += "</ul></div>"
        
        html_content += """
        <p style="margin-top: 30px; color: #666; font-size: 14px;">
            This is an automated daily report from your Camp Power-Up registration system.
        </p>
        """
        
        # Send email using SendGrid
        if not SENDGRID_AVAILABLE:
            print("⚠️ SendGrid not available. Skipping email report.")
            return False
            
        sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            print("⚠️ No SendGrid API key found. Skipping email report.")
            return False
            
        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        
        message = Mail(
            from_email=CAMP_EMAIL,
            to_emails=ADMIN_EMAIL,
            subject=subject,
            html_content=html_content
        )
        
        response = sg.send(message)
        print(f"📧 Daily report sent to {ADMIN_EMAIL} (Status: {response.status_code})")
        return True
        
    except Exception as e:
        print(f"❌ Error sending daily report: {e}")
        return False

def cleanup_old_backups(days_to_keep=30):
    """Remove backup files older than specified days."""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith('registrations_backup_') and filename.endswith('.json'):
            file_path = os.path.join(BACKUP_DIR, filename)
            file_date = datetime.fromtimestamp(os.path.getctime(file_path))
            
            if file_date < cutoff_date:
                os.remove(file_path)
                print(f"🗑️ Removed old backup: {filename}")

def main():
    """Main function to run the daily backup and audit process."""
    print(f"🏕️ Camp Power-Up Daily Backup & Audit - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Ensure directories exist
    ensure_directories()
    
    # Create daily backup
    backup_file, total_registrations = create_daily_backup()
    
    # Detect changes from previous day
    changes = detect_changes()
    print(f"📋 Changes detected: {changes['summary']}")
    
    # Create audit log
    audit_file = create_audit_log(changes)
    
    # Send daily report
    send_daily_report(backup_file, audit_file, changes)
    
    # Cleanup old backups
    cleanup_old_backups(30)
    
    print("=" * 60)
    print("✅ Daily backup and audit process completed!")

if __name__ == "__main__":
    main()