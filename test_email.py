#!/usr/bin/env python3
"""
Test Email Configuration Script
Tests Gmail SMTP setup for Camp Power-Up communication system
"""

import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email Configuration (same as in communication/app.py)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'camppowerup2025@gmail.com',
    'password': 'dwyaqauvrkndpzys',
    'sender_name': 'Camp Power-Up Team'
}

def test_email_connection():
    """Test SMTP connection without sending email"""
    print("🔌 Testing SMTP connection...")
    
    try:
        # Create SMTP connection
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()  # Enable encryption
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.quit()
        
        print("✅ SMTP connection successful!")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check your email and app password.")
        return False
    except smtplib.SMTPConnectError:
        print("❌ Could not connect to SMTP server. Check your internet connection.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def send_test_email(recipient_email):
    """Send a test email to verify delivery"""
    print(f"📧 Sending test email to {recipient_email}...")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['email']}>"
        msg['To'] = recipient_email
        msg['Subject'] = "✅ Camp Power-Up Email Test - Success!"
        
        # Email body
        body = f"""
Hello!

🎉 Congratulations! Your Camp Power-Up email system is working perfectly.

✅ Gmail SMTP configuration successful
✅ Email delivery confirmed
✅ Ready for parent communications

Test Details:
- Sent from: {EMAIL_CONFIG['email']}
- Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- SMTP Server: {EMAIL_CONFIG['smtp_server']}
- Port: {EMAIL_CONFIG['smtp_port']}

Next steps:
1. Start sending parent communications
2. Set up email templates
3. Test bulk email functionality

Best regards,
The Camp Power-Up Communication System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['email'], recipient_email, text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print(f"📬 Check your inbox at {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Camp Power-Up Email Configuration Test")
    print("=" * 50)
    
    # Test 1: SMTP Connection
    if not test_email_connection():
        print("\n❌ Email configuration failed. Please check your credentials.")
        sys.exit(1)
    
    print()
    
    # Test 2: Send Test Email
    recipient = input("Enter your email address to receive a test email: ").strip()
    
    if not recipient:
        print("❌ No email address provided. Skipping email test.")
        return
    
    if '@' not in recipient:
        print("❌ Invalid email address format.")
        return
    
    print()
    if send_test_email(recipient):
        print("\n🎉 Email configuration test completed successfully!")
        print("✅ Your Camp Power-Up communication system is ready!")
    else:
        print("\n❌ Email test failed. Please check your configuration.")

if __name__ == "__main__":
    main()
