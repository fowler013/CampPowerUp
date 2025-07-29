#!/usr/bin/env python3
"""
Detailed Gmail SMTP Diagnostic Script
Helps troubleshoot Gmail authentication issues
"""

import smtplib
import socket
from email.mime.text import MIMEText

def test_connection_detailed():
    """Detailed SMTP connection test with more error information"""
    
    email = 'camppowerup2025@gmail.com'
    password = 'pxevfyjhsntsnwtp'
    
    print(f"📧 Testing Gmail SMTP for: {email}")
    print(f"🔑 App password: {password[:4]}{'*' * (len(password) - 4)}")
    print()
    
    try:
        print("1️⃣ Testing DNS resolution for smtp.gmail.com...")
        socket.gethostbyname('smtp.gmail.com')
        print("✅ DNS resolution successful")
        
        print("\n2️⃣ Connecting to SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        print("✅ SMTP connection established")
        
        print("\n3️⃣ Starting TLS encryption...")
        server.starttls()
        print("✅ TLS encryption started")
        
        print("\n4️⃣ Attempting authentication...")
        server.login(email, password)
        print("✅ Authentication successful!")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("\nPossible causes:")
        print("- App password is incorrect")
        print("- 2-factor authentication not enabled")
        print("- Account security settings blocking access")
        return False
        
    except socket.gaierror as e:
        print(f"❌ DNS Error: {e}")
        print("Check your internet connection")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection Error: {e}")
        print("SMTP server might be down or blocked")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def check_account_status():
    """Provide account troubleshooting steps"""
    print("\n🔍 Gmail Account Troubleshooting:")
    print("=" * 50)
    
    print("\n1. Verify 2-Factor Authentication:")
    print("   Go to: https://myaccount.google.com/security")
    print("   Make sure '2-Step Verification' is ON")
    
    print("\n2. Check App Passwords:")
    print("   Go to: https://myaccount.google.com/apppasswords")
    print("   Generate new password for 'Mail'")
    
    print("\n3. Account Security:")
    print("   Go to: https://myaccount.google.com/lesssecureapps")
    print("   Make sure 'Less secure app access' is OFF")
    
    print("\n4. Recent Security Activity:")
    print("   Go to: https://myaccount.google.com/notifications")
    print("   Check for any blocked sign-in attempts")

if __name__ == "__main__":
    print("🔍 Gmail SMTP Detailed Diagnostic")
    print("=" * 50)
    
    success = test_connection_detailed()
    
    if not success:
        check_account_status()
        
        print("\n💡 Quick Fixes to Try:")
        print("1. Generate a brand new app password")
        print("2. Wait 5-10 minutes after generating")
        print("3. Try signing into Gmail in a browser first")
        print("4. Check if the Gmail account is locked/suspended")
