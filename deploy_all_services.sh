#!/bin/bash
# 🏕️ Camp Power-Up - Deploy All Services Script
# Deploys all Camp Power-Up services to production

echo "🏕️ Camp Power-Up Complete Deployment"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Run this script from the CampPowerUp directory"
    exit 1
fi

# Function to check if a service is running
check_service() {
    local port=$1
    local name=$2
    
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$port/ | grep -q "200\|302"; then
        echo "✅ $name is running on port $port"
        return 0
    else
        echo "❌ $name is not responding on port $port"
        return 1
    fi
}

# Function to start a service
start_service() {
    local script=$1
    local port=$2
    local name=$3
    local dir=$4
    
    echo "🚀 Starting $name..."
    
    if [ -n "$dir" ]; then
        cd "$dir"
    fi
    
    # Kill any existing process on the port
    lsof -ti :$port | xargs kill -9 2>/dev/null || true
    sleep 2
    
    # Start the service in background
    nohup /Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python $script > "../logs/${name// /_}.log" 2>&1 &
    
    # Wait a moment for startup
    sleep 3
    
    if [ -n "$dir" ]; then
        cd ..
    fi
    
    # Check if it started successfully
    if check_service $port "$name"; then
        return 0
    else
        echo "⚠️ $name may still be starting up"
        return 1
    fi
}

# Create logs directory
mkdir -p logs

echo ""
echo "🔄 Checking for uncommitted changes..."
if ! git diff --quiet; then
    echo "📝 Uncommitted changes found. Committing..."
    git add .
    read -p "Enter commit message: " commit_msg
    git commit -m "$commit_msg"
fi

echo ""
echo "🚀 Deploying Registration Form to Railway..."
git push origin main
echo "✅ Registration Form deployment triggered (live in 2-3 minutes)"
echo "🔗 Registration Form: https://camppowerup-production.up.railway.app/"

echo ""
echo "🏃 Starting Local Services..."

# Start all local services
start_service "app.py" 5000 "Main Dashboard" ""
start_service "working_admin.py" 5006 "Admin Portal" ""
start_service "app.py" 5007 "Communication System" "communication"
start_service "app.py" 5008 "Registration System" "registration_form"

# Note: Game Library is integrated with Main Dashboard on port 5000

echo ""
echo "📊 Service Status Summary:"
echo "========================="

services=(
    "5000:Main Dashboard (includes Game Library):http://127.0.0.1:5000"
    "5006:Admin Portal:http://127.0.0.1:5006/admin/login"
    "5007:Communication:http://127.0.0.1:5007"
    "5008:Registration:http://127.0.0.1:5008"
)

all_running=true
for service in "${services[@]}"; do
    IFS=':' read -r port name url <<< "$service"
    if check_service $port "$name"; then
        echo "🔗 $name: $url"
    else
        all_running=false
    fi
done

echo ""
echo "🌐 Production URLs:"
echo "=================="
echo "🔗 Live Registration: https://camppowerup-production.up.railway.app/"
echo "👨‍💻 Admin Dashboard:   https://camppowerup-production.up.railway.app/admin"

echo ""
echo "🔧 Management Commands:"
echo "======================"
echo "📊 Check status:        python3 check_status.py"
echo "🛑 Stop all services:   ./stop_all_services.sh"
echo "📋 View logs:           tail -f logs/*.log"
echo "💾 Backup databases:    ./backup_databases.sh"

if [ "$all_running" = true ]; then
    echo ""
    echo "🎉 All services deployed and running successfully!"
else
    echo ""
    echo "⚠️  Some services may still be starting. Check logs if issues persist."
fi

echo ""
echo "📚 Full documentation: COMPLETE_SYSTEM_MANAGEMENT.md"