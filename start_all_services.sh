#!/bin/bash
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
