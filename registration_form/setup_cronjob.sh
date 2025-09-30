#!/bin/bash
"""
Camp Power-Up Cronjob Setup Script
Sets up daily backup and audit cronjob
"""

# Configuration
SCRIPT_DIR="/Users/tevinfowler/Documents/CampPowerUp/registration_form"
PYTHON_PATH="/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_audit_system.py"
LOG_FILE="$SCRIPT_DIR/backup_audit.log"

echo "🏕️ Camp Power-Up Cronjob Setup"
echo "=============================="

# Make the backup script executable
chmod +x "$BACKUP_SCRIPT"

# Create log file if it doesn't exist
touch "$LOG_FILE"

# Display current crontab
echo "Current crontab entries:"
crontab -l 2>/dev/null || echo "No current crontab entries"

echo ""
echo "Setting up daily backup cronjob..."

# Create new crontab entry (runs at 2 AM daily)
(crontab -l 2>/dev/null; echo "0 2 * * * cd $SCRIPT_DIR && $PYTHON_PATH $BACKUP_SCRIPT >> $LOG_FILE 2>&1") | crontab -

echo "✅ Cronjob installed successfully!"
echo ""
echo "Cronjob Details:"
echo "- Runs daily at 2:00 AM"
echo "- Script: $BACKUP_SCRIPT"
echo "- Log file: $LOG_FILE"
echo "- Python: $PYTHON_PATH"
echo ""
echo "To view the cronjob:"
echo "  crontab -l"
echo ""
echo "To view logs:"
echo "  tail -f $LOG_FILE"
echo ""
echo "To remove the cronjob:"
echo "  crontab -e  # then delete the line"