#!/usr/bin/env python3
"""
Railway Environment Setup Script
Configures the app for Railway PostgreSQL deployment
"""

import os
import subprocess
import sys

def check_railway_environment():
    """Check if running on Railway and if PostgreSQL is configured."""
    print("🚂 Railway Environment Check")
    print("=" * 50)
    
    # Check environment variables
    database_url = os.environ.get('DATABASE_URL')
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
    
    print(f"Railway Environment: {railway_env or 'Not detected'}")
    print(f"Database URL: {'✅ Set' if database_url else '❌ Not Set'}")
    
    if database_url:
        print(f"Database Type: {'PostgreSQL' if 'postgresql://' in database_url else 'Other'}")
        # Don't print the full URL for security
        if 'postgresql://' in database_url:
            parts = database_url.split('@')
            if len(parts) > 1:
                host_part = parts[1].split('/')[0]
                print(f"Database Host: {host_part}")
    
    return bool(database_url and 'postgresql://' in database_url)

def test_database_connection():
    """Test the database connection."""
    print("\n🔧 Testing Database Connection")
    print("=" * 50)
    
    try:
        # Import our database config
        from database_config import get_db_connection, DB_CONFIG
        
        print(f"Production Mode: {DB_CONFIG['is_production']}")
        print(f"Database URL Set: {bool(DB_CONFIG.get('database_url'))}")
        
        # Test connection
        with get_db_connection('registration') as conn:
            cursor = conn.cursor()
            
            if DB_CONFIG['is_production']:
                # PostgreSQL test
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"✅ PostgreSQL Connection: {version[:50]}...")
                
                # Test table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'registrations'
                    )
                """)
                table_exists = cursor.fetchone()[0]
                print(f"Registrations Table: {'✅ Exists' if table_exists else '❌ Missing'}")
                
            else:
                # SQLite test
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                print(f"✅ SQLite Connection: Version {version}")
                
                # Test table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='registrations'
                """)
                table_exists = cursor.fetchone()
                print(f"Registrations Table: {'✅ Exists' if table_exists else '❌ Missing'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")
        return False

def initialize_postgresql_tables():
    """Initialize PostgreSQL tables if needed."""
    print("\n📊 Initializing PostgreSQL Tables")
    print("=" * 50)
    
    try:
        from database_config import init_postgresql_tables
        success = init_postgresql_tables()
        if success:
            print("✅ PostgreSQL tables initialized successfully")
        else:
            print("ℹ️ Tables already exist or not in production mode")
        return success
    except Exception as e:
        print(f"❌ Table initialization failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🏕️ Camp Power-Up Railway Setup")
    print("=" * 60)
    
    # Check environment
    has_postgres = check_railway_environment()
    
    # Test connection
    connection_ok = test_database_connection()
    
    # Initialize tables if needed
    if has_postgres and connection_ok:
        initialize_postgresql_tables()
    
    # Summary
    print("\n📋 Setup Summary")
    print("=" * 50)
    if has_postgres and connection_ok:
        print("✅ Railway PostgreSQL setup complete!")
        print("✅ Ready for production deployment")
        print("\n🔗 Test endpoints:")
        print("   - Database test: /test-db")
        print("   - Registration form: /")
        print("   - Admin dashboard: /admin/login")
    else:
        print("⚠️ Setup incomplete - check the steps above")
        
        if not has_postgres:
            print("\n📚 Next steps:")
            print("1. Add PostgreSQL service to Railway project")
            print("2. Ensure DATABASE_URL is set in app service")
            print("3. Redeploy and run this script again")

if __name__ == "__main__":
    main()