#!/usr/bin/env python3
"""
🏕️ Camp Power-Up - Final Production Setup
Creates production configuration and deployment files
"""

import os

def create_production_config():
    """Create production configuration files"""
    print("🏕️ CREATING PRODUCTION CONFIGURATION")
    print("=" * 50)
    
    # Create .env template
    env_template = """# 🏕️ Camp Power-Up Production Configuration

# ========================================
# CAMP INFORMATION
# ========================================
CAMP_NAME="Camp Power-Up"
CAMP_EMAIL="admin@camppowerup.com"
CAMP_PHONE="(555) 123-CAMP"

# ========================================
# EMAIL CONFIGURATION
# ========================================
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USERNAME="your-camp-email@gmail.com"
SMTP_PASSWORD="your-app-password-here"
SMTP_USE_TLS="true"

# ========================================
# SMS CONFIGURATION (TWILIO)
# ========================================
TWILIO_ACCOUNT_SID="your-twilio-account-sid"
TWILIO_AUTH_TOKEN="your-twilio-auth-token"
TWILIO_PHONE_NUMBER="+1234567890"

# ========================================
# SECURITY SETTINGS
# ========================================
SECRET_KEY="change-this-to-a-secure-random-string"
SESSION_TIMEOUT_HOURS="8"
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env.template")
    
    # Create production requirements
    prod_requirements = """# Additional Production Dependencies
stripe>=5.0.0
pillow>=9.0.0
pandas>=1.5.0
matplotlib>=3.6.0
python-dotenv>=0.19.0
gunicorn>=20.0.0
"""
    
    with open('requirements-production.txt', 'w') as f:
        f.write(prod_requirements)
    
    print("✅ Created requirements-production.txt")
    
    # Create deployment script
    deploy_script = """#!/bin/bash
# 🏕️ Camp Power-Up Production Deployment

echo "🏕️ Starting Camp Power-Up Production Services"
echo "============================================="

# Create logs directory
mkdir -p logs

# Start all services
echo "🚀 Starting Admin Portal..."
nohup python working_admin.py > logs/admin.log 2>&1 &

echo "🚀 Starting Communication Service..."
nohup python communication/app.py > logs/communication.log 2>&1 &

echo "🚀 Starting Registration Service..."
nohup python registration_form/app.py > logs/registration.log 2>&1 &

echo "🚀 Starting Game Library..."
nohup python game_library.py > logs/games.log 2>&1 &

echo ""
echo "🎉 All services started!"
echo "🔗 Admin Portal: http://localhost:5009/admin/login"
echo "📧 Communication: http://localhost:5007"
echo "📋 Registration: http://localhost:5008"
echo "🎮 Game Library: http://localhost:5000"
"""
    
    with open('start_all_services.sh', 'w') as f:
        f.write(deploy_script)
    
    os.chmod('start_all_services.sh', 0o755)
    
    print("✅ Created start_all_services.sh")
    
    # Create stop script
    stop_script = """#!/bin/bash
# 🏕️ Stop All Camp Power-Up Services

echo "🛑 Stopping all Camp Power-Up services..."

pkill -f "working_admin.py"
pkill -f "communication/app.py"
pkill -f "registration_form/app.py"
pkill -f "game_library.py"

echo "✅ All services stopped"
"""
    
    with open('stop_all_services.sh', 'w') as f:
        f.write(stop_script)
    
    os.chmod('stop_all_services.sh', 0o755)
    
    print("✅ Created stop_all_services.sh")
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    print("✅ Created logs directory")
    
    print("\n🎉 PRODUCTION SETUP COMPLETE!")
    print("=" * 50)
    print("✅ Configuration templates created")
    print("✅ Deployment scripts ready")
    print("✅ Service management tools prepared")
    print("\n🚀 Ready for production deployment!")

if __name__ == "__main__":
    create_production_config()
