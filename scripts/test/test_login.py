#!/usr/bin/env python3
"""
Quick test script to verify login functionality
"""

import requests
import sys

def test_login():
    """Test the login functionality"""
    base_url = "http://127.0.0.1:5004"
    
    print("🔄 Testing login functionality...")
    
    # First, get the login page to get a CSRF token
    session = requests.Session()
    
    try:
        # Get login page
        login_page = session.get(f"{base_url}/admin/login")
        if login_page.status_code != 200:
            print(f"❌ Failed to load login page: {login_page.status_code}")
            return False
        
        # Extract CSRF token
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        
        if not csrf_token:
            print("❌ No CSRF token found in login page")
            return False
        
        csrf_value = csrf_token.get('value')
        print(f"✅ Got CSRF token: {csrf_value[:10]}...")
        
        # Attempt login
        login_data = {
            'username': 'admin',
            'password': 'Gkp0Ob4o_b-LKSUq_PJ_dg',
            'csrf_token': csrf_value
        }
        
        response = session.post(f"{base_url}/admin/login", data=login_data)
        
        if response.status_code == 302:  # Redirect means success
            print("✅ Login successful! (Got redirect)")
            return True
        elif response.status_code == 200:
            # Check if we're still on login page (failed login)
            if "login" in response.url.lower():
                print("❌ Login failed - still on login page")
                return False
            else:
                print("✅ Login successful! (Got page content)")
                return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  BeautifulSoup not available, install with: pip install beautifulsoup4")
        return False
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    if success:
        print("\n🎉 Login test PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Login test FAILED!")
        sys.exit(1)
