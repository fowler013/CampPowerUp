# 🏕️ Camp Power-Up Complete System Management Guide

## 🌐 Live Systems & URLs

### **Production Deployment (Railway)**
- **🔗 Live Registration Form**: https://camppowerup-production.up.railway.app/
- **👨‍💻 Admin Dashboard**: https://camppowerup-production.up.railway.app/admin

### **Local Development Services**
All services are now running locally for development and testing:

| Service | Port | URL | Purpose | Status |
|---------|------|-----|---------|---------|
| **Main Dashboard** | 5000 | http://127.0.0.1:5000 | Data analytics and camper management | ✅ RUNNING |
| **Registration Form** | 5008 | http://127.0.0.1:5008 | Camp registration (Local testing) | ✅ RUNNING |
| **Communication System** | 5007 | http://127.0.0.1:5007 | Parent communication and messaging | ✅ RUNNING |
| **Admin Portal** | 5006 | http://127.0.0.1:5006/admin/login | Unified secure admin interface | ✅ RUNNING |
| **Game Library** | 5000 | http://127.0.0.1:5000 | Game library (integrated with dashboard) | ✅ RUNNING |

**🚀 Quick Start**: Run `./deploy_all_services.sh` to start all services at once!

---

## 🚀 Complete System Architecture

### **System Components**

#### 1. **📝 Registration System**
- **Files**: `registration_form/app.py`, templates, static files
- **Database**: `registration_form/registration_submissions.db`
- **Features**: Registration form, admin dashboard, fraud detection
- **Deployment**: ✅ **LIVE on Railway** (Auto-deploys from main branch)

#### 2. **📊 Main Dashboard**
- **Files**: `app.py`, `templates/index.html`, `templates/campers.html`
- **Database**: `camp_power_up.db` (combined historical + new data)
- **Features**: Analytics, camper data, interactive dashboards

#### 3. **📧 Communication System**
- **Files**: `communication/app.py`, templates
- **Database**: Uses main `camp_power_up.db`
- **Features**: Email/SMS, parent portal, templates, automated messaging

#### 4. **🔐 Admin Portal**
- **Files**: `working_admin.py`, security modules
- **Features**: Unified secure admin interface, user management, security

#### 5. **🎮 Game Library**
- **Files**: `game_library.py`, `game_library_service.py`
- **Features**: Game management, popularity tracking, web interface

#### 6. **🛡️ Security Layer**
- **Files**: `security.py`, `config.py`
- **Features**: Authentication, authorization, audit logging, encryption

---

## ⚡ Automatic Deployment Setup

### **Railway (Production) - Already Configured ✅**
- **Registration Form**: Auto-deploys on every `git push origin main`
- **Health Checks**: Automatic monitoring
- **Scaling**: Automatic based on demand

### **Setting Up Additional Services for Production**

Want to deploy the other services? Here's how:

#### **Option 1: Deploy Each Service Separately on Railway**
```bash
# Create separate Railway projects for each service
railway login
railway init  # For each service directory
railway up    # Deploy each service
```

#### **Option 2: Docker Compose (Already Configured)**
```bash
# Complete multi-service deployment
docker-compose up -d

# Services will be available at:
# - Admin: http://localhost:5002
# - Communication: http://localhost:5007  
# - Registration: http://localhost:5008
```

#### **Option 3: Production Server Deployment**
```bash
# Use the production deployment script
python3 deploy_production.py
```

---

## 🛠️ Local Development Workflow

### **Starting All Services Locally**
```bash
# Option 1: Use the master start script
python3 start_services.py

# Option 2: Use individual start commands (see sections below)

# Option 3: Use the production builder
python3 production_builder_clean.py
```

### **Individual Service Commands**

#### **Main Dashboard**
```bash
cd /Users/tevinfowler/Documents/CampPowerUp
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python app.py
# Access: http://127.0.0.1:5000
```

#### **Registration System**
```bash
cd registration_form
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python app.py
# Access: http://127.0.0.1:5008
# Admin: http://127.0.0.1:5008/admin
```

#### **Communication System**
```bash
cd communication
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python app.py
# Access: http://127.0.0.1:5007
# Admin: http://127.0.0.1:5007/admin/login
```

#### **Secure Admin Portal**
```bash
cd /Users/tevinfowler/Documents/CampPowerUp
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python working_admin.py
# Access: http://127.0.0.1:5006/admin/login
# Default: admin / camp2024power (change on first login)
```

#### **Game Library Service**
```bash
cd /Users/tevinfowler/Documents/CampPowerUp
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python game_library_service.py
# Access: http://127.0.0.1:5000
```

---

## 🔄 Deployment Workflows

### **Quick Deploy to Railway (Registration Form)**
```bash
# Any changes to registration form auto-deploy
git add .
git commit -m "Update registration form"
git push origin main
# ✅ Live in 2-3 minutes at https://camppowerup-production.up.railway.app/
```

### **Deploy All Services to Production**
```bash
# Use the automated deployment script
./deploy.sh

# Or manually:
git add .
git commit -m "Update all services"
git push origin main

# Then run production deployment
python3 deploy_production.py
```

### **Development Testing**
```bash
# Check all services status
python3 check_status.py

# Start all services for testing
python3 start_services.py

# Run complete system test
python3 complete_system_test.py
```

---

## 📊 System Monitoring & Management

### **Check Registration Status**
```bash
# Latest registrations
cd registration_form
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('registration_submissions.db')
cursor = conn.cursor()
cursor.execute('SELECT child_first_name, child_last_name, parent_email, timestamp FROM registrations ORDER BY timestamp DESC LIMIT 10')
for row in cursor.fetchall():
    print(f'{row[0]} {row[1]} ({row[2]}) - {row[3]}')
conn.close()
"
```

### **System Health Check**
```bash
# Check all services
python3 check_status.py

# Check specific service
curl -I http://127.0.0.1:5000/  # Main dashboard
curl -I http://127.0.0.1:5007/  # Communication
curl -I http://127.0.0.1:5008/  # Registration
```

### **Database Management**
```bash
# Backup all databases
cp camp_power_up.db "backup_main_$(date +%Y%m%d).db"
cp registration_form/registration_submissions.db "backup_reg_$(date +%Y%m%d).db"
cp communication/communication.db "backup_comm_$(date +%Y%m%d).db"

# Check database sizes and record counts
python3 -c "
import sqlite3, os
for db in ['camp_power_up.db', 'registration_form/registration_submissions.db', 'communication/communication.db']:
    if os.path.exists(db):
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
        tables = cursor.fetchall()
        print(f'\\n{db}:')
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
            count = cursor.fetchone()[0]
            print(f'  {table[0]}: {count} records')
        conn.close()
"
```

---

## 🔐 Security Management

### **Admin Access**
- **Registration Admin**: https://camppowerup-production.up.railway.app/admin (Production)
- **Local Admin Portal**: http://127.0.0.1:5006/admin/login
- **Communication Admin**: http://127.0.0.1:5007/admin/login

### **Default Credentials** (Change immediately)
```
Username: admin
Password: camp2024power
```

### **Security Features**
- ✅ Password hashing with bcrypt
- ✅ Session management
- ✅ CSRF protection
- ✅ Rate limiting
- ✅ Audit logging
- ✅ Role-based access control

---

## 🚨 Troubleshooting

### **Service Won't Start**
```bash
# Check if port is in use
lsof -i :5000  # Replace with service port
lsof -ti :5000 | xargs kill -9  # Kill if needed

# Check Python path
which python3
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python --version
```

### **Database Issues**
```bash
# Reinitialize databases if corrupted
python3 -c "
import sqlite3
conn = sqlite3.connect('camp_power_up.db')
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
print('Main DB integrity:', cursor.fetchone()[0])
conn.close()
"
```

### **Railway Deployment Issues**
1. Check Railway dashboard: https://railway.app
2. View build logs for errors
3. Verify environment variables are set
4. Test locally first: `python3 registration_form/app.py`

---

## 📁 File Structure Overview

```
CampPowerUp/
├── 🚀 DEPLOYED TO RAILWAY
│   ├── registration_form/app.py     # ✅ LIVE Registration Form
│   ├── Dockerfile                   # Container configuration
│   ├── Procfile                     # Railway startup
│   ├── railway.json                 # Deployment settings
│   └── requirements.txt             # Dependencies
│
├── 📊 LOCAL SERVICES
│   ├── app.py                      # Main dashboard
│   ├── working_admin.py            # Admin portal
│   ├── communication/app.py        # Communication system
│   ├── game_library_service.py     # Game library
│   └── security.py                 # Security layer
│
├── 🛠️ MANAGEMENT TOOLS
│   ├── deploy.sh                   # Deployment script
│   ├── check_status.py             # Status checker
│   ├── start_services.py           # Service starter
│   └── production_builder_clean.py # Production setup
│
└── 📚 DOCUMENTATION
    ├── WEBSITE_MANAGEMENT_GUIDE.md  # This file
    ├── SECURITY_GUIDE.md            # Security docs
    └── Various service READMEs      # Individual service docs
```

---

## 🎯 Quick Commands Reference

```bash
# 🚀 Deploy Registration Form to Railway
git push origin main

# 🏃 Start All Local Services  
python3 start_services.py

# 🔍 Check System Status
python3 check_status.py

# 💾 Backup Databases
./backup_databases.sh

# 🔐 Access Admin Portals
# Registration: https://camppowerup-production.up.railway.app/admin
# Local Admin: http://127.0.0.1:5006/admin/login
# Communication: http://127.0.0.1:5007/admin/login

# 📊 View Latest Registrations
cd registration_form && python3 -c "import sqlite3; conn=sqlite3.connect('registration_submissions.db'); [print(f'{row[0]} {row[1]} - {row[3]}') for row in conn.execute('SELECT child_first_name, child_last_name, parent_email, timestamp FROM registrations ORDER BY timestamp DESC LIMIT 5').fetchall()]"
```

---

**🎉 Your complete Camp Power-Up system is now fully documented and ready for production!**

- ✅ **Registration Form**: Live on Railway with auto-deployment
- ✅ **All Services**: Documented and ready to deploy
- ✅ **Management Tools**: Scripts for easy maintenance
- ✅ **Security**: Comprehensive protection implemented
- ✅ **Monitoring**: Health checks and status monitoring