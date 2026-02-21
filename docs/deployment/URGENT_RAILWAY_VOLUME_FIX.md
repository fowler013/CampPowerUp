🚨 URGENT: Railway Production Volume Setup Required
=================================================

## PROBLEM IDENTIFIED
Production site (https://camppowerup-registration.up.railway.app/) shows empty registration details because:

1. **Railway Production has NO persistent volume configured**
2. **Staging has persistent volume configured** (that's why it works)
3. **SQLite database gets wiped on every deployment** in production
4. Registration IDs exist but actual data is gone

## IMMEDIATE FIX REQUIRED

### Step 1: Add Persistent Volume to Railway Production

**Option A: Railway Dashboard (Recommended)**
```
1. Go to https://railway.app/dashboard
2. Select your production project "camppowerup-registration"
3. Click on the service name 
4. Go to "Storage" tab
5. Click "Add Volume"
6. Set:
   - Volume Name: "registration-data"
   - Mount Path: "/data"
   - Size: "1GB" (more than enough for registration DB)
7. Click "Create Volume"
8. Railway will automatically redeploy
```

**Option B: Railway CLI (Alternative)**
```bash
railway login
railway link # Select your production project
railway volumes create registration-data --mount /data --size 1
railway redeploy
```

**⚠️ CRITICAL:** After volume creation, Railway automatically redeploys. The updated code will detect `/data` mount and use persistent storage!

### Step 2: Verify Volume Mount
```bash
# Check if volume exists in production:
https://camppowerup-registration.up.railway.app/test-db

# Should show:
# "database_file": "/data/registration_submissions.db" (not /app/)
```

### Step 3: Data Migration Tools (Ready to Use)

Once volume is configured, use these automated migration tools:

**A. Export Staging Data:**
```bash
# Get all staging registrations as JSON:
curl https://camppowerup-staging.up.railway.app/admin/export-json > staging_registrations.json

# Verify export:
curl https://camppowerup-staging.up.railway.app/test-db | jq .total_registrations
```

**B. Import to Production:**
```bash
# Upload to production (after volume setup):
curl -X POST https://camppowerup-registration.up.railway.app/admin/import-json \
  -H "Content-Type: application/json" \
  -d @staging_registrations.json

# Verify import success:
curl https://camppowerup-registration.up.railway.app/test-db | jq .total_registrations
```

**C. Test Data Persistence:**
```bash
# Before: Check current count
curl https://camppowerup-registration.up.railway.app/test-db | jq .total_registrations

# Trigger deployment (should NOT lose data):
git push origin main

# After: Verify data survived
curl https://camppowerup-registration.up.railway.app/test-db | jq .total_registrations
```

## WHY STAGING WORKS
- Staging has persistent volume at `/data`  
- Database survives deployments
- Registration data remains intact

## WHY PRODUCTION FAILS  
- No persistent volume configured
- Database at `/app/registration_submissions.db` (ephemeral)
- Gets wiped every deployment
- Registration IDs survive (in Railway's internal system) but data is gone

## VERIFICATION COMMANDS
```bash
# Check production database status:
curl https://camppowerup-registration.up.railway.app/test-db

# Check staging database status:  
curl https://camppowerup-staging.up.railway.app/test-db

# Debug specific registration:
curl https://camppowerup-registration.up.railway.app/debug-registration/REG_20251002_07A3B4BD
```

## IMMEDIATE ACTION NEEDED
1. **Configure persistent volume for production Railway project**
2. **Redeploy production with volume mount**
3. **Test registration flow end-to-end**
4. **Verify data persistence after redeployment**

This is the EXACT reason why production confirmation pages are empty while staging works perfectly.