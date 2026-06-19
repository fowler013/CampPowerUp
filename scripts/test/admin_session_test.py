#!/usr/bin/env python3
"""
🔍 Admin Session Diagnostic Tool
Quick test to verify your admin login and session status
"""

import requests
import json

def test_admin_session():
    """Test admin session and authentication"""
    print("🔍 ADMIN SESSION DIAGNOSTIC")
    print("=" * 40)
    
    base_url = "http://localhost:5009"
    session = requests.Session()
    
    print("\n1️⃣ Testing login page access...")
    try:
        response = session.get(f"{base_url}/admin/login")
        if response.status_code == 200:
            print("✅ Login page accessible")
        else:
            print(f"❌ Login page issue: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    print("\n2️⃣ Testing admin authentication...")
    login_data = {
        'username': 'admin',
        'password': 'myNewPassword123!'
    }
    
    try:
        response = session.post(f"{base_url}/admin/login", data=login_data)
        if response.status_code in [200, 302]:
            print("✅ Authentication successful")
            
            # Check if we're redirected to dashboard
            if response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                print(f"   Redirected to: {redirect_url}")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    print("\n3️⃣ Testing protected routes after login...")
    
    # Test dashboard access
    try:
        response = session.get(f"{base_url}/admin/dashboard")
        if response.status_code == 200:
            print("✅ Dashboard accessible after login")
        else:
            print(f"❌ Dashboard access issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
    
    # Test communication page
    try:
        response = session.get(f"{base_url}/admin/communication")
        if response.status_code == 200:
            print("✅ Communication page accessible")
        else:
            print(f"❌ Communication page issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Communication error: {e}")
    
    # Test send email route
    try:
        response = session.get(f"{base_url}/admin/send-email")
        if response.status_code == 200:
            print("✅ Send Email page accessible")
        else:
            print(f"❌ Send Email page issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Send Email error: {e}")
    
    # Test send SMS route
    try:
        response = session.get(f"{base_url}/admin/send-sms")
        if response.status_code == 200:
            print("✅ Send SMS page accessible")
        else:
            print(f"❌ Send SMS page issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Send SMS error: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 RESULTS SUMMARY:")
    print("If all tests show ✅, your session should work properly.")
    print("If you see ❌, there may be a session or authentication issue.")
    print("\n📋 TROUBLESHOOTING TIPS:")
    print("1. Make sure you're logged in at: http://localhost:5009/admin/login")
    print("2. Use the same browser tab for all admin functions")
    print("3. Check that cookies are enabled in your browser")
    print("4. Try clearing browser cache and logging in again")
    print("5. Make sure all admin links are from the same domain (localhost:5009)")

if __name__ == "__main__":
    test_admin_session()
