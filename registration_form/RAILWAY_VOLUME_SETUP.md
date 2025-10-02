# Railway Persistent Volume Setup Guide

## 🎯 Problem
Railway uses ephemeral storage by default, meaning your SQLite database gets wiped on every deployment. This causes all registration data to be lost.

## ✅ Solution: Configure Persistent Volume

### Step-by-Step Instructions:

1. **Go to Railway Dashboard**
   - Visit: https://railway.app
   - Login to your account

2. **Navigate to Your Project**
   - Click on "camppowerup-registration" project
   - Click on the service running your Flask app

3. **Add a Volume**
   - Click on the **"Settings"** tab
   - Scroll down to **"Volumes"** section
   - Click **"+ New Volume"**

4. **Configure the Volume**
   - **Mount Path**: `/data`
   - **Size**: `1 GB` (Railway free tier allows 1GB)
   - Click **"Add"**

5. **Railway will automatically redeploy**
   - Wait 2-3 minutes for redeployment
   - Your app will restart and detect the persistent volume

6. **Verify the Volume is Working**
   - Visit: https://camppowerup-registration.up.railway.app/railway-status
   - You should see:
     ```json
     {
       "persistent_volume_configured": true,
       "current_storage_type": "persistent",
       "data_persistence": "✅ Data survives deployments"
     }
     ```

## 🔍 How to Verify It's Working

After adding the volume, check:
- `/test-db` - Should show database_file: "/data/registration_submissions.db"
- Submit a test registration
- Trigger a Railway redeploy (push a small change to GitHub)
- Check if the test registration still exists

## 📦 Alternative: Manual Backup/Restore (If Volume Not Available)

If you can't add a persistent volume, you can manually backup/restore data:

### Backup Data:
1. Go to: https://camppowerup-registration.up.railway.app/admin
2. Login with credentials
3. Click "Export as JSON" 
4. Save the `registrations.json` file

### Restore Data:
1. After Railway redeploys and wipes data
2. Use the import endpoint with your saved JSON
3. Or keep registrations in a git-tracked file

## 🚨 Current Status

Run this to check current status:
```
curl https://camppowerup-registration.up.railway.app/railway-status
```

## 📊 Volume Information

- **Railway Free Tier**: 1GB persistent volume included
- **Database File Location**: `/data/registration_submissions.db`
- **Backup Location**: Your local computer via export
- **Auto-backup**: Consider setting up scheduled exports

## 🔧 Troubleshooting

**If volume isn't detected after adding:**
1. Check Railway logs for volume mount messages
2. Ensure mount path is exactly `/data` (case-sensitive)
3. Try redeploying manually from Railway dashboard
4. Check app logs for: "✅ Found persistent volume at /data"

**If you see "ephemeral storage" warning:**
- The volume isn't configured yet
- Follow steps 1-5 above
- Check Railway dashboard to confirm volume was created

## 💡 Best Practices

1. **Export data regularly** until volume is confirmed working
2. **Keep a local backup** of registrations
3. **Test volume** by redeploying and checking data persistence
4. **Monitor storage** - 1GB should handle thousands of registrations
