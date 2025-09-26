#!/bin/bash
# 💾 Backup All Camp Power-Up Databases

echo "💾 Camp Power-Up Database Backup"
echo "==============================="

# Create backup directory with timestamp
backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

echo "📁 Creating backups in: $backup_dir"

# Database files to backup
declare -A databases=(
    ["camp_power_up.db"]="Main Camp Database (Analytics, Camper Data)"
    ["registration_form/registration_submissions.db"]="Registration Database (New Enrollments)"
    ["communication/communication.db"]="Communication Database (Messages, Templates)"
    ["security.db"]="Security Database (Users, Audit Logs)"
)

backup_count=0
total_size=0

for db_path in "${!databases[@]}"; do
    db_desc="${databases[$db_path]}"
    
    if [ -f "$db_path" ]; then
        echo "🔄 Backing up $db_path..."
        
        # Get file size
        size=$(stat -f%z "$db_path" 2>/dev/null || stat -c%s "$db_path" 2>/dev/null || echo "0")
        size_mb=$((size / 1024 / 1024))
        
        # Copy database
        backup_file="$backup_dir/$(basename "$db_path")"
        cp "$db_path" "$backup_file"
        
        if [ $? -eq 0 ]; then
            echo "✅ $db_desc → $backup_file (${size_mb}MB)"
            backup_count=$((backup_count + 1))
            total_size=$((total_size + size))
            
            # Verify backup integrity
            if command -v sqlite3 >/dev/null 2>&1; then
                if sqlite3 "$backup_file" "PRAGMA integrity_check;" | grep -q "ok"; then
                    echo "   ✓ Integrity check passed"
                else
                    echo "   ⚠️ Integrity check warning"
                fi
            fi
        else
            echo "❌ Failed to backup $db_path"
        fi
    else
        echo "⚠️ $db_path not found (may not exist yet)"
    fi
done

# Backup configuration files
echo ""
echo "📋 Backing up configuration files..."

config_files=(".env" "config.py" "requirements.txt" "railway.json" "Procfile")

for config in "${config_files[@]}"; do
    if [ -f "$config" ]; then
        cp "$config" "$backup_dir/"
        echo "✅ $config → $backup_dir/"
    fi
done

# Create backup summary
cat > "$backup_dir/backup_info.txt" << EOF
Camp Power-Up Database Backup
=============================
Backup Date: $(date)
Backup Location: $backup_dir

Databases Backed Up: $backup_count
Total Size: $((total_size / 1024 / 1024))MB

Files:
EOF

ls -la "$backup_dir"/ >> "$backup_dir/backup_info.txt"

echo ""
echo "📊 Backup Summary:"
echo "=================="
echo "✅ Databases backed up: $backup_count"
echo "💾 Total backup size: $((total_size / 1024 / 1024))MB"
echo "📁 Backup location: $backup_dir"

# Create compressed archive
if command -v tar >/dev/null 2>&1; then
    echo ""
    echo "🗜️  Creating compressed archive..."
    archive_name="camp_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$archive_name" -C backups "$(basename "$backup_dir")"
    
    if [ $? -eq 0 ]; then
        archive_size=$(stat -f%z "$archive_name" 2>/dev/null || stat -c%s "$archive_name" 2>/dev/null || echo "0")
        archive_size_mb=$((archive_size / 1024 / 1024))
        echo "✅ Compressed backup: $archive_name (${archive_size_mb}MB)"
        
        # Cleanup uncompressed backup
        read -p "🗑️  Remove uncompressed backup? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$backup_dir"
            echo "✅ Uncompressed backup removed"
        fi
    else
        echo "❌ Failed to create compressed archive"
    fi
fi

echo ""
echo "🔧 Backup Management:"
echo "===================="
echo "📂 View backups:     ls -la backups/"
echo "🔄 Restore backup:   cp backups/DATABASE_NAME.db ./"
echo "🧹 Clean old backups: find backups/ -mtime +30 -delete"

# Show current database stats
echo ""
echo "📊 Current Database Status:"
echo "=========================="

for db_path in "${!databases[@]}"; do
    if [ -f "$db_path" ]; then
        if command -v sqlite3 >/dev/null 2>&1; then
            record_count=$(sqlite3 "$db_path" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
            echo "📋 $(basename "$db_path"): $record_count tables"
        fi
    fi
done

echo ""
echo "🎉 Backup completed successfully!"