#!/usr/bin/env python3
"""
Email Service for Camp Power-Up
Handles all email sending functionality with multiple providers
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import json

class EmailService:
    def __init__(self):
        """Initialize email service with configuration"""
        self.config = self._load_email_config()
        
    def _load_email_config(self):
        """Load email configuration from environment variables"""
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'sender_email': os.getenv('SENDER_EMAIL', ''),
            'sender_password': os.getenv('SENDER_PASSWORD', ''),
            'sender_name': os.getenv('SENDER_NAME', 'Camp Power-Up'),
            'use_tls': os.getenv('USE_TLS', 'true').lower() == 'true'
        }
    
    def send_bulk_email(self, recipients, subject, message, sender_name=None):
        """
        Send bulk email to multiple recipients
        
        Args:
            recipients (list): List of email addresses
            subject (str): Email subject
            message (str): Email message (can be HTML)
            sender_name (str): Optional sender name override
            
        Returns:
            dict: Results with success/failure counts and details
        """
        if not self.config['sender_email'] or not self.config['sender_password']:
            return {
                'success': False,
                'error': 'Email configuration not set. Please configure SMTP settings.',
                'sent': 0,
                'failed': 0,
                'details': []
            }
        
        results = {
            'success': True,
            'sent': 0,
            'failed': 0,
            'details': [],
            'timestamp': datetime.now().isoformat()
        }
        
        sender_display = sender_name or self.config['sender_name']
        
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            
            if self.config['use_tls']:
                server.starttls()  # Enable security
            
            server.login(self.config['sender_email'], self.config['sender_password'])
            
            for recipient in recipients:
                try:
                    # Create message
                    msg = MIMEMultipart()
                    msg['From'] = f"{sender_display} <{self.config['sender_email']}>"
                    msg['To'] = recipient
                    msg['Subject'] = subject
                    
                    # Add body to email
                    if '<html>' in message.lower() or '<p>' in message.lower():
                        msg.attach(MIMEText(message, 'html'))
                    else:
                        msg.attach(MIMEText(message, 'plain'))
                    
                    # Send email
                    server.send_message(msg)
                    results['sent'] += 1
                    results['details'].append({
                        'recipient': recipient,
                        'status': 'sent',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    results['failed'] += 1
                    results['details'].append({
                        'recipient': recipient,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            server.quit()
            
        except Exception as e:
            results['success'] = False
            results['error'] = f"SMTP Connection Error: {str(e)}"
            results['failed'] = len(recipients)
            
        return results
    
    def send_single_email(self, recipient, subject, message, sender_name=None):
        """Send a single email"""
        result = self.send_bulk_email([recipient], subject, message, sender_name)
        return result
    
    def test_connection(self):
        """Test email server connection"""
        if not self.config['sender_email'] or not self.config['sender_password']:
            return {
                'success': False,
                'error': 'Email configuration not set'
            }
        
        try:
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            
            if self.config['use_tls']:
                server.starttls()
            
            server.login(self.config['sender_email'], self.config['sender_password'])
            server.quit()
            
            return {
                'success': True,
                'message': 'Email connection successful',
                'server': self.config['smtp_server'],
                'port': self.config['smtp_port']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'server': self.config['smtp_server'],
                'port': self.config['smtp_port']
            }
    
    def get_email_templates(self):
        """Get predefined email templates"""
        return {
            'welcome': {
                'subject': 'Welcome to Camp Power-Up!',
                'message': '''
                <html>
                <body>
                    <h2>🏕️ Welcome to Camp Power-Up!</h2>
                    <p>Dear Parent/Guardian,</p>
                    <p>We're excited to welcome your child to Camp Power-Up! This email confirms your registration.</p>
                    
                    <h3>📋 Next Steps:</h3>
                    <ul>
                        <li>Check your camp session details</li>
                        <li>Review our daily schedule</li>
                        <li>Prepare any required items</li>
                    </ul>
                    
                    <p>If you have any questions, please don't hesitate to contact us.</p>
                    
                    <p>Best regards,<br>
                    The Camp Power-Up Team</p>
                </body>
                </html>
                '''
            },
            'daily_update': {
                'subject': 'Daily Camp Update - [DATE]',
                'message': '''
                <html>
                <body>
                    <h2>🌟 Daily Camp Update</h2>
                    <p>Dear Parents,</p>
                    <p>Here's what happened at camp today:</p>
                    
                    <h3>🎮 Today's Activities:</h3>
                    <ul>
                        <li>[Activity 1]</li>
                        <li>[Activity 2]</li>
                        <li>[Activity 3]</li>
                    </ul>
                    
                    <h3>📸 Photos:</h3>
                    <p>Photos from today will be uploaded to our parent portal shortly.</p>
                    
                    <h3>🏕️ Tomorrow's Plan:</h3>
                    <p>[Tomorrow's activities preview]</p>
                    
                    <p>Have a great evening!<br>
                    The Camp Power-Up Team</p>
                </body>
                </html>
                '''
            },
            'pickup_reminder': {
                'subject': 'Camp Pickup Reminder',
                'message': '''
                <html>
                <body>
                    <h2>🚗 Pickup Reminder</h2>
                    <p>Dear Parent/Guardian,</p>
                    <p>This is a friendly reminder about pickup time for your camper.</p>
                    
                    <h3>⏰ Pickup Details:</h3>
                    <ul>
                        <li><strong>Time:</strong> [PICKUP_TIME]</li>
                        <li><strong>Location:</strong> Camp Power-Up Main Entrance</li>
                        <li><strong>Please bring:</strong> Photo ID</li>
                    </ul>
                    
                    <p>If you'll be late or need to arrange alternate pickup, please call us immediately.</p>
                    
                    <p>Thank you!<br>
                    The Camp Power-Up Team</p>
                </body>
                </html>
                '''
            },
            'emergency_alert': {
                'subject': '🚨 URGENT: Camp Emergency Alert',
                'message': '''
                <html>
                <body>
                    <h2>🚨 Emergency Alert</h2>
                    <p>Dear Parents,</p>
                    <p><strong>This is an urgent message regarding camp operations.</strong></p>
                    
                    <h3>📢 Alert Details:</h3>
                    <p>[EMERGENCY_DETAILS]</p>
                    
                    <h3>🎯 Action Required:</h3>
                    <p>[ACTION_REQUIRED]</p>
                    
                    <p>We will keep you updated as the situation develops.</p>
                    
                    <p>Best regards,<br>
                    The Camp Power-Up Team</p>
                </body>
                </html>
                '''
            }
        }

# Global email service instance
email_service = EmailService()

def send_camp_email(recipients, subject, message, template=None):
    """
    Convenience function for sending camp emails
    
    Args:
        recipients (list): Email addresses
        subject (str): Email subject
        message (str): Email message
        template (str): Optional template name
        
    Returns:
        dict: Send results
    """
    if template:
        templates = email_service.get_email_templates()
        if template in templates:
            template_data = templates[template]
            subject = template_data['subject']
            message = template_data['message']
    
    return email_service.send_bulk_email(recipients, subject, message)

if __name__ == '__main__':
    # Test email service
    service = EmailService()
    result = service.test_connection()
    print("📧 Email Service Test:")
    print(f"   Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    if not result['success']:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Server: {result['server']}:{result['port']}")
