#!/bin/bash
# 🏕️ Camp Power-Up Production Deployment Script

echo "🏕️ Camp Power-Up Production Deployment"
echo "======================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please copy .env.template to .env and configure."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Start services
echo "🚀 Starting production services..."

# Create logs directory
mkdir -p logs

# Start in background with nohup for production
nohup python3 working_admin.py > logs/admin.log 2>&1 &
echo "✅ Admin portal started"

nohup python3 communication/app.py > logs/communication.log 2>&1 &
echo "✅ Communication service started"

nohup python3 registration_form/app.py > logs/registration.log 2>&1 &
echo "✅ Registration service started"

nohup python3 game_library.py > logs/games.log 2>&1 &
echo "✅ Game library started"

echo ""
echo "🎉 All services started!"
echo "🔗 Admin Portal: http://localhost:5009/admin/login"
echo "📧 Communication: http://localhost:5007"
echo "📋 Registration: http://localhost:5008"
echo "🎮 Game Library: http://localhost:5000"
echo ""
echo "📋 Logs are stored in the logs/ directory"
echo "🛑 To stop all services: ./stop_services.sh"
