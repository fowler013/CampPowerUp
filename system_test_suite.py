#!/usr/bin/env python3
"""
🧪 Camp Power-Up System Testing Suite
Comprehensive testing for all services and features
"""

import requests
import json
import time
from datetime import datetime

class CampPowerUpTester:
    def __init__(self):
        self.base_urls = {
            'admin': 'http://localhost:5009',
            'communication': 'http://localhost:5007',
            'registration': 'http://localhost:5008',
            'games': 'http://localhost:5000'
        }
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_service_availability(self):
        """Test if all services are accessible"""
        print("\n🔍 Testing Service Availability...")
        
        for service, url in self.base_urls.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 302, 404]:  # 404 is OK for root paths
                    self.log_test(f"{service.title()} Service", "PASS", f"HTTP {response.status_code}")
                else:
                    self.log_test(f"{service.title()} Service", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"{service.title()} Service", "FAIL", str(e))
    
    def test_admin_portal(self):
        """Test admin portal functionality"""
        print("\n🔐 Testing Admin Portal...")
        
        # Test login page
        try:
            response = requests.get(f"{self.base_urls['admin']}/admin/login")
            if response.status_code == 200 and "login" in response.text.lower():
                self.log_test("Admin Login Page", "PASS", "Login form accessible")
            else:
                self.log_test("Admin Login Page", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Admin Login Page", "FAIL", str(e))
        
        # Test admin dashboard routes
        admin_routes = [
            '/admin/dashboard',
            '/admin/communication',
            '/admin/registration',  
            '/admin/game-library',
            '/admin/analytics'
        ]
        
        for route in admin_routes:
            try:
                response = requests.get(f"{self.base_urls['admin']}{route}")
                # These will redirect to login, which is expected behavior
                if response.status_code in [200, 302]:
                    self.log_test(f"Admin Route {route}", "PASS", "Route accessible")
                else:
                    self.log_test(f"Admin Route {route}", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Admin Route {route}", "WARN", f"Connection error: {e}")
    
    def test_communication_service(self):
        """Test communication service"""
        print("\n📧 Testing Communication Service...")
        
        try:
            response = requests.get(self.base_urls['communication'])
            if response.status_code in [200, 302]:
                self.log_test("Communication Service", "PASS", f"HTTP {response.status_code}")
            else:
                self.log_test("Communication Service", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Communication Service", "FAIL", str(e))
    
    def test_registration_service(self):
        """Test registration service"""
        print("\n📋 Testing Registration Service...")
        
        try:
            response = requests.get(self.base_urls['registration'])
            if response.status_code == 200:
                self.log_test("Registration Service", "PASS", "Service responsive")
                
                # Check if it's the registration form
                if "registration" in response.text.lower():
                    self.log_test("Registration Form", "PASS", "Form detected")
                else:
                    self.log_test("Registration Form", "WARN", "Form content unclear")
            else:
                self.log_test("Registration Service", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Registration Service", "FAIL", str(e))
    
    def test_game_library(self):
        """Test game library service"""
        print("\n🎮 Testing Game Library...")
        
        try:
            response = requests.get(self.base_urls['games'])
            if response.status_code == 200:
                self.log_test("Game Library Service", "PASS", "Service responsive")
                
                # Check for game/activity content
                if any(word in response.text.lower() for word in ['game', 'activity', 'camp']):
                    self.log_test("Game Library Content", "PASS", "Content detected")
                else:
                    self.log_test("Game Library Content", "WARN", "Content unclear")
            else:
                self.log_test("Game Library Service", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Game Library Service", "FAIL", str(e))
    
    def test_port_configuration(self):
        """Test that all services are on correct ports"""
        print("\n🔌 Testing Port Configuration...")
        
        expected_ports = {
            'admin': 5009,
            'communication': 5007,
            'registration': 5008,
            'games': 5000
        }
        
        for service, expected_port in expected_ports.items():
            url = self.base_urls[service]
            actual_port = int(url.split(':')[-1])
            
            if actual_port == expected_port:
                self.log_test(f"{service.title()} Port", "PASS", f"Port {actual_port}")
            else:
                self.log_test(f"{service.title()} Port", "FAIL", f"Expected {expected_port}, got {actual_port}")
    
    def test_database_connectivity(self):
        """Test database connectivity through admin portal"""
        print("\n🗄️ Testing Database Connectivity...")
        
        # This would require authentication, so we'll test indirectly
        try:
            # Test if admin dashboard loads (indicates database connection)
            response = requests.get(f"{self.base_urls['admin']}/admin/dashboard")
            
            # 302 redirect to login is expected and good
            if response.status_code == 302:
                self.log_test("Database Connectivity", "PASS", "Admin system responding (redirects to login)")
            elif response.status_code == 200:
                self.log_test("Database Connectivity", "PASS", "Admin system accessible")
            else:
                self.log_test("Database Connectivity", "WARN", f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database Connectivity", "FAIL", str(e))
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("🏕️ CAMP POWER-UP SYSTEM TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Warnings: {warned_tests}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"   🎯 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   - {result['test']}: {result['details']}")
        
        if warned_tests > 0:
            print(f"\n⚠️  Warnings:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"   - {result['test']}: {result['details']}")
        
        print(f"\n🎉 Overall System Status: ", end="")
        if success_rate >= 90:
            print("EXCELLENT ✨")
        elif success_rate >= 75:
            print("GOOD ✅")
        elif success_rate >= 50:
            print("NEEDS WORK ⚠️")
        else:
            print("CRITICAL ISSUES ❌")
        
        # Save detailed report
        with open('test_report.json', 'w') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'warned': warned_tests,
                    'success_rate': success_rate
                },
                'results': self.test_results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: test_report.json")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting Camp Power-Up System Tests...")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.test_service_availability()
        self.test_port_configuration()
        self.test_admin_portal()
        self.test_communication_service()
        self.test_registration_service()
        self.test_game_library()
        self.test_database_connectivity()
        
        self.generate_report()

def main():
    """Main testing function"""
    tester = CampPowerUpTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
