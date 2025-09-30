#!/usr/bin/env python3
"""
🔗 DATABASE_URL Configuration Troubleshooter
============================================

This script validates DATABASE_URL format, tests connection parameters,
and diagnoses common PostgreSQL connection issues for Railway deployments.

Usage:
    python registration_form/database_url_troubleshooter.py [DATABASE_URL]
"""

import os
import sys
import re
from urllib.parse import urlparse
from typing import Dict, Any, Optional, Tuple

class DatabaseURLTroubleshooter:
    def __init__(self):
        self.issues = []
        self.recommendations = []
        
    def log_issue(self, issue: str, severity: str = "ERROR"):
        self.issues.append({"issue": issue, "severity": severity})
        
    def log_recommendation(self, rec: str, priority: str = "HIGH"):
        self.recommendations.append({"recommendation": rec, "priority": priority})
        
    def validate_database_url_format(self, db_url: str) -> Dict[str, Any]:
        """Validate DATABASE_URL format and extract components"""
        print("🔍 Analyzing DATABASE_URL Format...")
        
        if not db_url:
            self.log_issue("DATABASE_URL is empty or None", "CRITICAL")
            return {}
            
        try:
            parsed = urlparse(db_url)
            
            components = {
                'scheme': parsed.scheme,
                'username': parsed.username,
                'password': parsed.password,
                'hostname': parsed.hostname,
                'port': parsed.port,
                'database': parsed.path.lstrip('/') if parsed.path else None
            }
            
            print(f"   Scheme: {components['scheme']}")
            print(f"   Host: {components['hostname']}")
            print(f"   Port: {components['port']}")
            print(f"   Database: {components['database']}")
            print(f"   Username: {components['username']}")
            print(f"   Password: {'****' if components['password'] else 'None'}")
            
            # Validate scheme
            if components['scheme'] not in ['postgresql', 'postgres']:
                self.log_issue(f"Invalid scheme '{components['scheme']}' - should be 'postgresql' or 'postgres'", "CRITICAL")
            else:
                print("   ✅ Scheme is valid")
                
            # Validate required components
            required_fields = ['hostname', 'username', 'password', 'database']
            for field in required_fields:
                if not components[field]:
                    self.log_issue(f"Missing required field: {field}", "CRITICAL")
                else:
                    print(f"   ✅ {field} is present")
                    
            # Validate port
            if components['port']:
                if not (1 <= components['port'] <= 65535):
                    self.log_issue(f"Invalid port {components['port']}", "HIGH")
                else:
                    print(f"   ✅ Port {components['port']} is valid")
            else:
                print("   ℹ️  Using default PostgreSQL port (5432)")
                
            return components
            
        except Exception as e:
            self.log_issue(f"Failed to parse DATABASE_URL: {e}", "CRITICAL")
            return {}
            
    def check_railway_url_patterns(self, db_url: str) -> bool:
        """Check if URL matches Railway PostgreSQL patterns"""
        print("\n🚂 Railway URL Pattern Analysis...")
        
        railway_patterns = [
            r'.*\.railway\.app',
            r'.*\.up\.railway\.app', 
            r'.*postgres.*railway.*',
            r'.*railway.*postgres.*'
        ]
        
        is_railway = any(re.search(pattern, db_url, re.IGNORECASE) for pattern in railway_patterns)
        
        if is_railway:
            print("   ✅ URL appears to be from Railway PostgreSQL service")
            return True
        else:
            print("   ⚠️  URL doesn't match Railway patterns")
            self.log_issue("DATABASE_URL might not be from Railway PostgreSQL service", "MEDIUM")
            return False
            
    def validate_connection_string_syntax(self, db_url: str) -> bool:
        """Validate PostgreSQL connection string syntax"""
        print("\n📝 Connection String Syntax Check...")
        
        # Basic PostgreSQL URL format
        postgres_pattern = r'^postgresql://[^:]+:[^@]+@[^:/]+:\d+/\w+$'
        
        if re.match(postgres_pattern, db_url):
            print("   ✅ Connection string syntax is valid")
            return True
        else:
            print("   ❌ Connection string syntax is invalid")
            self.log_issue("DATABASE_URL has invalid syntax", "CRITICAL")
            
            # Provide specific guidance
            print("\n   📋 Expected format:")
            print("   postgresql://username:password@hostname:port/database")
            print("\n   🔧 Common issues:")
            print("   - Missing postgresql:// prefix")
            print("   - Special characters in password not URL-encoded")
            print("   - Missing port number")
            print("   - Missing database name")
            
            return False
            
    def check_common_railway_issues(self, components: Dict[str, Any]):
        """Check for common Railway PostgreSQL configuration issues"""
        print("\n🔧 Railway Configuration Issues Check...")
        
        if not components:
            return
            
        # Check for Railway-specific issues
        issues_found = False
        
        # Issue 1: Generic localhost/127.0.0.1
        if components.get('hostname') in ['localhost', '127.0.0.1']:
            self.log_issue("Using localhost - Railway PostgreSQL should have external hostname", "CRITICAL")
            self.log_recommendation("Verify PostgreSQL service is properly deployed on Railway", "CRITICAL")
            issues_found = True
            
        # Issue 2: Default PostgreSQL port but no external access
        if components.get('port') == 5432:
            print("   ℹ️  Using standard PostgreSQL port 5432")
            
        # Issue 3: Missing or default database name
        if components.get('database') in ['postgres', 'postgresql', '']:
            print("   ⚠️  Using default/generic database name")
            self.log_recommendation("Verify database name matches Railway PostgreSQL service", "MEDIUM")
            
        # Issue 4: Weak or default credentials
        if components.get('username') == 'postgres' and components.get('password') == 'postgres':
            self.log_issue("Using default PostgreSQL credentials", "MEDIUM")
            
        # Issue 5: Railway environment variable format
        if not any(railway_word in str(components.get('hostname', '')) for railway_word in ['railway', 'postgres']):
            print("   ⚠️  Hostname doesn't contain 'railway' or 'postgres'")
            
        if not issues_found:
            print("   ✅ No common Railway issues detected")
            
    def simulate_connection_test(self, db_url: str) -> bool:
        """Simulate connection test (without actually connecting)"""
        print("\n🔌 Connection Simulation...")
        
        try:
            # Try to import psycopg2 to check if it's available
            import psycopg2
            print("   ✅ psycopg2 is available for PostgreSQL connections")
            
            # Simulate connection parameters
            parsed = urlparse(db_url)
            
            print(f"   🔗 Would attempt connection to:")
            print(f"      Host: {parsed.hostname}")
            print(f"      Port: {parsed.port or 5432}")
            print(f"      Database: {parsed.path.lstrip('/')}")
            print(f"      User: {parsed.username}")
            
            # Check for potential connection blockers
            if not parsed.hostname:
                self.log_issue("No hostname specified - connection will fail", "CRITICAL")
                return False
                
            if not parsed.username or not parsed.password:
                self.log_issue("Missing credentials - connection will fail", "CRITICAL")
                return False
                
            print("   ✅ Connection parameters look valid")
            return True
            
        except ImportError:
            print("   ❌ psycopg2 not installed")
            self.log_issue("psycopg2 not installed - PostgreSQL connections will fail", "CRITICAL")
            self.log_recommendation("Install psycopg2-binary: pip install psycopg2-binary", "CRITICAL")
            return False
            
    def check_environment_setup(self):
        """Check environment setup for DATABASE_URL"""
        print("\n🌍 Environment Setup Check...")
        
        # Check if DATABASE_URL is set in environment
        env_db_url = os.environ.get('DATABASE_URL')
        
        if env_db_url:
            print(f"   ✅ DATABASE_URL found in environment")
            print(f"      Length: {len(env_db_url)} characters")
            print(f"      Starts with: {env_db_url[:20]}...")
            return env_db_url
        else:
            print("   ❌ DATABASE_URL not found in environment variables")
            self.log_issue("DATABASE_URL environment variable not set", "CRITICAL")
            
            print("\n   💡 Possible reasons:")
            print("   - Railway PostgreSQL service not added")
            print("   - Environment variables not properly configured")  
            print("   - App service not connected to PostgreSQL service")
            
            self.log_recommendation("Add PostgreSQL service to Railway project", "CRITICAL")
            self.log_recommendation("Verify DATABASE_URL appears in app environment variables", "CRITICAL")
            
            return None
            
    def generate_fix_instructions(self, db_url: Optional[str] = None):
        """Generate specific fix instructions based on findings"""
        print("\n" + "="*60)
        print("🔧 TROUBLESHOOTING RESULTS & FIXES")
        print("="*60)
        
        if self.issues:
            print("\n❌ ISSUES IDENTIFIED:")
            for i, issue in enumerate(self.issues, 1):
                severity_icon = "🔥" if issue["severity"] == "CRITICAL" else "⚠️" if issue["severity"] == "HIGH" else "💡"
                print(f"   {i}. {severity_icon} [{issue['severity']}] {issue['issue']}")
                
        if self.recommendations:
            print("\n🔧 RECOMMENDED FIXES:")
            for i, rec in enumerate(self.recommendations, 1):
                priority_icon = "🔥" if rec["priority"] == "CRITICAL" else "⚠️" if rec["priority"] == "HIGH" else "💡"
                print(f"   {i}. {priority_icon} [{rec['priority']}] {rec['recommendation']}")
                
        # Generate specific Railway instructions
        print(f"\n📋 RAILWAY-SPECIFIC INSTRUCTIONS:")
        
        if not db_url or "sqlite" in db_url.lower():
            print("   1. 🚂 Add PostgreSQL to Railway:")
            print("      • Go to Railway dashboard")
            print("      • Click 'New' → 'Database' → 'Add PostgreSQL'")
            print("      • Wait for deployment")
            
        print("   2. 🔗 Verify Connection:")
        print("      • Check app service environment variables")
        print("      • DATABASE_URL should appear automatically")
        print("      • App should redeploy after PostgreSQL is added")
            
        print("   3. 🧪 Test the Fix:")
        print("      • python registration_form/railway_diagnostics.py")
        print("      • curl https://camppowerup-registration.up.railway.app/test-db")
        
        # Summary
        critical_issues = sum(1 for issue in self.issues if issue["severity"] == "CRITICAL")
        
        if critical_issues > 0:
            print(f"\n🚨 {critical_issues} CRITICAL ISSUES - Immediate action required!")
        elif self.issues:
            print(f"\n⚠️  {len(self.issues)} issues found - Fixes recommended")
        else:
            print(f"\n🎉 DATABASE_URL configuration looks good!")
            
    def run_full_analysis(self, db_url: Optional[str] = None):
        """Run complete DATABASE_URL analysis"""
        print("🔗 DATABASE_URL Configuration Troubleshooter")
        print("=" * 50)
        
        # Check environment first
        env_db_url = self.check_environment_setup()
        
        # Use provided URL or environment URL
        analysis_url = db_url or env_db_url
        
        if not analysis_url:
            print("\n❌ No DATABASE_URL available for analysis")
            self.generate_fix_instructions()
            return
            
        print(f"\n🔍 Analyzing DATABASE_URL...")
        
        # Run all validations
        components = self.validate_database_url_format(analysis_url)
        self.check_railway_url_patterns(analysis_url)
        self.validate_connection_string_syntax(analysis_url)
        self.check_common_railway_issues(components)
        self.simulate_connection_test(analysis_url)
        
        # Generate fix instructions
        self.generate_fix_instructions(analysis_url)

def main():
    """Main troubleshooter function"""
    db_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    troubleshooter = DatabaseURLTroubleshooter()
    troubleshooter.run_full_analysis(db_url)

if __name__ == "__main__":
    main()