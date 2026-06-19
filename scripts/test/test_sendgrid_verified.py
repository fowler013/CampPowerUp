#!/usr/bin/env python3
"""
Test SendGrid with verified sender - Run AFTER email verification
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

def test_sendgrid_verified():
    """Test SendGrid with verified sender email"""
    
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('SENDGRID_FROM_EMAIL')
    from_name = os.getenv('SENDGRID_FROM_NAME')
    
    if not api_key:
        print("❌ SENDGRID_API_KEY not found in environment")
        return False
        
    print(f"🧪 Testing SendGrid with:")
    print(f"   From: {from_name} <{from_email}>")
    print(f"   API Key: {api_key[:20]}...")
    
    # SendGrid API endpoint
    url = "https://api.sendgrid.com/v3/mail/send"
    
    # Email data
    email_data = {
        "personalizations": [
            {
                "to": [{"email": "fowler0613@gmail.com", "name": "Tevin Fowler"}],
                "subject": "✅ SendGrid Verification Test - Camp Power-Up"
            }
        ],
        "from": {
            "email": from_email,
            "name": from_name
        },
        "reply_to": {
            "email": from_email,
            "name": from_name
        },
        "content": [
            {
                "type": "text/html",
                "value": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
                    <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2c3e50; margin-bottom: 20px;">🎉 SendGrid is Working!</h2>
                        <p style="color: #34495e; font-size: 16px; line-height: 1.5;">
                            Great news! Your SendGrid email system is now properly configured with verified sender identity.
                        </p>
                        <div style="background-color: #e8f5e8; padding: 15px; border-left: 4px solid #27ae60; margin: 20px 0;">
                            <strong style="color: #27ae60;">✅ Email verification successful</strong><br>
                            <span style="color: #2c3e50;">Your Camp Power-Up registration confirmations will now be delivered!</span>
                        </div>
                        <p style="color: #7f8c8d; font-size: 14px; margin-top: 30px;">
                            This is a test email sent from your verified SendGrid configuration.
                        </p>
                    </div>
                </div>
                """
            }
        ]
    }
    
    # Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print("📤 Sending test email...")
        response = requests.post(url, headers=headers, json=email_data, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 202:
            print("✅ SUCCESS! Email sent successfully")
            print("📧 Check your inbox at fowler0613@gmail.com")
            return True
        else:
            print("❌ FAILED! SendGrid API Error:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 403:
                print("\n💡 SOLUTION: You need to verify your email address in SendGrid!")
                print("   1. Go to: https://app.sendgrid.com/settings/sender_auth")
                print("   2. Click 'Verify a Single Sender'")
                print("   3. Add: fowler0613@gmail.com")
                print("   4. Check your email and click verification link")
                print("   5. Run this test again")
            
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 SendGrid Verified Sender Test")
    print("=" * 40)
    
    success = test_sendgrid_verified()
    
    if success:
        print("\n🎉 All systems ready!")
        print("   → Email confirmations will work on Railway")
        print("   → Don't forget to set Railway environment variables")
    else:
        print("\n❌ Email verification needed")
        print("   → Complete SendGrid verification first")