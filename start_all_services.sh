#!/bin/bash
# 🏕️ Camp Power-Up Production Deployment

echo "🏕️ Starting Camp Power-Up Production Services"
echo "============================================="

# Create logs directory
mkdir -p logs

# Start all services
echo "🚀 Starting Admin Portal..."
nohup python3 working_admin.py > logs/admin.log 2>&1 &

echo "🚀 Starting Communication Service..."
nohup env PORT=5007 python3 communication/app.py > logs/communication.log 2>&1 &

echo "🚀 Starting Registration Service..."
nohup python3 registration_form/app.py > logs/registration.log 2>&1 &

echo "🚀 Starting Game Library..."
nohup python3 game_library_service.py > logs/games.log 2>&1 &

echo ""
echo "🎉 All services started!"
echo "🔗 Admin Portal: http://localhost:5009/admin/login"
echo "📧 Communication: http://localhost:5007"
echo "📋 Registration: http://localhost:5008"
echo "🎮 Game Library: http://localhost:5000"
