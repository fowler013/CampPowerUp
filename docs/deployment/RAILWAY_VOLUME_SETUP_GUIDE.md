# 🚨 RAILWAY DATABASE PERSISTENCE SETUP GUIDE

## The Problem
Railway deployments use **ephemeral storage** - each deployment creates a fresh container with a clean filesystem. This means:
- SQLite databases are wiped with every deployment
- User registration data disappears
- Confirmation pages show empty data

## The Solution: Railway Volumes

### Step 1: Create Railway Volume
1. Go to your Railway project dashboard
2. Click **"+ New"** → **"Volume"**
3. Name it: `camp-data`
4. Size: `1GB` (more than enough for SQLite)
5. Click **"Create Volume"**

### Step 2: Mount Volume to Service
1. Go to your **camppowerup-registration** service
2. Click **"Settings"** tab
3. Scroll to **"Volume Mounts"**
4. Click **"+ Mount Volume"**
5. Select: `camp-data`
6. Mount Path: `/app/data`
7. Click **"Save"**

### Step 3: Verify Environment Variables
Your service should have:
- `FLASK_ENV=production`
- `DEBUG=false`

### Step 4: Redeploy
After mounting the volume, trigger a new deployment:
- Any git push will redeploy with persistent storage
- Database will now persist between deployments

## Current Code Status
✅ **Railway-aware database path** already implemented
✅ **Auto-creates `/app/data` directory** when on Railway
✅ **Graceful fallback** for missing registrations
✅ **Professional confirmation pages** ready

## What Happens After Volume Setup
1. **New registrations** will be stored in persistent database
2. **Confirmation pages** will show complete data
3. **Data survives** deployments and restarts
4. **Admin dashboard** will maintain registration history

## Alternative: PostgreSQL Database
Instead of SQLite + Volume, you can:
1. Add **PostgreSQL** service to Railway project
2. Set `DATABASE_URL` environment variable
3. Code will automatically detect and use PostgreSQL

## Test After Setup
1. Create a test registration
2. Check confirmation page shows complete data
3. Redeploy the service
4. Verify registration data still exists

**This will permanently solve the empty confirmation pages!**