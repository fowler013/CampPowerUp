# 🏕️ Camp Power-Up Registration System - Management Guide

## 🌐 Live Website
- **Registration Form**: https://camppowerup-production.up.railway.app/
- **Admin Dashboard**: https://camppowerup-production.up.railway.app/admin

---

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Automatic Deployment](#automatic-deployment)
- [Managing Registrations](#managing-registrations)
- [Making Updates](#making-updates)
- [Database Management](#database-management)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

---

## 🚀 Quick Start

### Accessing Your Admin Dashboard
1. Go to: https://camppowerup-production.up.railway.app/admin
2. View all camp registrations
3. Export data as needed
4. Monitor new submissions in real-time

### Sharing the Registration Form
Send parents this link: **https://camppowerup-production.up.railway.app/**

---

## ⚡ Automatic Deployment

**✅ Already Configured!** Your website automatically deploys when you push to GitHub:

### How It Works
1. You make changes to code locally
2. Commit and push to `main` branch: `git push origin main`
3. Railway automatically detects changes
4. Website rebuilds and deploys (usually 2-3 minutes)
5. Changes go live immediately

### Monitoring Deployments
- **Railway Dashboard**: https://railway.app → Your Project
- **Build Logs**: Check for any deployment issues
- **Live Status**: Verify website is running

---

## 📊 Managing Registrations

### Viewing Submissions
```bash
# From your local terminal, check latest registrations:
cd /Users/tevinfowler/Documents/CampPowerUp/registration_form
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('registration_submissions.db')
cursor = conn.cursor()
cursor.execute('SELECT child_first_name, child_last_name, parent_email, timestamp FROM registrations ORDER BY timestamp DESC LIMIT 10')
rows = cursor.fetchall()
print('Latest registrations:')
for i, row in enumerate(rows, 1):
    print(f'  {i}. {row[0]} {row[1]} ({row[2]}) - {row[3]}')
conn.close()
"
```

### Admin Dashboard Features
- **View All Registrations**: Complete list with search/filter
- **Registration Details**: Full information for each camper
- **Export Data**: Download registrations as CSV/JSON
- **Real-time Updates**: New submissions appear automatically

---

## 🛠️ Making Updates

### Code Changes Workflow
```bash
# 1. Navigate to your project
cd /Users/tevinfowler/Documents/CampPowerUp

# 2. Make your changes (edit files as needed)

# 3. Test locally first
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python registration_form/app.py

# 4. Commit and push changes
git add .
git commit -m "Description of your changes"
git push origin main

# 5. Website automatically deploys in 2-3 minutes!
```

### Common Updates

#### Update Registration Form Fields
- **File**: `registration_form/templates/registration_form.html`
- **Add/modify**: Form fields, validation, styling
- **Deploy**: Push changes, form updates automatically

#### Modify Admin Dashboard
- **File**: `registration_form/templates/admin_dashboard.html`
- **Update**: Display columns, styling, functionality
- **Deploy**: Changes go live on next push

#### Adjust App Settings
- **File**: `registration_form/app.py`
- **Modify**: Database schema, routing, business logic
- **Deploy**: Automatic deployment after push

---

## 💾 Database Management

### Database Location
- **Production**: Managed by Railway (persistent storage)
- **Local Development**: `registration_form/registration_submissions.db`

### Backup Registrations
```bash
# Create backup of local database
cp registration_form/registration_submissions.db "backup_$(date +%Y%m%d).db"
```

### View Database Schema
```bash
cd /Users/tevinfowler/Documents/CampPowerUp
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('registration_form/registration_submissions.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(registrations)')
columns = cursor.fetchall()
print('Database Schema:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')
conn.close()
"
```

---

## 🚨 Troubleshooting

### Website Not Loading
1. **Check Railway Status**: https://railway.app → Your Project
2. **View Logs**: Look for error messages in Railway dashboard
3. **Verify URL**: Ensure using correct https://camppowerup-production.up.railway.app/

### Deployment Failed
1. **Check Git Push**: Verify changes were pushed to main branch
2. **Review Build Logs**: Railway dashboard shows build errors
3. **Test Locally**: Run `python registration_form/app.py` locally first

### Registration Form Issues
```bash
# Test form locally
cd /Users/tevinfowler/Documents/CampPowerUp
PORT=8080 /Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python registration_form/app.py
# Visit: http://localhost:8080
```

### Admin Dashboard Not Working
- **URL**: Ensure using `/admin` endpoint
- **Clear Cache**: Hard refresh browser (Cmd+Shift+R)
- **Check Logs**: Railway dashboard for server errors

### Database Issues
```bash
# Reinitialize local database if corrupted
cd registration_form
rm registration_submissions.db
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python app.py
```

---

## 🔧 Technical Details

### Project Structure
```
CampPowerUp/
├── registration_form/          # Main application
│   ├── app.py                 # Flask application
│   ├── templates/             # HTML templates
│   │   ├── registration_form.html
│   │   └── admin_dashboard.html
│   ├── static/css/style.css   # Styling
│   └── registration_submissions.db
├── Dockerfile                 # Container configuration
├── Procfile                   # Railway startup command
├── railway.json              # Railway deployment settings
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### Deployment Configuration
- **Platform**: Railway (https://railway.app)
- **Runtime**: Python 3.11
- **Database**: SQLite (persistent storage)
- **Auto-Deploy**: GitHub main branch
- **Health Check**: `/` endpoint

### Environment Variables
Railway automatically sets:
- `PORT`: Application port (usually 8080)
- Other Railway-specific variables

### Key Files for Management
- **`registration_form/app.py`**: Main application logic
- **`railway.json`**: Deployment configuration
- **`Procfile`**: Startup command
- **`requirements.txt`**: Dependencies

---

## 📞 Quick Reference

### Important URLs
- **Live Site**: https://camppowerup-production.up.railway.app/
- **Admin Dashboard**: https://camppowerup-production.up.railway.app/admin
- **Railway Dashboard**: https://railway.app
- **GitHub Repo**: https://github.com/fowler013/CampPowerUp

### Key Commands
```bash
# Deploy changes
git push origin main

# Test locally  
python registration_form/app.py

# Check registrations
# (See "Managing Registrations" section above)
```

### Support
- **Railway Docs**: https://docs.railway.app
- **Flask Docs**: https://flask.palletsprojects.com
- **SQLite Docs**: https://sqlite.org/docs.html

---

**🎉 Your Camp Power-Up registration system is now live and automatically managed!**

Every time you push changes to GitHub, Railway automatically deploys them to your live website. The system is designed to be reliable, scalable, and easy to maintain.