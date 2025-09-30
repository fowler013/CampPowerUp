#!/usr/bin/env python3
"""
Simple SendGrid Email Fix for Railway
"""

import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Email configuration
EMAIL_CONFIG = {
    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
    'email_address': os.environ.get('CAMP_EMAIL', 'camppowerup2025@gmail.com'),
    'email_password': os.environ.get('CAMP_EMAIL_PASSWORD', ''),
    'from_name': 'Camp Power-Up Registration',
    'sendgrid_api_key': os.environ.get('SENDGRID_API_KEY', ''),
    'use_sendgrid': bool(os.environ.get('SENDGRID_API_KEY', ''))
}

def send_email_via_sendgrid(to_email, subject, html_content):
    """Send email using SendGrid API (Railway-compatible)."""
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
            "email": EMAIL_CONFIG['email_address'],
            "name": EMAIL_CONFIG['from_name']
        },
        "content": [{
            "type": "text/html", 
            "value": html_content
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 202:
            print(f"✅ SendGrid email sent successfully to {to_email}")
            return True
        else:
            print(f"❌ SendGrid error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ SendGrid request failed: {e}")
        return False

def create_simple_email_html(registration_data):
    """Create simple HTML email content."""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #28a745;">✅ Registration Confirmed!</h1>
        <p>Thank you for registering for Camp Power-Up 2025!</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h2 style="color: #28a745;">Confirmation ID: {registration_data['submission_id']}</h2>
            <p><strong>Camper:</strong> {registration_data['child_first_name']} {registration_data['child_last_name']}</p>
            <p><strong>Age:</strong> {registration_data['child_age']} years old</p>
        </div>
        
        <div style="background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107;">
            <h3>📝 Next Steps:</h3>
            <ol>
                <li><strong>Payment:</strong> Send $180 via Zelle to <strong>fowler0613@gmail.com</strong></li>
                <li><strong>Include:</strong> "{registration_data['child_first_name']} {registration_data['child_last_name']}" in payment memo</li>
                <li><strong>Confirmation:</strong> Payment confirmation within 24 hours</li>
            </ol>
        </div>
        
        <p>Questions? Contact us at <strong>fowler0613@gmail.com</strong></p>
        <p><em>Camp Power-Up 2025 | Gaming & Technology Camp</em></p>
    </div>
    """

def send_confirmation_email_fixed(registration_data):
    """Fixed email sending with SendGrid support."""
    try:
        subject = f"Registration Confirmed - Camp Power-Up 2025 - {registration_data['child_first_name']} {registration_data['child_last_name']}"
        html_content = create_simple_email_html(registration_data)
        
        # Try SendGrid first (works on Railway)
        if EMAIL_CONFIG['use_sendgrid'] and EMAIL_CONFIG['sendgrid_api_key']:
            print("🚀 Sending via SendGrid...")
            return send_email_via_sendgrid(
                registration_data['parent_email'],
                subject,
                html_content
            )
        
        # Fallback to SMTP (local development)
        elif EMAIL_CONFIG['email_password']:
            print("📧 Sending via SMTP...")
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email_address']}>"
            msg['To'] = registration_data['parent_email']
            
            # Simple text version
            text_content = f"""
            Registration Confirmed - Camp Power-Up 2025
            
            Confirmation ID: {registration_data['submission_id']}
            Camper: {registration_data['child_first_name']} {registration_data['child_last_name']}
            
            Next Steps:
            1. Send $180 via Zelle to fowler0613@gmail.com  
            2. Include "{registration_data['child_first_name']} {registration_data['child_last_name']}" in memo
            
            Questions? Contact fowler0613@gmail.com
            """
            
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['email_address'], EMAIL_CONFIG['email_password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ SMTP email sent to {registration_data['parent_email']}")
            return True
        else:
            print("⚠️ No email configuration available (need SENDGRID_API_KEY or CAMP_EMAIL_PASSWORD)")
            return False
            
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

if __name__ == "__main__":
    # Test configuration
    print("Email Configuration:")
    print(f"- Use SendGrid: {EMAIL_CONFIG['use_sendgrid']}")
    print(f"- Email address: {EMAIL_CONFIG['email_address']}")
    print(f"- Has password: {'Yes' if EMAIL_CONFIG['email_password'] else 'No'}")
    print(f"- Has SendGrid key: {'Yes' if EMAIL_CONFIG['sendgrid_api_key'] else 'No'}")