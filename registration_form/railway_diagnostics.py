#!/usr/bin/env python3
"""
🚂 Railway PostgreSQL Diagnostic Tool
=====================================

This script performs comprehensive diagnostics on your Railway deployment
to identify why PostgreSQL isn't working and provide specific fix instructions.

Usage:
    python registration_form/railway_diagnostics.py
"""

import requests
import json
import sys
from typing import Dict, Any, List
import time

# Railway Configuration
RAILWAY_APP_URL = "https://camppowerup-registration.up.railway.app"
RAILWAY_DASHBOARD_URL = "https://railway.app/dashboard"

class RailwayDiagnostics:
    def __init__(self):
        self.issues_found = []
        self.fixes_needed = []
        
    def log_issue(self, issue: str, severity: str = "ERROR"):
        """Log diagnostic issues with severity levels"""
        self.issues_found.append({"issue": issue, "severity": severity})
        
    def log_fix(self, fix: str, priority: str = "HIGH"):
        """Log required fixes with priority levels"""
        self.fixes_needed.append({"fix": fix, "priority": priority})
        
    def print_header(self, title: str):
        """Print formatted section headers"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
        
    def check_railway_connectivity(self) -> bool:
        """Test basic connectivity to Railway deployment"""
        self.print_header("Railway Connectivity Check")
        
        try:
            response = requests.get(f"{RAILWAY_APP_URL}/", timeout=10)
            print(f"✅ Railway app is reachable: {response.status_code}")
            print(f"   URL: {RAILWAY_APP_URL}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot reach Railway app: {e}")
            self.log_issue("Railway app is not accessible", "CRITICAL")
            return False
            
    def check_database_endpoint(self) -> Dict[str, Any]:
        """Check the database test endpoint for detailed info"""
        self.print_header("Database Connection Analysis")
        
        try:
            response = requests.get(f"{RAILWAY_APP_URL}/test-db", timeout=10)
            if response.status_code == 200:
                db_info = response.json()
                print("📊 Database Status:")
                print(f"   Database Type: {db_info.get('database_type', 'Unknown')}")
                print(f"   Environment: {db_info.get('environment', 'Unknown')}")
                print(f"   Records Count: {db_info.get('registrations_count', 0)}")
                print(f"   Connection Success: {db_info.get('success', False)}")
                
                # Analyze database type
                if db_info.get('database_type') == 'SQLite':
                    self.log_issue("Railway is using SQLite instead of PostgreSQL", "CRITICAL")
                    self.log_fix("Add PostgreSQL service to Railway project", "CRITICAL")
                elif db_info.get('database_type') == 'PostgreSQL':
                    print("✅ PostgreSQL is correctly configured!")
                else:
                    self.log_issue("Unknown database type detected", "HIGH")
                    
                return db_info
            else:
                print(f"❌ Database endpoint failed: HTTP {response.status_code}")
                self.log_issue("Database test endpoint is not working", "HIGH")
                return {}
                
        except Exception as e:
            print(f"❌ Database endpoint error: {e}")
            self.log_issue(f"Database endpoint unreachable: {e}", "HIGH")
            return {}
            
    def check_environment_variables(self) -> Dict[str, Any]:
        """Analyze environment variables through app responses"""
        self.print_header("Environment Variables Analysis")
        
        try:
            # Try to get environment info from debug endpoint
            response = requests.get(f"{RAILWAY_APP_URL}/debug", timeout=5)
            if response.status_code == 200:
                debug_info = response.json()
                print("🔧 Environment Variables Detected:")
                for key, value in debug_info.items():
                    if 'DATABASE' in key.upper() or 'DB' in key.upper():
                        # Mask sensitive parts of DATABASE_URL
                        if 'password' in str(value).lower():
                            masked_value = str(value)[:20] + "****" + str(value)[-10:]
                        else:
                            masked_value = value
                        print(f"   {key}: {masked_value}")
                return debug_info
            else:
                print("⚠️  Debug endpoint not available (this is normal)")
                return {}
                
        except Exception:
            # Create a simple environment check
            print("🔍 Checking environment through database connection...")
            db_info = self.check_database_endpoint()
            
            if db_info.get('database_type') == 'SQLite':
                print("❌ DATABASE_URL environment variable likely missing")
                self.log_issue("DATABASE_URL not configured on Railway", "CRITICAL")
                
            return {}
            
    def test_form_submission(self) -> bool:
        """Test registration form submission"""
        self.print_header("Registration Form Test")
        
        test_data = {
            'child_first_name': 'Test',
            'child_last_name': 'Diagnostic',
            'child_age': '8',
            'parent_first_name': 'Railway',
            'parent_last_name': 'Test',
            'parent_email': 'test@railwaydiag.com',
            'parent_phone': '555-TEST-RWY',
            'emergency_contact_name': 'Emergency Test',
            'emergency_contact_phone': '555-EMERGENCY',
            'session_preference': 'morning',
            'is_returning_camper': 'off'
        }
        
        try:
            print("📝 Submitting test registration...")
            response = requests.post(
                f"{RAILWAY_APP_URL}/submit_registration",
                data=test_data,
                timeout=15
            )
            
            if response.status_code == 200:
                print("✅ Form submission successful!")
                return True
            elif response.status_code == 400:
                print("❌ Form submission failed with 400 error")
                self.log_issue("Registration form returns 400 errors", "CRITICAL")
                self.log_fix("Fix database connection to resolve 400 errors", "CRITICAL")
                return False
            else:
                print(f"⚠️  Form submission returned: HTTP {response.status_code}")
                self.log_issue(f"Form submission returned HTTP {response.status_code}", "HIGH")
                return False
                
        except Exception as e:
            print(f"❌ Form submission error: {e}")
            self.log_issue(f"Form submission failed: {e}", "HIGH")
            return False
            
    def check_admin_dashboard(self) -> bool:
        """Check admin dashboard accessibility"""
        self.print_header("Admin Dashboard Check")
        
        try:
            response = requests.get(f"{RAILWAY_APP_URL}/admin", timeout=10)
            if response.status_code == 200:
                print("✅ Admin dashboard is accessible")
                
                # Check if it contains registration data
                if 'No registrations' in response.text:
                    print("⚠️  Admin dashboard shows no registrations")
                    self.log_issue("Admin dashboard is empty (likely database issue)", "HIGH")
                else:
                    print("📊 Admin dashboard contains registration data")
                return True
            else:
                print(f"❌ Admin dashboard failed: HTTP {response.status_code}")
                self.log_issue("Admin dashboard is not accessible", "MEDIUM")
                return False
                
        except Exception as e:
            print(f"❌ Admin dashboard error: {e}")
            self.log_issue(f"Admin dashboard unreachable: {e}", "MEDIUM")
            return False
            
    def analyze_railway_setup(self):
        """Provide Railway-specific setup analysis"""
        self.print_header("Railway Setup Analysis")
        
        print("🔍 Checking Railway project configuration...")
        
        # Based on our findings, provide specific guidance
        db_info = self.check_database_endpoint()
        
        if db_info.get('database_type') == 'SQLite':
            print("\n❌ DIAGNOSIS: Railway is missing PostgreSQL service")
            print("\n📋 Required Railway Setup Steps:")
            print("   1. Go to Railway dashboard: https://railway.app/dashboard")
            print("   2. Select your Camp Power-Up project")
            print("   3. Look for these services:")
            print("      • App service (camppowerup-registration)")
            print("      • PostgreSQL service (MISSING - this is the problem!)")
            print("\n🔧 TO FIX:")
            print("   1. Click 'New' button in your Railway project")
            print("   2. Select 'Database' → 'Add PostgreSQL'")
            print("   3. Wait for PostgreSQL to deploy (1-2 minutes)")
            print("   4. PostgreSQL will automatically provide DATABASE_URL")
            print("   5. Your app will auto-redeploy with PostgreSQL")
            
        elif db_info.get('database_type') == 'PostgreSQL':
            print("✅ PostgreSQL is properly configured!")
            print("🎉 Your Railway setup is working correctly")
            
    def generate_dashboard_guide(self):
        """Generate specific Railway dashboard instructions"""
        self.print_header("Railway Dashboard Guide")
        
        print("🎯 EXACT STEPS FOR RAILWAY DASHBOARD:")
        print("\n1. Open Railway Dashboard:")
        print(f"   → Visit: {RAILWAY_DASHBOARD_URL}")
        print("   → Login to your Railway account")
        
        print("\n2. Find Your Project:")
        print("   → Look for 'camppowerup-registration' or similar")
        print("   → Click on the project name")
        
        print("\n3. Check Current Services:")
        print("   → You should see your app service")
        print("   → Look for a PostgreSQL database service")
        print("   → If NO PostgreSQL service exists, that's the problem!")
        
        print("\n4. Add PostgreSQL (if missing):")
        print("   → Click the 'New' button (usually top-right)")
        print("   → Select 'Database' from the dropdown")
        print("   → Choose 'Add PostgreSQL'")
        print("   → Railway will create the service automatically")
        
        print("\n5. Verify Connection:")
        print("   → After PostgreSQL deploys, click on it")
        print("   → You should see connection details")
        print("   → Your app should auto-redeploy")
        
        print("\n6. Test the Fix:")
        print("   → Run this script again: python registration_form/railway_diagnostics.py")
        print("   → Database type should show 'PostgreSQL'")
        
    def run_comprehensive_diagnosis(self):
        """Run all diagnostic checks"""
        print("🚂 Railway PostgreSQL Diagnostic Tool")
        print("=====================================")
        
        # Run all checks
        connectivity = self.check_railway_connectivity()
        if not connectivity:
            return
            
        db_info = self.check_database_endpoint()
        env_info = self.check_environment_variables()
        form_test = self.test_form_submission()
        admin_test = self.check_admin_dashboard()
        
        # Analyze setup
        self.analyze_railway_setup()
        
        # Generate dashboard guide
        self.generate_dashboard_guide()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print diagnostic summary with action items"""
        self.print_header("DIAGNOSTIC SUMMARY")
        
        if self.issues_found:
            print("❌ ISSUES FOUND:")
            for i, issue in enumerate(self.issues_found, 1):
                severity_icon = "🔥" if issue["severity"] == "CRITICAL" else "⚠️" if issue["severity"] == "HIGH" else "💡"
                print(f"   {i}. {severity_icon} [{issue['severity']}] {issue['issue']}")
        else:
            print("✅ No issues found! Your Railway setup looks good.")
            
        if self.fixes_needed:
            print("\n🔧 REQUIRED FIXES:")
            for i, fix in enumerate(self.fixes_needed, 1):
                priority_icon = "🔥" if fix["priority"] == "CRITICAL" else "⚠️" if fix["priority"] == "HIGH" else "💡"
                print(f"   {i}. {priority_icon} [{fix['priority']}] {fix['fix']}")
                
        print(f"\n📊 DIAGNOSIS COMPLETE")
        print(f"Issues Found: {len(self.issues_found)}")
        print(f"Fixes Needed: {len(self.fixes_needed)}")
        
        if any(issue["severity"] == "CRITICAL" for issue in self.issues_found):
            print("\n🚨 CRITICAL ISSUES DETECTED - Action Required!")
        elif self.issues_found:
            print("\n⚠️  Issues detected - Fixes recommended")
        else:
            print("\n🎉 All systems operational!")

def main():
    """Main diagnostic function"""
    diagnostics = RailwayDiagnostics()
    diagnostics.run_comprehensive_diagnosis()

if __name__ == "__main__":
    main()