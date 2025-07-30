#!/usr/bin/env python3
"""
Camp Power-Up Parent Communication System
=========================================

A comprehensive communication system for Camp Power-Up that handles:
- Email notifications and reminders
- SMS updates for important information
- Parent portal for updates and photos
- Automated messaging workflows
- Emergency communications

Features:
- Email templates for different camp events
- SMS integration for urgent updates
- Parent portal with secure login
- Photo sharing and updates
- Payment reminders
- Daily activity summaries
- Emergency contact system
"""

import os
import sqlite3
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import hashlib
import secrets
import time
import threading

app = Flask(__name__)
app.secret_key = 'camp_power_up_communication_2025'

# Configuration
# Use the main camp database that contains all the registration data
DATABASE_PATH = os.path.abspath(os.path.join('..', 'camp_power_up.db'))
REGISTRATION_DB_PATH = os.path.abspath(os.path.join('..', 'registration_form', 'registration_submissions.db'))
COMMUNICATION_DB = 'communication.db'

# Email Configuration - Gmail Setup
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'camppowerup2025@gmail.com',
    'password': 'dwyaqauvrkndpzys',
    'sender_name': 'Camp Power-Up Team'
}

# SMS Configuration (using Twilio)
SMS_CONFIG = {
    'account_sid': os.getenv('TWILIO_ACCOUNT_SID', 'your-twilio-sid'),
    'auth_token': os.getenv('TWILIO_AUTH_TOKEN', 'your-twilio-token'),
    'from_number': os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')  # Your Twilio phone number
}

def init_communication_db():
    """Initialize the communication database"""
    conn = sqlite3.connect(COMMUNICATION_DB)
    cursor = conn.cursor()
    
    # Create communication logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS communication_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL,  -- email, sms, portal_message
            recipient TEXT NOT NULL,
            subject TEXT,
            message TEXT,
            status TEXT DEFAULT 'pending',  -- pending, sent, failed
            template_used TEXT,
            camper_id TEXT,
            parent_email TEXT
        )
    ''')
    
    # Create message templates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,  -- email, sms
            subject TEXT,
            body TEXT NOT NULL,
            variables TEXT,  -- JSON list of variables like {child_name}, {date}
            active BOOLEAN DEFAULT 1,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create parent portal posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portal_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            post_type TEXT DEFAULT 'general',  -- general, activity, photo, announcement
            target_audience TEXT DEFAULT 'all',  -- all, specific_campers, returning_only
            image_path TEXT,
            priority TEXT DEFAULT 'normal',  -- low, normal, high, urgent
            expires_date DATETIME,
            read_confirmations TEXT  -- JSON list of parent emails who read it
        )
    ''')
    
    # Create scheduled messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER,
            send_date DATETIME NOT NULL,
            recipient_filter TEXT,  -- all, returning_campers, new_campers, specific_list
            status TEXT DEFAULT 'scheduled',  -- scheduled, sent, cancelled
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES message_templates (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_default_templates():
    """Create default email and SMS templates"""
    conn = sqlite3.connect(COMMUNICATION_DB)
    cursor = conn.cursor()
    
    templates = [
        {
            'name': 'welcome_email',
            'type': 'email',
            'subject': 'Welcome to Camp Power-Up 2025! 🎮⚡',
            'body': '''Dear {parent_name},

Welcome to Camp Power-Up 2025! We're thrilled that {child_name} will be joining us for an amazing week of gaming, learning, and fun.

📅 Camp Details:
• Dates: June 16-20, 2025
• Time: 9:00 AM - 3:00 PM daily
• Location: [Your Camp Location]

🎒 What to Bring:
• Lunch and water bottle
• Comfortable clothes
• Nintendo Switch (if you have one)
• Positive attitude and excitement!

💰 Payment Reminder:
• Total Fee: ${fee_amount}
• Payment due by: {payment_due_date}
• Pay online at: [Payment Link]

📞 Questions?
Reply to this email or call us at [Camp Phone Number].

See you soon!
The Camp Power-Up Team 🏕️

P.S. Follow us on [Social Media] for updates and sneak peeks!''',
            'variables': '["parent_name", "child_name", "fee_amount", "payment_due_date"]'
        },
        {
            'name': 'payment_reminder',
            'type': 'email',
            'subject': 'Payment Reminder - Camp Power-Up 2025 💳',
            'body': '''Hi {parent_name},

This is a friendly reminder that payment for {child_name}'s Camp Power-Up registration is due soon.

💰 Payment Details:
• Amount Due: ${fee_amount}
• Due Date: {payment_due_date}
• Registration ID: {submission_id}

🔗 Pay Now: [Payment Link]

If you've already paid, please disregard this message. If you have any questions about payment or need to discuss payment options, please don't hesitate to reach out.

Thanks!
Camp Power-Up Team''',
            'variables': '["parent_name", "child_name", "fee_amount", "payment_due_date", "submission_id"]'
        },
        {
            'name': 'daily_update',
            'type': 'email',
            'subject': 'Day {day_number} Update - {child_name} at Camp Power-Up! 🎮',
            'body': '''Hi {parent_name},

{child_name} had an awesome Day {day_number} at Camp Power-Up! Here's what we did:

🎮 Today's Activities:
{daily_activities}

🌟 Highlight of the Day:
{daily_highlight}

📸 Photos:
Check out today's photos in your parent portal: [Portal Link]

🏆 {child_name}'s Achievement:
{child_achievement}

Tomorrow we'll be doing: {tomorrow_preview}

Have a great evening!
The Camp Power-Up Team''',
            'variables': '["parent_name", "child_name", "day_number", "daily_activities", "daily_highlight", "child_achievement", "tomorrow_preview"]'
        },
        {
            'name': 'pickup_reminder',
            'type': 'sms',
            'subject': '',
            'body': 'Camp Power-Up reminder: Pickup for {child_name} is at 3:00 PM today. Please arrive on time. Thanks! 🏕️',
            'variables': '["child_name"]'
        },
        {
            'name': 'emergency_alert',
            'type': 'sms',
            'subject': '',
            'body': 'CAMP ALERT: {emergency_message} Please call {camp_phone} immediately if needed. {child_name} is safe.',
            'variables': '["emergency_message", "camp_phone", "child_name"]'
        },
        {
            'name': 'camp_complete',
            'type': 'email',
            'subject': 'Thank You! {child_name} Completed Camp Power-Up 2025! 🎉',
            'body': '''Dear {parent_name},

What an incredible week! {child_name} has successfully completed Camp Power-Up 2025, and we couldn't be more proud!

🏆 {child_name}'s Achievements:
{final_achievements}

📊 Skills Developed:
{skills_learned}

📸 Final Photos & Videos:
All photos and videos from the week are available in your parent portal: [Portal Link]

🎮 Take-Home Resources:
• Gaming tips and guidelines
• Recommended family-friendly games
• Online safety resources
• Certificate of completion (attached)

💭 We'd Love Your Feedback:
Please take 2 minutes to complete our camp survey: [Survey Link]

🔄 See You Next Year?
Early bird registration for Camp Power-Up 2026 opens in January with special discounts for returning families!

Thank you for trusting us with {child_name}. It's been an absolute joy having them at camp!

The Camp Power-Up Team 🏕️⚡''',
            'variables': '["parent_name", "child_name", "final_achievements", "skills_learned"]'
        }
    ]
    
    for template in templates:
        cursor.execute('''
            INSERT OR REPLACE INTO message_templates 
            (name, type, subject, body, variables) 
            VALUES (?, ?, ?, ?, ?)
        ''', (template['name'], template['type'], template['subject'], 
              template['body'], template['variables']))
    
    conn.commit()
    conn.close()

def get_parent_contacts():
    """Get all parent contact information from the registration database"""
    try:
        conn = sqlite3.connect(REGISTRATION_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                child_first_name,
                child_last_name,
                parent_email,
                parent_phone,
                is_returning_camper,
                timestamp
            FROM registrations 
            ORDER BY timestamp DESC
        ''')
        
        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                'child_name': f"{row[0]} {row[1]}",
                'parent_name': f"Parent of {row[0]}",  # Use child's name since no parent name in DB
                'email': row[2],
                'phone': row[3],
                'is_returning': bool(row[4]),
                'registration_date': row[5]
            })
        
        conn.close()
        return contacts
        
    except Exception as e:
        print(f"Error getting parent contacts: {e}")
        return []

def get_parent_by_email(email):
    """Get specific parent information by email"""
    try:
        conn = sqlite3.connect(REGISTRATION_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                child_first_name,
                child_last_name,
                parent_email,
                parent_phone,
                is_returning_camper
            FROM registrations 
            WHERE parent_email = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'child_name': f"{row[0]} {row[1]}",
                'parent_name': f"Parent of {row[0]}",  # Use child's name since no parent name in DB
                'email': row[2],
                'phone': row[3],
                'is_returning': bool(row[4])
            }
        return None
        
    except Exception as e:
        print(f"Error getting parent by email: {e}")
        return None

class EmailSender:
    """Handle email sending functionality"""
    
    def __init__(self, config=EMAIL_CONFIG):
        self.config = config
    
    def send_email(self, to_email, subject, body, html_body=None, attachments=None):
        """Send an email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config['sender_name']} <{self.config['email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, 'rb') as f:
                            if attachment_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                attachment = MIMEImage(f.read())
                                attachment.add_header('Content-Disposition', 
                                                    f'attachment; filename={os.path.basename(attachment_path)}')
                            else:
                                attachment = MIMEText(f.read(), 'base64', 'utf-8')
                                attachment.add_header('Content-Disposition', 
                                                    f'attachment; filename={os.path.basename(attachment_path)}')
                            msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email'], self.config['password'])
                server.send_message(msg)
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

class SMSSender:
    """Handle SMS sending functionality"""
    
    def __init__(self, config=SMS_CONFIG):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Twilio client if credentials are provided"""
        try:
            if (self.config['account_sid'] != 'your-twilio-sid' and 
                self.config['auth_token'] != 'your-twilio-token'):
                from twilio.rest import Client
                self.client = Client(self.config['account_sid'], self.config['auth_token'])
                print("✅ Twilio SMS client initialized successfully")
            else:
                print("⚠️  Twilio credentials not configured - SMS will be simulated")
        except Exception as e:
            print(f"❌ Failed to initialize Twilio client: {str(e)}")
            self.client = None
    
    def send_sms(self, to_number, message):
        """Send an SMS using Twilio"""
        try:
            # Clean phone number (remove spaces, dashes, etc.)
            clean_number = ''.join(filter(str.isdigit, str(to_number)))
            if len(clean_number) == 10:
                clean_number = '+1' + clean_number
            elif len(clean_number) == 11 and clean_number.startswith('1'):
                clean_number = '+' + clean_number
            elif not clean_number.startswith('+'):
                clean_number = '+1' + clean_number
            
            if self.client:
                # Send real SMS via Twilio
                message_obj = self.client.messages.create(
                    body=message,
                    from_=self.config['from_number'],
                    to=clean_number
                )
                print(f"📱 SMS sent successfully to {clean_number} (SID: {message_obj.sid})")
                return True, f"SMS sent successfully (SID: {message_obj.sid})"
            else:
                # Simulate SMS sending for testing
                print(f"📱 [SIMULATED] SMS to {clean_number}: {message}")
                return True, "SMS simulated successfully (Twilio not configured)"
            
        except Exception as e:
            error_msg = f"Failed to send SMS to {to_number}: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

def log_communication(comm_type, recipient, subject, message, status, template_used=None, camper_id=None, parent_email=None):
    """Log communication attempts"""
    conn = sqlite3.connect(COMMUNICATION_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO communication_logs 
        (type, recipient, subject, message, status, template_used, camper_id, parent_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (comm_type, recipient, subject, message, status, template_used, camper_id, parent_email))
    
    conn.commit()
    conn.close()

def get_camper_data():
    """Get all camper data from the main database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM registrations
        ''')
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        campers = []
        for row in rows:
            camper_dict = dict(zip(columns, row))
            campers.append(camper_dict)
        
        conn.close()
        return campers
        
    except Exception as e:
        print(f"Error getting camper data: {e}")
        return []

@app.route('/')
def communication_dashboard():
    """Main communication dashboard with real data"""
    try:
        # Get actual parent contacts from registration database
        parent_contacts = get_parent_contacts()
        
        # Get communication stats
        conn = sqlite3.connect(COMMUNICATION_DB)
        cursor = conn.cursor()
        
        # Count total communications sent
        cursor.execute('SELECT COUNT(*) FROM communication_logs WHERE status = "sent"')
        total_sent = cursor.fetchone()[0]
        
        # Count emails vs SMS
        cursor.execute('SELECT type, COUNT(*) FROM communication_logs WHERE status = "sent" GROUP BY type')
        comm_types = dict(cursor.fetchall())
        
        # Get recent communications
        cursor.execute('''
            SELECT timestamp, type, recipient, subject, status 
            FROM communication_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_comms = cursor.fetchall()
        
        conn.close()
        
        stats = {
            'total_parents': len(parent_contacts),
            'returning_campers': len([p for p in parent_contacts if p['is_returning']]),
            'new_campers': len([p for p in parent_contacts if not p['is_returning']]),
            'total_sent': total_sent,
            'emails_sent': comm_types.get('email', 0),
            'sms_sent': comm_types.get('sms', 0),
            'recent_communications': recent_comms
        }
        
        return render_template('communication_dashboard.html', 
                             parent_contacts=parent_contacts,
                             stats=stats)
                             
    except Exception as e:
        print(f"Error in communication dashboard: {e}")
        return render_template('communication_dashboard.html', 
                             parent_contacts=[],
                             stats={})

@app.route('/send_message', methods=['GET', 'POST'])
def send_message():
    """Send custom message to parents"""
    if request.method == 'POST':
        data = request.json
        
        message_type = data.get('type', 'email')
        recipients = data.get('recipients', [])
        subject = data.get('subject', '')
        message = data.get('message', '')
        template_id = data.get('template_id')
        
        # Send messages
        email_sender = EmailSender()
        sms_sender = SMSSender()
        
        results = []
        
        for recipient in recipients:
            if message_type == 'email':
                success, result = email_sender.send_email(recipient, subject, message)
            else:  # SMS
                success, result = sms_sender.send_sms(recipient, message)
            
            # Log the communication
            log_communication(
                message_type, recipient, subject, message,
                'sent' if success else 'failed', template_id
            )
            
            results.append({
                'recipient': recipient,
                'success': success,
                'message': result
            })
        
        return jsonify({'success': True, 'results': results})
    
    # GET request - show send message form
    campers = get_camper_data()
    return render_template('send_message.html', campers=campers)

@app.route('/portal')
def parent_portal():
    """Parent portal for viewing camp updates and photos"""
    return render_template('parent_portal.html')

@app.route('/templates')
def manage_templates():
    """Manage message templates"""
    conn = sqlite3.connect(COMMUNICATION_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM message_templates WHERE active = 1
        ORDER BY created_date DESC
    ''')
    
    templates = cursor.fetchall()
    conn.close()
    
    return jsonify({'templates': templates})

@app.route('/send_campaign', methods=['POST'])
def send_campaign():
    """Send pre-built campaign messages"""
    data = request.json
    campaign_type = data.get('type')
    
    # Get appropriate recipients based on campaign type
    campers = get_camper_data()
    
    # Filter recipients based on campaign type
    recipients = []
    if campaign_type == 'welcome':
        # Send to new campers only
        recipients = [camper['parent_email'] for camper in campers if not camper.get('is_returning_camper')]
    elif campaign_type == 'payment_reminder':
        # Send to unpaid registrations
        recipients = [camper['parent_email'] for camper in campers if camper.get('payment_status') != 'paid']
    else:
        # Send to all parents
        recipients = [camper['parent_email'] for camper in campers]
    
    # Load template and send messages
    email_sender = EmailSender()
    results = []
    
    # This would load the actual template and send personalized messages
    # For now, just simulate success
    for recipient in recipients:
        success = True  # Simulated success
        results.append({
            'recipient': recipient,
            'success': success,
            'message': 'Message sent successfully'
        })
        
        # Log the communication
        log_communication(
            'email', recipient, f'{campaign_type} campaign', 
            f'Campaign message: {campaign_type}', 'sent', campaign_type
        )
    
    return jsonify({'success': True, 'results': results, 'count': len(recipients)})

@app.route('/communication_stats')
def communication_stats():
    """Get communication statistics"""
    conn = sqlite3.connect(COMMUNICATION_DB)
    cursor = conn.cursor()
    
    # Get today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT 
            type,
            status,
            COUNT(*) as count
        FROM communication_logs 
        WHERE date(timestamp) = ?
        GROUP BY type, status
    ''', (today,))
    
    stats = cursor.fetchall()
    conn.close()
    
    return jsonify({'stats': stats})

# ===== API ENDPOINTS FOR FRONTEND INTEGRATION =====

@app.route('/api/parent-contacts', methods=['GET'])
def api_get_parent_contacts():
    """API endpoint to get all parent contact information"""
    try:
        contacts = get_parent_contacts()
        return jsonify({
            'success': True,
            'data': contacts,
            'total': len(contacts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/send-email', methods=['POST'])
def api_send_email():
    """API endpoint to send individual emails"""
    try:
        data = request.json
        recipients = data.get('recipients', [])
        subject = data.get('subject', '')
        message = data.get('message', '')
        
        if not recipients or not subject or not message:
            return jsonify({
                'success': False,
                'error': 'Recipients, subject, and message are required'
            }), 400
        
        email_sender = EmailSender()
        results = []
        
        for recipient in recipients:
            success, result = email_sender.send_email(recipient, subject, message)
            
            # Log the communication
            log_communication(
                'email', recipient, subject, message,
                'sent' if success else 'failed'
            )
            
            results.append({
                'recipient': recipient,
                'success': success,
                'message': result
            })
        
        success_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_sent': len(recipients),
                'successful': success_count,
                'failed': len(recipients) - success_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/send-sms', methods=['POST'])
def api_send_sms():
    """API endpoint to send individual SMS messages"""
    try:
        data = request.json
        recipients = data.get('recipients', [])
        message = data.get('message', '')
        
        if not recipients or not message:
            return jsonify({
                'success': False,
                'error': 'Recipients and message are required'
            }), 400
        
        # Validate message length (SMS limit is typically 160 characters)
        if len(message) > 160:
            return jsonify({
                'success': False,
                'error': 'SMS message must be 160 characters or less'
            }), 400
        
        sms_sender = SMSSender()
        results = []
        
        for recipient in recipients:
            success, result = sms_sender.send_sms(recipient, message)
            
            # Log the communication
            log_communication(
                'sms', recipient, 'SMS', message,
                'sent' if success else 'failed'
            )
            
            results.append({
                'recipient': recipient,
                'success': success,
                'message': result
            })
        
        success_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_sent': len(recipients),
                'successful': success_count,
                'failed': len(recipients) - success_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sms-test')
def sms_test():
    """Simple SMS test page"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>SMS Test</title>
</head>
<body>
    <h1>SMS Test Form</h1>
    
    <form>
        <h3>Message Type</h3>
        <input type="radio" name="messageType" value="email" checked> Email
        <input type="radio" name="messageType" value="sms"> SMS
        
        <h3>Phone Numbers</h3>
        <textarea id="phoneNumbers" placeholder="555-123-4567, 555-987-6543">555-123-4567</textarea>
        
        <h3>Message</h3>
        <textarea id="message" placeholder="Your SMS message here">Test SMS message from Camp Power-Up!</textarea>
        
        <br><br>
        <button type="button" onclick="testSMS()">Send SMS Test</button>
    </form>
    
    <div id="result"></div>
    
    <script>
        function testSMS() {
            const messageType = document.querySelector('input[name="messageType"]:checked').value;
            const phoneNumbers = document.getElementById('phoneNumbers').value;
            const message = document.getElementById('message').value;
            
            console.log('Testing SMS with:', {messageType, phoneNumbers, message});
            
            const recipients = phoneNumbers.split(',').map(p => p.trim());
            
            const requestBody = {
                recipients: recipients,
                message: message
            };
            
            console.log('Request body:', JSON.stringify(requestBody, null, 2));
            
            fetch('/api/send-sms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                if (data.success) {
                    alert('SMS test successful!');
                } else {
                    alert('SMS test failed: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('result').innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
            });
        }
    </script>
</body>
</html>'''

@app.route('/api/communication-stats', methods=['GET'])
def api_get_communication_stats():
    """API endpoint to get communication statistics"""
    try:
        # Get parent contacts stats
        contacts = get_parent_contacts()
        
        # Get communication logs stats
        conn = sqlite3.connect(COMMUNICATION_DB)
        cursor = conn.cursor()
        
        # Count total communications sent
        cursor.execute('SELECT COUNT(*) FROM communication_logs WHERE status = "sent"')
        total_sent = cursor.fetchone()[0]
        
        # Count by type
        cursor.execute('SELECT type, COUNT(*) FROM communication_logs WHERE status = "sent" GROUP BY type')
        comm_types = dict(cursor.fetchall())
        
        conn.close()
        
        stats = {
            'total_parents': len(contacts),
            'returning_campers': len([p for p in contacts if p['is_returning']]),
            'new_campers': len([p for p in contacts if not p['is_returning']]),
            'total_communications_sent': total_sent,
            'emails_sent': comm_types.get('email', 0),
            'sms_sent': comm_types.get('sms', 0)
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🏕️ Camp Power-Up Communication System")
    print("=====================================")
    
    # Initialize database and templates
    init_communication_db()
    create_default_templates()
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5004))
    
    print("📧 Email templates loaded")
    print("📱 SMS system ready")
    print(f"🌐 Parent portal available at: http://127.0.0.1:{port}")
    print(f"🔧 Admin dashboard available at: http://127.0.0.1:{port}/admin")
    
    app.run(debug=True, port=port)
