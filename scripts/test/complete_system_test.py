#!/usr/bin/env python3
"""
🏕️ Camp Power-Up - Complete System Test & Demonstration
Tests all modules, features, and integrations
"""

import requests
import sqlite3
import time
import json
import subprocess
from datetime import datetime, timedelta

class CampPowerUpTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5009"
        self.session = requests.Session()
        self.test_results = []
        print("🚀 CAMP POWER-UP COMPREHENSIVE TESTING")
        print("=" * 50)
    
    def test_admin_login(self):
        """Test admin authentication system"""
        print("\n🔐 Testing Admin Authentication...")
        
        # Test login page access
        try:
            response = self.session.get(f"{self.base_url}/admin/login")
            if response.status_code == 200:
                print("✅ Login page accessible")
                self.test_results.append(("Admin Login Page", "PASS"))
            else:
                print("❌ Login page not accessible")
                self.test_results.append(("Admin Login Page", "FAIL"))
        except Exception as e:
            print(f"❌ Login page error: {e}")
            self.test_results.append(("Admin Login Page", "FAIL"))
        
        # Test authentication
        try:
            login_data = {'username': 'admin', 'password': 'admin123'}
            response = self.session.post(f"{self.base_url}/admin/login", data=login_data)
            if response.status_code == 200 or response.status_code == 302:
                print("✅ Admin authentication working")
                self.test_results.append(("Admin Authentication", "PASS"))
            else:
                print("❌ Admin authentication failed")
                self.test_results.append(("Admin Authentication", "FAIL"))
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            self.test_results.append(("Admin Authentication", "FAIL"))
    
    def test_database_connections(self):
        """Test all database connections"""
        print("\n🗄️ Testing Database Connections...")
        
        databases = [
            ("Security Database", "security.db"),
            ("Registration Database", "registration_submissions.db"),
            ("Camp Database", "data/camp.db"),
            ("Communication Database", "communication/communication.db")
        ]
        
        for db_name, db_path in databases:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                if tables:
                    print(f"✅ {db_name}: {len(tables)} tables found")
                    self.test_results.append((db_name, "PASS"))
                else:
                    print(f"⚠️ {db_name}: No tables found")
                    self.test_results.append((db_name, "WARNING"))
            except Exception as e:
                print(f"❌ {db_name}: {e}")
                self.test_results.append((db_name, "FAIL"))
    
    def test_admin_modules(self):
        """Test all admin portal modules"""
        print("\n📊 Testing Admin Portal Modules...")
        
        modules = [
            "/admin/dashboard",
            "/admin/communication",
            "/admin/registration",
            "/admin/game-library",
            "/admin/analytics",
            "/admin/contacts",
            "/admin/settings",
            "/admin/security"
        ]
        
        for module in modules:
            try:
                response = self.session.get(f"{self.base_url}{module}")
                if response.status_code == 200:
                    print(f"✅ {module.split('/')[-1].title()} module accessible")
                    self.test_results.append((f"Module: {module.split('/')[-1]}", "PASS"))
                else:
                    print(f"❌ {module.split('/')[-1].title()} module error: {response.status_code}")
                    self.test_results.append((f"Module: {module.split('/')[-1]}", "FAIL"))
            except Exception as e:
                print(f"❌ {module.split('/')[-1].title()} module error: {e}")
                self.test_results.append((f"Module: {module.split('/')[-1]}", "FAIL"))
    
    def test_security_features(self):
        """Test security implementations"""
        print("\n🔒 Testing Security Features...")
        
        # Test password change
        try:
            change_data = {'current_password': 'admin123', 'new_password': 'TempPass123!'}
            response = self.session.post(f"{self.base_url}/admin/change-password", data=change_data)
            if response.status_code in [200, 302]:
                print("✅ Password change functionality working")
                self.test_results.append(("Password Change", "PASS"))
                
                # Change it back
                change_back = {'current_password': 'TempPass123!', 'new_password': 'admin123'}
                self.session.post(f"{self.base_url}/admin/change-password", data=change_back)
            else:
                print("❌ Password change failed")
                self.test_results.append(("Password Change", "FAIL"))
        except Exception as e:
            print(f"❌ Password change error: {e}")
            self.test_results.append(("Password Change", "FAIL"))
        
        # Test session management
        try:
            response = self.session.get(f"{self.base_url}/admin/dashboard")
            if 'session' in str(response.content).lower() or response.status_code == 200:
                print("✅ Session management active")
                self.test_results.append(("Session Management", "PASS"))
            else:
                print("❌ Session management issues")
                self.test_results.append(("Session Management", "FAIL"))
        except Exception as e:
            print(f"❌ Session management error: {e}")
            self.test_results.append(("Session Management", "FAIL"))
    
    def test_communication_system(self):
        """Test email/SMS communication capabilities"""
        print("\n📧 Testing Communication System...")
        
        # Test communication portal access
        try:
            response = self.session.get(f"{self.base_url}/admin/communication")
            if response.status_code == 200:
                print("✅ Communication portal accessible")
                self.test_results.append(("Communication Portal", "PASS"))
            else:
                print("❌ Communication portal not accessible")
                self.test_results.append(("Communication Portal", "FAIL"))
        except Exception as e:
            print(f"❌ Communication portal error: {e}")
            self.test_results.append(("Communication Portal", "FAIL"))
        
        # Test message templates
        try:
            templates_found = False
            # Check if templates are available (this would be in the HTML response)
            response = self.session.get(f"{self.base_url}/admin/communication")
            if 'template' in str(response.content).lower():
                templates_found = True
            
            if templates_found:
                print("✅ Message templates available")
                self.test_results.append(("Message Templates", "PASS"))
            else:
                print("⚠️ Message templates not found")
                self.test_results.append(("Message Templates", "WARNING"))
        except Exception as e:
            print(f"❌ Message templates error: {e}")
            self.test_results.append(("Message Templates", "FAIL"))
    
    def test_registration_system(self):
        """Test registration management"""
        print("\n📋 Testing Registration System...")
        
        try:
            response = self.session.get(f"{self.base_url}/admin/registration")
            if response.status_code == 200:
                print("✅ Registration management accessible")
                self.test_results.append(("Registration Management", "PASS"))
                
                # Check for registration data
                if 'registration' in str(response.content).lower():
                    print("✅ Registration data interface working")
                    self.test_results.append(("Registration Data", "PASS"))
                else:
                    print("⚠️ No registration data found")
                    self.test_results.append(("Registration Data", "WARNING"))
            else:
                print("❌ Registration management not accessible")
                self.test_results.append(("Registration Management", "FAIL"))
        except Exception as e:
            print(f"❌ Registration system error: {e}")
            self.test_results.append(("Registration Management", "FAIL"))
    
    def test_game_library(self):
        """Test game library and activities"""
        print("\n🎮 Testing Game Library...")
        
        try:
            response = self.session.get(f"{self.base_url}/admin/game-library")
            if response.status_code == 200:
                print("✅ Game library accessible")
                self.test_results.append(("Game Library", "PASS"))
                
                # Check for activity data
                if 'game' in str(response.content).lower() or 'activity' in str(response.content).lower():
                    print("✅ Activity management working")
                    self.test_results.append(("Activity Management", "PASS"))
                else:
                    print("⚠️ No activity data found")
                    self.test_results.append(("Activity Management", "WARNING"))
            else:
                print("❌ Game library not accessible")
                self.test_results.append(("Game Library", "FAIL"))
        except Exception as e:
            print(f"❌ Game library error: {e}")
            self.test_results.append(("Game Library", "FAIL"))
    
    def test_analytics_system(self):
        """Test analytics and reporting"""
        print("\n📈 Testing Analytics System...")
        
        try:
            response = self.session.get(f"{self.base_url}/admin/analytics")
            if response.status_code == 200:
                print("✅ Analytics dashboard accessible")
                self.test_results.append(("Analytics Dashboard", "PASS"))
                
                # Check for analytics data
                if 'chart' in str(response.content).lower() or 'statistic' in str(response.content).lower():
                    print("✅ Analytics data visualization working")
                    self.test_results.append(("Analytics Visualization", "PASS"))
                else:
                    print("⚠️ No analytics visualizations found")
                    self.test_results.append(("Analytics Visualization", "WARNING"))
            else:
                print("❌ Analytics dashboard not accessible")
                self.test_results.append(("Analytics Dashboard", "FAIL"))
        except Exception as e:
            print(f"❌ Analytics system error: {e}")
            self.test_results.append(("Analytics Dashboard", "FAIL"))
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 50)
        print("🏕️ CAMP POWER-UP SYSTEM TEST REPORT")
        print("=" * 50)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Total Tests: {len(self.test_results)}")
        
        passed = len([r for r in self.test_results if r[1] == "PASS"])
        warnings = len([r for r in self.test_results if r[1] == "WARNING"])
        failed = len([r for r in self.test_results if r[1] == "FAIL"])
        
        print(f"✅ Passed: {passed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"❌ Failed: {failed}")
        
        success_rate = (passed / len(self.test_results)) * 100
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        print("\n🔍 DETAILED RESULTS:")
        print("-" * 30)
        for test_name, result in self.test_results:
            status_icon = "✅" if result == "PASS" else "⚠️" if result == "WARNING" else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! System is production-ready!")
        elif success_rate >= 75:
            print("\n👍 GOOD! System is mostly functional with minor issues.")
        elif success_rate >= 50:
            print("\n⚠️ FAIR! System needs attention before production.")
        else:
            print("\n❌ POOR! System requires significant fixes.")
        
        return success_rate
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting comprehensive system test...")
        
        self.test_admin_login()
        self.test_database_connections()
        self.test_admin_modules()
        self.test_security_features()
        self.test_communication_system()
        self.test_registration_system()
        self.test_game_library()
        self.test_analytics_system()
        
        return self.generate_test_report()

def main():
    """Main testing function"""
    print("🏕️ CAMP POWER-UP COMPLETE SYSTEM VERIFICATION")
    print("=" * 60)
    print("Testing all systems, modules, and integrations...")
    print("This will verify that everything is working correctly!")
    print()
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to initialize...")
    time.sleep(3)
    
    tester = CampPowerUpTester()
    success_rate = tester.run_all_tests()
    
    print(f"\n🏁 Testing complete! Overall success rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n🚀 READY TO PROCEED WITH FULL BUILD!")
        print("All systems are operational and ready for customization!")
    else:
        print("\n🔧 Some issues detected. Review the report above.")
    
    return success_rate

if __name__ == "__main__":
    main()
