#!/usr/bin/env python3
"""
🏕️ Camp Power-Up Complete System Status Checker
===============================================
Comprehensive status check for all Camp Power-Up services and systems
"""

import requests
import sqlite3
import os
import subprocess
from datetime import datetime

def check_url_status(url, name, timeout=10):
    """Check if a URL is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name} is LIVE and responding")
            return True
        else:
            print(f"⚠️  {name} returned status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ {name} is not responding: {e}")
        return False

def check_port_status(port, name):
    """Check if a local port is being used"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            pid = result.stdout.strip().split('\n')[0]
            print(f"✅ {name} is running on port {port} (PID: {pid})")
            return True
        else:
            print(f"❌ {name} is not running on port {port}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Port check timed out for {name}")
        return False
    except FileNotFoundError:
        print(f"⚠️  Cannot check port status (lsof not available)")
        return False

def check_database_status(db_path, name):
    """Check database status and record counts"""
    if not os.path.exists(db_path):
        print(f"❌ {name}: Database file not found ({db_path})")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table count
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        # Try to get record counts from common tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        total_records = 0
        table_info = []
        
        for (table_name,) in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = cursor.fetchone()[0]
                total_records += count
                table_info.append(f"{table_name}: {count}")
            except:
                pass
        
        conn.close()
        
        # Get file size
        size = os.path.getsize(db_path)
        size_mb = size / (1024 * 1024)
        
        print(f"✅ {name}: {table_count} tables, {total_records} total records, {size_mb:.1f}MB")
        if table_info:
            for info in table_info[:3]:  # Show first 3 tables
                print(f"   └─ {info}")
            if len(table_info) > 3:
                print(f"   └─ ... and {len(table_info) - 3} more tables")
        
        return True
        
    except Exception as e:
        print(f"❌ {name}: Database error - {e}")
        return False

def get_recent_registrations():
    """Get recent registrations"""
    db_path = "registration_form/registration_submissions.db"
    
    if not os.path.exists(db_path):
        print("📝 No local registrations database found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get recent registrations
        cursor.execute('''
            SELECT child_first_name, child_last_name, parent_email, timestamp 
            FROM registrations 
            ORDER BY timestamp DESC 
            LIMIT 3
        ''')
        recent = cursor.fetchall()
        
        if recent:
            print("🕐 Most recent registrations:")
            for i, (first, last, email, timestamp) in enumerate(recent, 1):
                print(f"   {i}. {first} {last} ({email}) - {timestamp}")
        else:
            print("📝 No registrations found")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading registrations: {e}")

def main():
    print("🏕️ Camp Power-Up Complete System Status")
    print("=" * 45)
    print(f"⏰ Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check production deployment
    print("🌐 Production Deployment Status:")
    print("-" * 35)
    production_ok = check_url_status("https://camppowerup-production.up.railway.app/", "Registration Form")
    production_admin_ok = check_url_status("https://camppowerup-production.up.railway.app/admin", "Admin Dashboard")
    print()
    
    # Check local services
    print("🖥️  Local Services Status:")
    print("-" * 27)
    
    services = [
        (5000, "Main Dashboard"),
        (5001, "Game Library"),
        (5006, "Admin Portal"),
        (5007, "Communication System"),
        (5008, "Registration System (Local)")
    ]
    
    local_running = 0
    for port, name in services:
        if check_port_status(port, name):
            local_running += 1
    
    print()
    
    # Check databases
    print("💾 Database Status:")
    print("-" * 18)
    
    databases = [
        ("camp_power_up.db", "Main Camp Database"),
        ("registration_form/registration_submissions.db", "Registration Database"),
        ("communication/communication.db", "Communication Database"),
        ("security.db", "Security Database")
    ]
    
    db_ok = 0
    for db_path, name in databases:
        if check_database_status(db_path, name):
            db_ok += 1
    
    print()
    
    # Recent activity
    print("📋 Recent Activity:")
    print("-" * 18)
    get_recent_registrations()
    print()
    
    # System summary
    print("📊 System Summary:")
    print("-" * 17)
    print(f"🌐 Production:      {'✅ LIVE' if production_ok else '❌ DOWN'}")
    print(f"🖥️  Local Services:  {local_running}/{len(services)} running")
    print(f"💾 Databases:       {db_ok}/{len(databases)} accessible")
    
    # Overall health
    if production_ok and local_running >= 1 and db_ok >= 2:
        health = "🟢 HEALTHY"
    elif production_ok:
        health = "🟡 PARTIAL (Production OK)"
    else:
        health = "🔴 ISSUES DETECTED"
    
    print(f"🎯 Overall Status:  {health}")
    print()
    
    # Quick links and commands
    print("🔗 Quick Links:")
    print("-" * 14)
    print("   Registration Form: https://camppowerup-production.up.railway.app/")
    print("   Admin Dashboard:   https://camppowerup-production.up.railway.app/admin")
    if local_running > 0:
        print("   Local Admin:       http://127.0.0.1:5006/admin/login")
        print("   Local Services:    http://127.0.0.1:[5000|5007|5008]")
    print()
    
    print("🔧 Management Commands:")
    print("-" * 22)
    print("   Start all services:  ./deploy_all_services.sh")
    print("   Stop all services:   ./stop_all_services.sh")
    print("   Backup databases:    ./backup_databases.sh")
    print("   View documentation:  cat COMPLETE_SYSTEM_MANAGEMENT.md")

if __name__ == "__main__":
    main()