#!/bin/bash
# 🛑 Stop All Camp Power-Up Services

echo "🛑 Stopping All Camp Power-Up Services"
echo "===================================="

# Ports for all services
ports=(5000 5001 5006 5007 5008)
service_names=("Main Dashboard" "Game Library" "Admin Portal" "Communication System" "Registration System")

echo "🔍 Finding and stopping services..."

for i in "${!ports[@]}"; do
    port=${ports[$i]}
    name=${service_names[$i]}
    
    echo "🔄 Checking port $port ($name)..."
    
    # Find processes using the port
    pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "🛑 Stopping $name (PID: $pids)"
        echo "$pids" | xargs kill -TERM 2>/dev/null
        
        # Wait a moment for graceful shutdown
        sleep 2
        
        # Force kill if still running
        remaining_pids=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            echo "💥 Force stopping $name (PID: $remaining_pids)"
            echo "$remaining_pids" | xargs kill -9 2>/dev/null
        fi
        
        # Verify stopped
        if ! lsof -ti :$port >/dev/null 2>&1; then
            echo "✅ $name stopped successfully"
        else
            echo "⚠️  $name may still be running"
        fi
    else
        echo "ℹ️  $name was not running on port $port"
    fi
done

echo ""
echo "🧹 Cleaning up background processes..."

# Kill any remaining Python processes that might be Camp Power-Up services
pkill -f "app.py" 2>/dev/null || true
pkill -f "working_admin.py" 2>/dev/null || true
pkill -f "game_library_service.py" 2>/dev/null || true

echo "✅ All services stopped!"
# 🏕️ Stop All Camp Power-Up Services

echo "🛑 Stopping all Camp Power-Up services..."

pkill -f "working_admin.py"
pkill -f "communication/app.py"
pkill -f "registration_form/app.py"
pkill -f "game_library.py"

echo "✅ All services stopped"
