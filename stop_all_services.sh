#!/bin/bash
# 🏕️ Stop All Camp Power-Up Services

echo "🛑 Stopping all Camp Power-Up services..."

pkill -f "working_admin.py"
pkill -f "communication/app.py"
pkill -f "registration_form/app.py"
pkill -f "game_library.py"

echo "✅ All services stopped"
