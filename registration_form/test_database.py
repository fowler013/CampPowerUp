#!/usr/bin/env python3
"""
Database Testing Script for Camp Power-Up
Tests database connections and admin dashboard functionality
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database_config import DB_CONFIG, get_db_connection
import sqlite3

def test_database_connection():
    """Test database connection and registration count."""
    print("🏕️ Camp Power-Up Database Testing")
    print("=" * 50)
    
    print(f"Environment: {'Production' if DB_CONFIG['is_production'] else 'Development'}")
    print(f"Database Type: {'PostgreSQL' if DB_CONFIG['is_production'] else 'SQLite'}")
    print(f"DATABASE_URL: {'Set' if DB_CONFIG.get('database_url') else 'Not Set'}")
    print()
    
    try:
        print(f"🔗 Testing {'PostgreSQL' if DB_CONFIG['is_production'] else 'SQLite'} connection...")
        
        with get_db_connection('registration') as conn:
            if not DB_CONFIG['is_production']:
                conn.row_factory = sqlite3.Row
                
            cursor = conn.cursor()
            
            # Test query
            cursor.execute('SELECT COUNT(*) FROM registrations')
            total_count = cursor.fetchone()[0]
            
            # Get sample registration
            cursor.execute('''
                SELECT child_first_name, child_last_name, parent_email, timestamp 
                FROM registrations 
                ORDER BY timestamp DESC 
                LIMIT 3
            ''')
            recent_registrations = cursor.fetchall()
        
        print(f"✅ Database connection successful!")
        print(f"📊 Total registrations: {total_count}")
        print()
        
        if recent_registrations:
            print("📋 Recent registrations:")
            for i, reg in enumerate(recent_registrations, 1):
                print(f"   {i}. {reg[0]} {reg[1]} ({reg[2]}) - {reg[3]}")
        else:
            print("📋 No registrations found")
            
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_admin_dashboard_data():
    """Test the admin dashboard data retrieval."""
    print("\n🔧 Testing Admin Dashboard Data")
    print("=" * 50)
    
    try:
        with get_db_connection('registration') as conn:
            if DB_CONFIG['is_production']:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM registrations ORDER BY timestamp DESC')
                columns = [desc[0] for desc in cursor.description]
                registrations = [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM registrations ORDER BY timestamp DESC')
                registrations = [dict(row) for row in cursor.fetchall()]
        
        total_registrations = len(registrations)
        paid_count = len([r for r in registrations if r['payment_status'] == 'paid'])
        pending_count = len([r for r in registrations if r['payment_status'] == 'pending'])
        
        print(f"✅ Admin dashboard data retrieval successful!")
        print(f"📊 Statistics:")
        print(f"   Total Registrations: {total_registrations}")
        print(f"   Paid: {paid_count}")
        print(f"   Pending Payment: {pending_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin dashboard data test failed: {e}")
        return False

def main():
    """Run all database tests."""
    print("🧪 Starting Camp Power-Up Database Tests")
    print("=" * 60)
    print()
    
    # Test basic connection
    db_test = test_database_connection()
    
    # Test admin dashboard
    admin_test = test_admin_dashboard_data()
    
    print("\n" + "=" * 60)
    if db_test and admin_test:
        print("✅ All tests passed! Database is working correctly.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("\n💡 Next steps:")
    if not DB_CONFIG['is_production']:
        print("   - To test with Railway staging: ./get_staging_url.sh")
        print("   - Configure staging: ./use_staging.sh")
    else:
        print("   - You're connected to PostgreSQL!")
        print("   - Admin dashboard should show persistent data")

if __name__ == "__main__":
    main()