# Railway Database Setup for Camp Power-Up

## 🔥 CRITICAL: Data Persistence Issue Fixed

### The Problem
Railway deployments use ephemeral filesystems, which means:
- ❌ SQLite databases get wiped on every deployment
- ❌ All new registrations would be lost
- ❌ Only historical data (deployed with code) would persist

### The Solution
**PostgreSQL Database Service on Railway**

## 🚀 Railway Setup Instructions

### Step 1: Add PostgreSQL Service
1. Go to your Railway project dashboard
2. Click "New Service" → "Database" → "PostgreSQL"
3. Railway will automatically create a `DATABASE_URL` environment variable

### Step 2: Verify Environment Variables
Make sure you have these set in Railway:
```
DATABASE_URL=postgresql://... (automatically set by Railway)
CAMP_EMAIL=camppowerup2025@gmail.com
CAMP_EMAIL_PASSWORD=rtwpafmyjnjwylic
SMTP_SERVER=smtp.gmail.com
FLASK_ENV=production
DEBUG=false
```

### Step 3: Deploy
```bash
git push origin main
```

## 🔧 How It Works

### Local Development (SQLite)
- Uses `registration_submissions.db` for new registrations
- Uses `camp_power_up.db` for historical data
- Data stored in local files

### Production (PostgreSQL)
- Uses Railway PostgreSQL for new registrations
- Historical data loaded from deployed SQLite files
- **Data persists across all deployments** 🎉

### Automatic Detection
The app automatically detects the environment:
- If `DATABASE_URL` exists → Use PostgreSQL (Railway)
- If not → Use SQLite (Local development)

## 📊 Database Schema

### New Registrations Table (PostgreSQL)
Stores all new camp registrations with full form data, persists forever.

### Historical Data Access
Historical data is read from the deployed SQLite files but new data goes to PostgreSQL.

## 🧪 Testing Database Setup

Visit: `https://your-app.railway.app/admin/database-info`

Should show:
```json
{
  "database_type": "PostgreSQL",
  "is_production": true,
  "persistence": "Persistent (PostgreSQL)"
}
```

## ✅ Benefits

1. **Data Safety**: New registrations never lost
2. **Zero Downtime**: Deployments don't affect data
3. **Scalability**: PostgreSQL handles concurrent users
4. **Backup**: Railway manages database backups
5. **Performance**: Better than SQLite for web apps

## 🆘 Troubleshooting

### If registrations aren't persisting:
1. Check Railway PostgreSQL service is running
2. Verify `DATABASE_URL` environment variable exists
3. Check app logs for PostgreSQL connection errors

### Local development issues:
1. Make sure you're in the right directory
2. SQLite files should exist locally
3. Check file permissions

---

**Result**: Your camp registration system is now production-ready with persistent data storage! 🏕️