#!/bin/bash
# EMERGENCY RESTORE SCRIPT
# Use this script to restore the working version if something breaks

echo "🚨 RESTORING WORKING VERSION..."
echo "Copying working backup to main app..."

cp registration_form/app_working_backup.py registration_form/app.py

echo "✅ Restored app.py from working backup"
echo "📁 Templates are already in place"
echo "🚀 You can now commit and push to deploy the working version"
echo ""
echo "Next steps:"
echo "1. git add ."
echo "2. git commit -m 'EMERGENCY RESTORE: Back to working version'"
echo "3. git push"
echo ""
echo "✅ Working version restored!"