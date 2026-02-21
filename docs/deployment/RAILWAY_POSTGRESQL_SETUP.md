# 🚂 Railway PostgreSQL Setup Guide

## **The Problem**
The 400 error on form submissions is caused by Railway running in SQLite mode instead of PostgreSQL mode. This causes:
- ❌ Non-persistent data (lost on deployments)
- ❌ Database connection issues with concurrent users
- ❌ Form validation failures
- ❌ Admin dashboard showing empty data

## **The Solution: Add PostgreSQL Database**

### **Step 1: Add PostgreSQL Service**

1. **Visit Railway Dashboard:**
   - Go to https://railway.app/dashboard
   - Select your `CampPowerUp` project

2. **Add Database Service:**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will create a new PostgreSQL service
   - Wait for it to deploy (takes 1-2 minutes)

3. **Verify Database Created:**
   - You should see a new "PostgreSQL" service in your project
   - Click on it to see connection details

### **Step 2: Connect App to Database**

The DATABASE_URL should automatically be available to your app service. If not:

1. **Get Database URL:**
   - Click on your PostgreSQL service
   - Go to "Connect" tab
   - Copy the "DATABASE_URL" value

2. **Set Environment Variable (if needed):**
   - Click on your main app service
   - Go to "Variables" tab
   - Add: `DATABASE_URL` = (the copied value)

### **Step 3: Verify Connection**

After deployment completes:

1. **Test Database Connection:**
   ```bash
   curl https://camppowerup-registration.up.railway.app/test-db
   ```
   
   Should return:
   ```json
   {
     "success": true,
     "database_type": "PostgreSQL",
     "environment": "production",
     "registrations_count": 0
   }
   ```

2. **Test Registration Form:**
   - Visit: https://camppowerup-registration.up.railway.app/
   - Submit a test registration
   - Should succeed without 400 error

### **Step 4: Migration (Optional)**

If you want to migrate existing local data:

1. **Export Local Data:**
   ```bash
   cd registration_form
   python -c "
   import sqlite3, json
   conn = sqlite3.connect('registration_submissions.db')
   cursor = conn.cursor()
   cursor.execute('SELECT * FROM registrations')
   rows = cursor.fetchall()
   columns = [desc[0] for desc in cursor.description]
   data = [dict(zip(columns, row)) for row in rows]
   with open('local_registrations_backup.json', 'w') as f:
       json.dump(data, f, indent=2)
   print(f'Exported {len(data)} registrations')
   "
   ```

2. **Import to PostgreSQL** (via admin dashboard after setup)

## **Expected Changes After Setup**

✅ **Form Submissions Work:** No more 400 errors  
✅ **Data Persists:** Registrations survive deployments  
✅ **Admin Dashboard Shows Data:** Total registered count works  
✅ **Better Performance:** PostgreSQL handles concurrent users  
✅ **Backup System Works:** Daily backups can run on Railway  

## **Troubleshooting**

**If test-db still shows SQLite:**
- Check that DATABASE_URL is set in app service variables
- Redeploy the app service after adding PostgreSQL
- Check Railway logs for connection errors

**If connection fails:**
- Verify PostgreSQL service is running (green status)
- Check that both services are in same Railway project
- Try redeploying both services

**If 400 errors persist:**
- Check Railway logs: `railway logs`
- Verify form data validation
- Test with simple registration first

## **Railway CLI (Optional)**

For advanced users:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Check services
railway status

# View logs
railway logs

# Set variables
railway variables set DATABASE_URL=postgresql://...
```

## **Next Steps After Setup**

1. ✅ Verify PostgreSQL connection works
2. 🧪 Test registration form thoroughly  
3. 🔧 Run admin dashboard tests
4. 📊 Enable backup system on Railway
5. 🚀 Merge this branch to main