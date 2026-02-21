#!/bin/bash
# Emergency restore script for working admin system
# Run this if app.py gets broken: ./RESTORE_FINAL_ADMIN.sh

echo "🚨 EMERGENCY RESTORE: Restoring working admin system..."

# Stop any running Flask processes
echo "🛑 Stopping Flask processes..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Restore the working admin version
echo "📋 Restoring app_WORKING_ADMIN_FINAL.py to app.py..."
cp registration_form/app_WORKING_ADMIN_FINAL.py registration_form/app.py

echo "✅ RESTORE COMPLETE!"
echo ""
echo "🔐 Admin System Restored with:"
echo "   • Professional admin interface"
echo "   • Authentication: campadmin/PowerUp2025!"
echo "   • All statistics working"
echo "   • Export functionality"
echo ""
echo "🚀 To restart: cd registration_form && python app.py"
echo "🌐 Admin URL: http://127.0.0.1:5000/admin"