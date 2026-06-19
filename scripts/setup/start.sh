#!/bin/bash
# Startup script for Railway deployment with volume permission fixes

echo "🚀 Starting Camp Power-Up Registration System..."
echo "👤 Running as UID: $(id -u), GID: $(id -g)"

# Check if /data volume exists and fix permissions
if [ -d "/data" ]; then
    echo "✅ Volume detected at /data"
    
    # Show current permissions
    ls -la /data | head -5
    
    # Fix ownership and permissions (we're running as root)
    echo "🔧 Fixing permissions on /data..."
    chmod 777 /data || echo "⚠️ Could not chmod /data"
    
    # Create app_data subdirectory with proper permissions
    echo "📁 Creating /data/app_data directory..."
    mkdir -p /data/app_data
    chmod 777 /data/app_data
    
    # Verify writable
    if touch /data/.test 2>/dev/null; then
        rm /data/.test
        echo "✅ /data is writable!"
    elif touch /data/app_data/.test 2>/dev/null; then
        rm /data/app_data/.test
        echo "✅ /data/app_data is writable!"
    else
        echo "⚠️ /data still not writable after permission fix"
    fi
else
    echo "⚠️ No volume found at /data - will use ephemeral storage"
fi

# Start the Flask application (as root for volume access)
echo "🌟 Starting Flask application..."
cd /app
exec python registration_form/app.py
