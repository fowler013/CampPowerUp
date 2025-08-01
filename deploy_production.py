#!/usr/bin/env python3
"""
Camp Power-Up Production Deployment Script
==========================================

This script starts all Camp Power-Up services in the correct order for production deployment.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("🏕️" + "=" * 60 + "🏕️")
    print("🚀 CAMP POWER-UP PRODUCTION DEPLOYMENT")
    print("🏕️" + "=" * 60 + "🏕️")
    print()

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        return False
    
    # Check virtual environment
    venv_path = Path('.venv')
    if not venv_path.exists():
        print("❌ Virtual environment not found. Run: python -m venv .venv")
        return False
    
    # Check required files
    required_files = [
        'working_admin.py',
        'communication/app.py',
        'registration_form/app.py',
        'requirements.txt'
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file missing: {file}")
            return False
    
    print("✅ All requirements met")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_databases():
    """Initialize all databases"""
    print("🗄️ Setting up databases...")
    
    try:
        # Import and run database setup
        sys.path.append('.')
        from working_admin import ensure_database
        
        if ensure_database():
            print("✅ Security database initialized")
        else:
            print("❌ Failed to initialize security database")
            return False
            
        # Initialize other databases
        from registration_form.app import init_registration_db
        init_registration_db()
        print("✅ Registration database initialized")
        
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def start_services():
    """Start all Camp Power-Up services"""
    print("🚀 Starting Camp Power-Up services...")
    
    services = [
        {
            'name': 'Admin Portal',
            'command': [sys.executable, 'working_admin.py'],
            'port': 5006,
            'description': 'Secure admin dashboard and unified management'
        },
        {
            'name': 'Communication System',
            'command': [sys.executable, 'communication/app.py'],
            'port': 5007,
            'description': 'Email and SMS communication system'
        },
        {
            'name': 'Registration System',
            'command': [sys.executable, 'registration_form/app.py'],
            'port': 5008,
            'description': 'Camp registration and enrollment'
        }
    ]
    
    processes = []
    
    for service in services:
        print(f"🔄 Starting {service['name']} on port {service['port']}...")
        
        try:
            # Change to appropriate directory if needed
            cwd = None
            if '/' in service['command'][1]:
                cwd = os.path.dirname(service['command'][1])
                service['command'][1] = os.path.basename(service['command'][1])
            
            process = subprocess.Popen(
                service['command'],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            processes.append({
                'process': process,
                'name': service['name'],
                'port': service['port'],
                'description': service['description']
            })
            
            # Give the service time to start
            time.sleep(2)
            
            if process.poll() is None:  # Process is still running
                print(f"✅ {service['name']} started successfully")
            else:
                print(f"❌ {service['name']} failed to start")
                
        except Exception as e:
            print(f"❌ Failed to start {service['name']}: {e}")
    
    return processes

def print_service_info(processes):
    """Print information about running services"""
    print("\n🌐 CAMP POWER-UP SERVICES RUNNING")
    print("=" * 50)
    
    for service in processes:
        if service['process'].poll() is None:
            print(f"✅ {service['name']}")
            print(f"   📍 URL: http://127.0.0.1:{service['port']}")
            print(f"   📝 {service['description']}")
            print()
    
    print("🔐 ADMIN CREDENTIALS")
    print("=" * 30)
    print("👤 Username: admin")
    print("🔑 Password: admin123")
    print()
    print("🎯 QUICK ACCESS")
    print("=" * 20)
    print("🏠 Admin Dashboard: http://127.0.0.1:5006/admin/login")
    print("📧 Communication: http://127.0.0.1:5007")
    print("📋 Registration: http://127.0.0.1:5008")
    print()

def monitor_services(processes):
    """Monitor running services"""
    print("🔍 Monitoring services (Ctrl+C to stop all)...")
    
    try:
        while True:
            time.sleep(5)
            
            # Check if any service has stopped
            for service in processes:
                if service['process'].poll() is not None:
                    print(f"⚠️ {service['name']} has stopped unexpectedly")
                    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        
        for service in processes:
            if service['process'].poll() is None:
                service['process'].terminate()
                print(f"🔄 Stopping {service['name']}...")
                
        print("✅ All services stopped")

def main():
    """Main deployment function"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("❌ Deployment failed: Requirements not met")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Deployment failed: Could not install dependencies")
        sys.exit(1)
    
    # Setup databases
    if not setup_databases():
        print("❌ Deployment failed: Database setup failed")
        sys.exit(1)
    
    # Start services
    processes = start_services()
    
    if not processes:
        print("❌ Deployment failed: No services started")
        sys.exit(1)
    
    # Print service information
    print_service_info(processes)
    
    # Monitor services
    monitor_services(processes)

if __name__ == "__main__":
    main()
