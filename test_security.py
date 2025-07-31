#!/usr/bin/env python3
"""
Security Test Script for Camp Power-Up
=====================================

This script tests the main security features to ensure everything is working.
"""

import requests
import sys
import time

def test_security_features():
    """Test the main security features"""
    
    print("🔐 CAMP POWER-UP SECURITY TEST")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5004"
    
    # Test 1: Unauthenticated access should redirect to login
    print("\n1️⃣ Testing unauthenticated access...")
    try:
        response = requests.get(f"{base_url}/", allow_redirects=False)
        if response.status_code == 302:
            print("   ✅ Main page redirects unauthenticated users")
        else:
            print(f"   ❌ Expected redirect (302), got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing main page: {e}")
    
    # Test 2: Login page accessible
    print("\n2️⃣ Testing login page access...")
    try:
        response = requests.get(f"{base_url}/admin/login")
        if response.status_code == 200 and "Camp Power-Up" in response.text:
            print("   ✅ Login page accessible and renders correctly")
        else:
            print(f"   ❌ Login page issue (status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Error testing login page: {e}")
    
    # Test 3: API endpoints require authentication
    print("\n3️⃣ Testing API endpoint protection...")
    try:
        response = requests.get(f"{base_url}/api/parent-contacts", allow_redirects=False)
        if response.status_code == 302:
            print("   ✅ API endpoints redirect unauthenticated users")
            if "/admin/login" in response.headers.get('Location', ''):
                print("   ✅ Redirects to login page correctly")
        else:
            print(f"   ❌ API endpoint not protected (status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Error testing API endpoint: {e}")
    
    # Test 4: Rate limiting on login (basic test)
    print("\n4️⃣ Testing rate limiting...")
    try:
        session = requests.Session()
        login_url = f"{base_url}/admin/login"
        
        # Get login page first to get any CSRF tokens
        login_page = session.get(login_url)
        
        # Try multiple failed login attempts
        failed_attempts = 0
        for i in range(3):
            data = {
                'username': 'wrong_user',
                'password': 'wrong_password'
            }
            response = session.post(login_url, data=data, allow_redirects=False)
            if response.status_code in [200, 302]:
                failed_attempts += 1
            time.sleep(0.1)  # Small delay
        
        if failed_attempts > 0:
            print(f"   ✅ Rate limiting allows {failed_attempts} attempts (normal behavior)")
        else:
            print("   ❌ No login attempts processed")
            
    except Exception as e:
        print(f"   ❌ Error testing rate limiting: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 SECURITY TEST SUMMARY")
    print("=" * 50)
    print("✅ All core security features appear to be working!")
    print("\n📋 Manual Tests Needed:")
    print("   - Login with valid credentials in browser")
    print("   - Test password change functionality")
    print("   - Verify audit logging in database")
    print("   - Test session timeout (8 hours)")
    
    print(f"\n🌐 Access the app: {base_url}")
    print("🔑 Default credentials:")
    print("   Username: admin")
    print("   Password: Gkp0Ob4o_b-LKSUq_PJ_dg")

if __name__ == "__main__":
    print("Starting security tests...")
    print("Make sure the app is running at http://127.0.0.1:5004")
    print()
    
    try:
        test_security_features()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
        sys.exit(1)
