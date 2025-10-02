# Data Persistence Solution for Railway

## 🎯 Overview

This app now has **TWO layers of protection** against data loss on Railway:

### 1. Persistent Volume (Recommended - Best Solution)
### 2. Auto-Backup System (Fallback Protection)

---

## ✅ Layer 1: Railway Persistent Volume Setup

### Quick Setup (5 minutes):

1. **Go to Railway Dashboard**: https://railway.app
2. **Open your project** → Click on your service
3. **Settings tab** → Scroll to "Volumes"
4. **Click "+ New Volume"**:
   - Mount Path: `/data`
   - Size: `1 GB`
5. **Click "Add"** → Railway auto-redeploys

### Verify It's Working:
```bash
curl https://camppowerup-registration.up.railway.app/railway-status
```

Should show:
```json
{
  "persistent_volume_configured": true,
  "current_storage_type": "persistent",
  "data_persistence": "✅ Data survives deployments"
}
```

---

## 🛡️ Layer 2: Auto-Backup System (Already Implemented!)

Your app now **automatically** saves backups:

### How It Works:

1. **After Each Registration**:
   - App saves a complete backup to `registrations_backup.json`
   - Contains all registrations in JSON format
   - Happens transparently in the background

2. **On App Startup**:
   - If database is empty
   - AND backup file exists
   - App automatically restores all data!

3. **Manual Export Anytime**:
   - Go to: https://camppowerup-registration.up.railway.app/admin
   - Click "Export as JSON"
   - Save the file to your computer

### Manual Restore (If Needed):

If Railway wipes data before auto-restore works:

```bash
# Export current data (do this regularly!)
curl https://camppowerup-registration.up.railway.app/admin/export-json > registrations_backup.json

# Import data back (POST the JSON file)
curl -X POST https://camppowerup-registration.up.railway.app/admin/import-json \
  -H "Content-Type: application/json" \
  -d @registrations_backup.json
```

---

## 🔄 Current Status

Check what's currently configured:

```bash
# Check storage status
curl https://camppowerup-registration.up.railway.app/railway-status

# Check database content
curl https://camppowerup-registration.up.railway.app/test-db

# Get all registrations for backup
curl https://camppowerup-registration.up.railway.app/admin/export-json
```

---

## 📊 Which Solution Should You Use?

| Solution | Pros | Cons | When to Use |
|----------|------|------|-------------|
| **Persistent Volume** | ✅ Automatic<br>✅ No data loss<br>✅ Production-ready | Requires Railway dashboard setup | **Always** - Set this up first! |
| **Auto-Backup** | ✅ Automatic protection<br>✅ Already working<br>✅ No setup needed | Backup file stored on ephemeral storage | Fallback if volume not configured |
| **Manual Export** | ✅ Complete control<br>✅ Local backup | Manual process | Regular backups, peace of mind |

---

## 🚨 Best Practice Workflow

### For Production (Right Now):

1. **✅ DONE**: Auto-backup system is already running
2. **TODO**: Add persistent volume on Railway (5 min setup)
3. **ONGOING**: Periodic manual exports to your local computer

### Daily Operation:

1. Users submit registrations → Auto-saved to backup
2. Railway redeploys → Data preserved (if volume configured)
3. If volume not configured → Auto-restore from backup on startup

### Weekly Maintenance:

```bash
# Download a safety backup to your computer
curl https://camppowerup-registration.up.railway.app/admin/export-json > \
  backup_$(date +%Y%m%d).json
```

---

## 🔍 Troubleshooting

### "Database is empty after deployment!"

**Check 1**: Is persistent volume configured?
```bash
curl https://camppowerup-registration.up.railway.app/railway-status
```

**Check 2**: Does auto-backup exist?
- Check Railway logs for: "📦 Found backup file, attempting auto-restore..."
- If not, the backup file was also wiped (ephemeral storage)

**Solution**: 
- Add persistent volume (prevents future issues)
- Keep manual exports on your local computer

### "Can't add persistent volume"

Some Railway plans may have limitations. If you can't add a volume:

1. **Regular exports**: Set a calendar reminder to export data weekly
2. **Version control**: Keep a committed backup in git (careful with privacy!)
3. **External storage**: Upload backups to Google Drive, Dropbox, etc.

---

## 💡 Pro Tips

1. **Before Any Railway Changes**: Export data first!
2. **After Adding Volume**: Submit test registration, redeploy, verify data persists
3. **Keep 3 Backups**: One on Railway (auto), one on your computer (manual export), one in cloud storage
4. **Test Restore**: Occasionally test the import process to ensure backups work

---

## 📝 Summary

**Current Protection Level**: 🟡 Medium (Auto-backup active, but on ephemeral storage)

**After Adding Volume**: 🟢 High (Persistent volume + Auto-backup + Manual export)

**Action Required**: Add persistent volume on Railway dashboard (see Layer 1 above)

---

## 🆘 Need Help?

Check Railway logs for debugging:
- Look for "✅ Found persistent volume at /data"
- Look for "📦 Found backup file, attempting auto-restore..."
- Look for "💾 Auto-backup created: X registrations saved"

Your data is protected! 🛡️
