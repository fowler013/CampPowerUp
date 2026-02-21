#!/bin/bash
# 🏕️ Camp Power-Up Stop Services Script

echo "🛑 Stopping Camp Power-Up services..."

pkill -f "working_admin.py"
pkill -f "communication/app.py"
pkill -f "registration_form/app.py"
pkill -f "game_library.py"

echo "✅ All services stopped"
