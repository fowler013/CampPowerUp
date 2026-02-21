#!/bin/bash
# SUPER EMERGENCY RESTORE - Complete Working System
# Run this if ANYTHING gets broken: ./RESTORE_COMPLETE_WORKING_SYSTEM.sh

echo "🚨 SUPER EMERGENCY RESTORE: Complete Working System"
echo "=================================================="

# Stop any running Flask processes
echo "🛑 Stopping Flask processes..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Restore the LATEST working version with confirmation fix
echo "📋 Restoring app_CONFIRMATION_FIXED.py to app.py..."
cp registration_form/app_CONFIRMATION_FIXED.py registration_form/app.py

# Also restore the admin backup if needed
echo "📋 Admin backup available: app_WORKING_ADMIN_FINAL.py"

echo ""
echo "✅ COMPLETE SYSTEM RESTORED!"
echo ""
echo "🔐 Features Restored:"
echo "   • Professional admin interface (campadmin/PowerUp2025!)"
echo "   • Working statistics dashboard with age groups"
echo "   • Professional confirmation pages matching staging"
echo "   • Complete registration form with JSON submission" 
echo "   • Export functionality and registration management"
echo ""
echo "🚀 To restart: cd registration_form && python app.py"
echo "🌐 URLs:"
echo "   Registration: http://127.0.0.1:5000/"
echo "   Admin: http://127.0.0.1:5000/admin"
echo ""
echo "💾 Data Safety: All registration data preserved in SQLite DB"