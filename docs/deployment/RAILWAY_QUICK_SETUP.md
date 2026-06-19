# 🚀 Railway PostgreSQL Quick Setup

## **TL;DR - Fix in 5 Minutes**

### **Problem:** Registration form gives 400 errors on Railway
### **Cause:** Railway using SQLite instead of PostgreSQL  
### **Solution:** Add PostgreSQL service to Railway project

---

## **🎯 Quick Fix Steps**

### **1. Confirm Issue**
```bash
python registration_form/railway_diagnostics.py
```
**Look for:** `❌ Database Type: SQLite` (this is the problem!)

### **2. Railway Dashboard**
1. Go to: **https://railway.app/dashboard**
2. Open your **Camp Power-Up project**
3. Click **"New"** → **"Database"** → **"Add PostgreSQL"** 
4. Wait 1-2 minutes for deployment

### **3. Verify Fix**
```bash
python registration_form/railway_diagnostics.py
```
**Look for:** `✅ Database Type: PostgreSQL` (fixed!)

---

## **🔍 What You Should See**

### **Before (Broken):**
```
┌─────────────────────────┐
│  📱 App Service         │    ← Only this exists
│  camppowerup-registration│
│  Status: ✅ Deployed    │
└─────────────────────────┘
```

### **After (Fixed):**
```
┌─────────────────────────┐    ┌─────────────────────────┐
│  📱 App Service         │    │  🗄️  PostgreSQL         │
│  Status: ✅ Deployed    │    │  Status: ✅ Deployed    │
└─────────────────────────┘    └─────────────────────────┘
```

---

## **📋 Troubleshooting**

### **Can't Find "New" Button?**
- Make sure you're **inside your project** (not on main dashboard)
- Look for project name at top: `camppowerup-registration`

### **No "Database" Option?**
- Try: **"Add Service"** → **"Database"** → **"PostgreSQL"**
- Or: **"+"** button → **"Database"**

### **PostgreSQL Added But Still SQLite?**
```bash
# Check if DATABASE_URL is set
python registration_form/database_url_troubleshooter.py
```

### **Still Getting 400 Errors?**
```bash
# Run full diagnostics
python registration_form/railway_diagnostics.py

# Test specific endpoint
curl https://camppowerup-registration.up.railway.app/test-db
```

---

## **🎉 Success Indicators**

✅ **Diagnostic shows:** `Database Type: PostgreSQL`  
✅ **Test endpoint returns:** `{"database_type": "PostgreSQL"}`  
✅ **Registration form works** without 400 errors  
✅ **Admin dashboard shows** persistent data  
✅ **All 4/4 tests pass** in staging suite  

---

## **📚 Detailed Guides**

- **Visual Dashboard Guide:** `RAILWAY_DASHBOARD_GUIDE.md`
- **Complete Setup:** `RAILWAY_POSTGRESQL_SETUP.md`  
- **Full PR Details:** `RAILWAY_POSTGRESQL_PR.md`

**Need help?** Run the diagnostics - they'll tell you exactly what's missing! 🚂