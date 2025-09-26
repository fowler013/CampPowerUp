# Railway Deployment Guide

## Problem: Pandas Build Issues
pandas has compilation issues on Railway with Python 3.13. We have two solutions:

### Solution 1: Minimal Deployment (Recommended for MVP)
Use `requirements-railway.txt` which excludes pandas. This means:
- Historical CSV import won't work on Railway
- New registrations via forms will still work perfectly
- Admin dashboard will work with current database data

### Solution 2: Add pandas later (if needed)
After successful Railway deployment, if you need CSV import functionality:
1. Try adding: `pandas==1.5.3` (older, more stable version)
2. Use Railway's build environment variables if needed

## Quick Railway Deploy Steps:

1. **Copy minimal requirements**:
   ```bash
   cp requirements-railway.txt requirements.txt
   ```

2. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Minimal requirements for Railway deployment"
   git push origin main
   ```

3. **Deploy on Railway**:
   - Connect your GitHub repo
   - Railway will auto-detect Python app
   - Uses `runtime.txt` (Python 3.11.9)
   - Uses PostgreSQL database (not SQLite)

4. **Test basic functionality**:
   - Registration form should work
   - Admin dashboard should show new registrations
   - Historical CSV data won't be available (acceptable for MVP)

## Production Database Setup:
Railway will provision PostgreSQL automatically. Your app will use the `DATABASE_URL` environment variable.

## Files Ready for Railway:
- ✅ `runtime.txt` - Python 3.11.9
- ✅ `requirements-railway.txt` - Minimal dependencies
- ✅ `Procfile` - Gunicorn configuration
- ✅ `railway.json` - Railway configuration
- ✅ `migrate_database.py` - Database migration script
- ✅ `.env.production` - Production environment template

The app is ready to deploy to Railway with basic functionality!