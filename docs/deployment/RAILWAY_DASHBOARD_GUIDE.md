# 🚂 Railway Dashboard Setup Guide

## **Step-by-Step PostgreSQL Configuration**

This guide shows you EXACTLY what to look for and click in the Railway dashboard to add PostgreSQL to your project.

---

## **Step 1: Access Railway Dashboard**

1. **Open your browser** and go to: https://railway.app/dashboard
2. **Login** with your Railway account credentials
3. **Look for your project** - it should be named something like:
   - `camppowerup-registration`
   - `camp-power-up`
   - `registration-form`

---

## **Step 2: Identify Current Services**

When you open your project, you should see a visual layout with service boxes:

### **✅ What You Currently Have:**
```
┌─────────────────────────┐
│  📱 App Service         │
│  camppowerup-registration│
│  Status: ✅ Deployed    │
│  URL: https://...       │
└─────────────────────────┘
```

### **❌ What You're Missing:**
```
┌─────────────────────────┐
│  🗄️  PostgreSQL         │
│  DATABASE SERVICE       │
│  Status: NOT EXISTS     │
│  This is the problem!   │
└─────────────────────────┘
```

---

## **Step 3: Add PostgreSQL Service**

### **Visual Indicators to Look For:**

1. **Find the "New" Button:**
   - Usually located in the **top-right corner**
   - Might say "New Service", "Add Service", or just "New"
   - Color: Usually **purple** or **blue**

2. **Click "New" → See Dropdown Menu:**
   ```
   ┌─────────────────┐
   │ 📱 App          │
   │ 🗄️  Database     │  ← Click this!
   │ 🔧 Plugin       │
   │ 📦 Volume       │
   └─────────────────┘
   ```

3. **Select Database → PostgreSQL:**
   ```
   ┌──────────────────┐
   │ 🐘 PostgreSQL    │  ← Click this!
   │ 🍃 MongoDB       │
   │ 🔴 Redis         │
   │ 🗄️  MySQL        │
   └──────────────────┘
   ```

---

## **Step 4: PostgreSQL Service Creation**

After clicking "Add PostgreSQL", you'll see:

### **During Setup (1-2 minutes):**
```
┌─────────────────────────┐
│  🗄️  PostgreSQL         │
│  Status: 🔄 Deploying   │
│  Please wait...         │
└─────────────────────────┘
```

### **After Successful Setup:**
```
┌─────────────────────────┐
│  🗄️  PostgreSQL         │
│  Status: ✅ Deployed    │
│  DATABASE_URL: Available │
└─────────────────────────┘
```

---

## **Step 5: Verify Configuration**

### **Your Project Should Now Look Like:**
```
┌─────────────────────────┐    ┌─────────────────────────┐
│  📱 App Service         │    │  🗄️  PostgreSQL         │
│  camppowerup-registration│    │  postgres-database      │
│  Status: ✅ Deployed    │    │  Status: ✅ Deployed    │
│  URL: https://...       │    │  DATABASE_URL: Set      │
└─────────────────────────┘    └─────────────────────────┘
                │                              │
                └──── Connected via DATABASE_URL ────┘
```

### **Important Visual Cues:**
- **Both services** should show **green checkmarks** ✅
- **App service** might show "Redeploying" after PostgreSQL is added
- **PostgreSQL service** should have connection details available

---

## **Step 6: Check Environment Variables**

1. **Click on your App Service** (not the PostgreSQL service)
2. **Look for "Variables" or "Environment" tab**
3. **You should see:**
   ```
   DATABASE_URL = postgresql://username:password@host:port/database
   ```
4. **If DATABASE_URL is missing:**
   - Click "Add Variable" or "Connect Database"
   - Railway should auto-connect them

---

## **Step 7: Test the Fix**

After PostgreSQL is added and connected:

### **Method 1: Run Our Diagnostic Script**
```bash
cd /Users/tevinfowler/Documents/CampPowerUp
python registration_form/railway_diagnostics.py
```

### **Method 2: Check Database Endpoint**
```bash
curl "https://camppowerup-registration.up.railway.app/test-db"
```

### **Expected Result:**
```json
{
  "database_type": "PostgreSQL",
  "environment": "production", 
  "success": true
}
```

---

## **Common Issues & Solutions**

### **Issue: "New" Button Not Visible**
- **Solution:** Make sure you're **inside your project**, not on the main dashboard
- **Look for:** Project name at the top of the page

### **Issue: PostgreSQL Option Missing**
- **Solution:** Try "Database" → "Add Database" → "PostgreSQL"
- **Alternative:** Look for "Add Service" instead of "New"

### **Issue: Services Not Connecting**
- **Solution:** Click PostgreSQL service → "Connect" → Select your app
- **Auto-connect:** Railway usually does this automatically

### **Issue: App Still Using SQLite**
- **Solution:** App needs to redeploy after DATABASE_URL is set
- **Manual trigger:** In app service, click "Deploy" or "Redeploy"

---

## **Visual Troubleshooting**

### **✅ Success Indicators:**
- Two services visible in project dashboard
- Both services show green "Deployed" status  
- DATABASE_URL appears in app environment variables
- Test endpoint returns "PostgreSQL"

### **❌ Problem Indicators:**
- Only one service (just the app) visible
- App service has no DATABASE_URL variable
- Test endpoint returns "SQLite"
- Registration form still gives 400 errors

---

## **Need More Help?**

If you're still having trouble:

1. **Take screenshots** of your Railway dashboard
2. **Run the diagnostic script** and share the output
3. **Check the Railway logs** for any deployment errors
4. **Verify your Railway plan** supports PostgreSQL databases

The diagnostic script will tell us exactly what's missing! 🚂