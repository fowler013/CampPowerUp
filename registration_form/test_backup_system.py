#!/usr/bin/env python3
"""
Test the backup and audit system manually
"""

import sys
import os

# Add the registration_form directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the backup system
from backup_audit_system import main

if __name__ == "__main__":
    print("🧪 Testing Camp Power-Up Backup & Audit System")
    print("=" * 50)
    
    try:
        main()
        print("\n✅ Test completed successfully!")
        
        # Show what was created
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        audit_dir = os.path.join(os.path.dirname(__file__), 'audit_logs')
        
        print(f"\n📁 Files created in {backup_dir}:")
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                print(f"  - {file}")
        
        print(f"\n📋 Files created in {audit_dir}:")
        if os.path.exists(audit_dir):
            for file in os.listdir(audit_dir):
                print(f"  - {file}")
                
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()