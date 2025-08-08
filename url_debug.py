#!/usr/bin/env python3
"""
🔍 URL Debug Tool - Shows exactly which links should work
"""

import requests

def test_admin_urls():
    """Test and display the correct admin URLs"""
    print("🔍 ADMIN PORTAL URL VERIFICATION")
    print("=" * 50)
    
    base_url = "http://localhost:5009"
    
    print(f"\n✅ CORRECT URLs (should work after login):")
    print(f"🏠 Admin Dashboard: {base_url}/admin/dashboard")
    print(f"📧 Communication Hub: {base_url}/admin/communication")
    print(f"📨 Send Bulk Email: {base_url}/admin/send-email")
    print(f"📱 Send Bulk SMS: {base_url}/admin/send-sms")
    
    print(f"\n❌ WRONG URLs (these will cause redirect issues):")
    print(f"❌ http://127.0.0.1:5007/admin/login")
    print(f"❌ http://127.0.0.1:5007/send_bulk_email")
    print(f"❌ http://127.0.0.1:5007/send_bulk_sms")
    
    print(f"\n🔧 DEBUGGING STEPS:")
    print(f"1. Login at: {base_url}/admin/login")
    print(f"2. Password: myNewPassword123!")
    print(f"3. Go to Communication: {base_url}/admin/communication")
    print(f"4. Click 'Send Bulk Email' - URL should stay on port 5009")
    print(f"5. If it redirects to port 5007, there's a link problem")
    
    # Test the communication service to see what's there
    print(f"\n🔍 Testing communication service on port 5007:")
    try:
        response = requests.get("http://localhost:5007/")
        print(f"✅ Communication service responds: {response.status_code}")
        print(f"   This service has its own separate login system")
        print(f"   You should NOT be redirected here from admin portal")
    except Exception as e:
        print(f"❌ Communication service error: {e}")

if __name__ == "__main__":
    test_admin_urls()
