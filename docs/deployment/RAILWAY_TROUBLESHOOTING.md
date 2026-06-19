# Railway Deployment Troubleshooting Guide

## ✅ PORT Issue Fixed

The `$PORT is not a valid port number` error has been resolved by:
- ✅ Updated Procfile to use gunicorn properly
- ✅ Simplified railway.json configuration  
- ✅ Removed conflicting PORT configurations
- ✅ App code already handles PORT environment variable correctly

## 🚀 Railway Deployment Steps

### 1. **Connect GitHub Repository**
1. Go to Railway dashboard: https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `CampPowerUp` repository
4. Railway will automatically detect and deploy

### 2. **Set Required Environment Variables**
In Railway dashboard → Project Settings → Variables:

```bash
# Required for security
SECRET_KEY=your-super-secure-32-char-random-string
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-admin-password

# Required for email functionality  
CAMP_EMAIL=camppowerup2025@gmail.com
CAMP_EMAIL_PASSWORD=your-gmail-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Production settings
FLASK_ENV=production
DEBUG=false
```

### 3. **Add PostgreSQL Database**
1. In Railway dashboard → "Add Service" → "Database" → "PostgreSQL"
2. Railway will automatically set `DATABASE_URL` environment variable
3. Set `REGISTRATION_DATABASE_URL` to the same value as `DATABASE_URL`

## 🐛 Common Issues & Solutions

### **Issue: App not starting**
**Solution**: Check Railway logs:
- Go to Railway dashboard → Your project → Deployments → Click latest
- Check "Build Logs" and "Deploy Logs" for errors

### **Issue: Database connection errors**
**Solution**: Verify PostgreSQL service is running:
- Ensure PostgreSQL service is added to your project
- Check that `DATABASE_URL` environment variable is set
- Verify database migration completed

### **Issue: Email not working**
**Solution**: Check email configuration:
- Verify `CAMP_EMAIL_PASSWORD` is a Gmail App Password (not regular password)
- Test Gmail SMTP connection using local diagnostic script
- Check Railway logs for email-related errors

### **Issue: Admin login not working**
**Solution**: Verify admin credentials:
- Ensure `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set in Railway
- Try default credentials if env vars not working: `campadmin` / `PowerUp2025!`
- Check Railway logs for authentication errors

## 📋 Railway Configuration Files

### **Procfile** (Primary deployment method)
```
web: python -m gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 registration_form.app:app
```

### **railway.json** (Simplified configuration)
```json
{
  "build": {
    "builder": "NIXPACKS"  
  },
  "environments": {
    "production": {
      "variables": {
        "FLASK_ENV": "production",
        "DEBUG": "false"
      }
    }
  }
}
```

## 🔧 Alternative Deployment Commands

If Railway Procfile doesn't work, try these in Railway settings:

### **Option 1: Direct gunicorn**
```bash
python -m gunicorn --bind 0.0.0.0:$PORT --workers 2 registration_form.app:app
```

### **Option 2: Using startup script**
```bash
./start_railway.sh
```

### **Option 3: Direct Python (fallback)**
```bash
cd registration_form && python app.py
```

## 📊 Health Check

Railway will automatically check `http://your-app.railway.app/` for health status.
- ✅ Returns 200 OK = App is healthy
- ❌ Returns error = App has issues

## 🎯 Success Indicators

Your deployment is successful when you can:
- ✅ Access registration form at: `https://your-app.railway.app/`
- ✅ Login to admin dashboard at: `https://your-app.railway.app/admin`
- ✅ Submit test registration and receive email confirmation
- ✅ View registrations in admin dashboard

## 🆘 Getting Help

1. **Check Railway Logs**: Most issues show up in deployment logs
2. **Test Locally First**: Make sure app works locally before deploying
3. **Verify Environment Variables**: Double-check all required vars are set
4. **Check Database**: Ensure PostgreSQL service is running and connected

---

**Your Camp Power-Up app is now ready for Railway deployment! 🚀**