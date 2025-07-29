#!/usr/bin/env python3
"""
SMS Diagnostic Script for Camp Power-Up Communication System
===========================================================

This script helps test and diagnose SMS functionality using Twilio.
Run this script to verify your SMS configuration is working correctly.
"""

import os
import sys
import time

# Add the communication directory to the path
sys.path.insert(0, os.path.abspath('communication'))

try:
    from app import SMSSender, SMS_CONFIG
    print("✅ Successfully imported SMS modules")
except ImportError as e:
    print(f"❌ Failed to import SMS modules: {e}")
    print("Make sure you're running this from the CampPowerUp root directory")
    sys.exit(1)

def test_sms_config():
    """Test SMS configuration"""
    print("\n📋 Testing SMS Configuration...")
    print(f"Account SID: {'✅ Set' if SMS_CONFIG['account_sid'] != 'your-twilio-sid' else '❌ Not configured'}")
    print(f"Auth Token: {'✅ Set' if SMS_CONFIG['auth_token'] != 'your-twilio-token' else '❌ Not configured'}")
    print(f"From Number: {SMS_CONFIG['from_number']}")
    
    if SMS_CONFIG['account_sid'] == 'your-twilio-sid':
        print("\n⚠️  Twilio credentials not configured - SMS will be simulated")
        print("To configure real SMS:")
        print("1. Set environment variables:")
        print("   export TWILIO_ACCOUNT_SID='your_sid'")
        print("   export TWILIO_AUTH_TOKEN='your_token'")
        print("   export TWILIO_PHONE_NUMBER='your_number'")
        print("2. Or edit SMS_CONFIG in communication/app.py")
        return False
    
    return True

def test_sms_sender():
    """Test SMS sender initialization"""
    print("\n🔧 Testing SMS Sender Initialization...")
    
    try:
        sms_sender = SMSSender()
        print("✅ SMS Sender initialized successfully")
        return sms_sender
    except Exception as e:
        print(f"❌ Failed to initialize SMS Sender: {e}")
        return None

def test_phone_number_formatting():
    """Test phone number formatting"""
    print("\n📱 Testing Phone Number Formatting...")
    
    test_numbers = [
        "1234567890",           # 10 digits
        "11234567890",          # 11 digits starting with 1
        "+1234567890",          # With country code
        "(555) 123-4567",       # Formatted
        "555-123-4567",         # Dashed
        "+1-555-123-4567",      # Full format
    ]
    
    sms_sender = SMSSender()
    
    for number in test_numbers:
        # Test the number formatting logic (simulated)
        clean_number = ''.join(filter(str.isdigit, str(number)))
        if len(clean_number) == 10:
            clean_number = '+1' + clean_number
        elif len(clean_number) == 11 and clean_number.startswith('1'):
            clean_number = '+' + clean_number
        elif not clean_number.startswith('+'):
            clean_number = '+1' + clean_number
        
        print(f"  {number:15} → {clean_number}")

def send_test_sms():
    """Send a test SMS"""
    print("\n🧪 SMS Sending Test...")
    
    # Get test phone number from user
    test_number = input("Enter a phone number to test SMS (or press Enter to skip): ").strip()
    
    if not test_number:
        print("⏭️  Skipping SMS test")
        return
    
    sms_sender = SMSSender()
    test_message = "🏕️ Test SMS from Camp Power-Up! Your SMS system is working correctly. 🎉"
    
    print(f"Sending test SMS to {test_number}...")
    print(f"Message: {test_message}")
    
    success, result = sms_sender.send_sms(test_number, test_message)
    
    if success:
        print(f"✅ {result}")
    else:
        print(f"❌ {result}")

def main():
    """Main diagnostic function"""
    print("🏕️ Camp Power-Up SMS Diagnostic Tool")
    print("=" * 40)
    
    # Test configuration
    config_ok = test_sms_config()
    
    # Test SMS sender
    sms_sender = test_sms_sender()
    
    if not sms_sender:
        print("\n❌ Cannot proceed with tests - SMS Sender failed to initialize")
        return
    
    # Test phone number formatting
    test_phone_number_formatting()
    
    # Offer to send test SMS
    if config_ok:
        print("\n⚠️  WARNING: The following test will send a REAL SMS and may incur charges!")
        response = input("Do you want to send a test SMS? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            send_test_sms()
        else:
            print("⏭️  Skipping real SMS test")
    else:
        print("\n📱 Simulating SMS test (no real SMS will be sent)...")
        test_message = "🏕️ Test SMS from Camp Power-Up! Your SMS system is working correctly. 🎉"
        success, result = sms_sender.send_sms("+15551234567", test_message)
        print(f"Result: {result}")
    
    print("\n✨ SMS Diagnostic Complete!")
    print("\nNext steps:")
    print("1. Configure Twilio credentials if not already done")
    print("2. Test the web interface at http://localhost:5000/send_message")
    print("3. Try sending SMS to parents from the communication dashboard")

if __name__ == "__main__":
    main()
