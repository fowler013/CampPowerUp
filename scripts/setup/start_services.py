#!/usr/bin/env python3
"""
Start all CampPowerUp services
"""
import subprocess
import time
import os

def start_service(directory, script, port, name):
    """Start a service in a specific directory"""
    print(f"🚀 Starting {name} on port {port}...")
    
    try:
        # Change to the directory and start the service
        process = subprocess.Popen(
            ['python3', script],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's still running
        if process.poll() is None:
            print(f"✅ {name} started successfully (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {name} failed to start:")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return None

def main():
    base_dir = '/Users/tevinfowler/Documents/CampPowerUp'
    
    # Start registration form
    reg_dir = os.path.join(base_dir, 'registration_form')
    reg_process = start_service(reg_dir, 'app.py', 5001, 'Registration Form')
    
    # Start communication service  
    comm_dir = os.path.join(base_dir, 'communication')
    comm_process = start_service(comm_dir, 'app_simple.py', 5004, 'Communication Service')
    
    print("\n📊 Service Status:")
    print(f"Registration Form: {'✅ Running' if reg_process and reg_process.poll() is None else '❌ Not running'}")
    print(f"Communication: {'✅ Running' if comm_process and comm_process.poll() is None else '❌ Not running'}")
    
    print(f"\n🔗 Service URLs:")
    print(f"Registration Form: http://127.0.0.1:5001")
    print(f"Communication: http://127.0.0.1:5004")

if __name__ == '__main__':
    main()
