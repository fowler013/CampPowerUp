# Camp Power-Up Security Configuration

## ⚠️ CRITICAL: Environment Variables Required for Production

### Required Railway Environment Variables

When deploying to Railway, you **MUST** set these environment variables in the Railway dashboard:

#### **Authentication & Security**
```bash
SECRET_KEY=your-super-secure-random-string-here-at-least-32-chars
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-admin-password
```

#### **Email Configuration**
```bash
CAMP_EMAIL=your-camp-email@gmail.com
CAMP_EMAIL_PASSWORD=your-gmail-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

#### **Database (Railway will auto-provide PostgreSQL URL)**
```bash
# Railway automatically provides this when you add PostgreSQL service:
DATABASE_URL=postgresql://user:pass@host:port/dbname

# This can be the same as DATABASE_URL for simplicity:
REGISTRATION_DATABASE_URL=postgresql://user:pass@host:port/dbname
```

#### **Application Settings**
```bash
FLASK_ENV=production
DEBUG=False
PORT=5001
HOST=0.0.0.0
```

## 🔐 Security Measures Implemented

### 1. **No Hardcoded Credentials**
- ✅ All passwords, API keys, and secrets moved to environment variables
- ✅ Default values only for development, not production
- ✅ Gmail app password removed from diagnostic scripts

### 2. **Admin Authentication**
- ✅ Session-based authentication with secure cookies
- ✅ Admin credentials loaded from environment variables
- ✅ Login required for all admin functions

### 3. **Database Security**
- ✅ SQLite for local development
- ✅ PostgreSQL for production (Railway managed)
- ✅ No connection strings with embedded credentials in code

### 4. **Email Security**
- ✅ Gmail app passwords (not regular passwords)
- ✅ SMTP credentials in environment variables only

## 🚨 Pre-Deployment Security Checklist

Before deploying to Railway:

- [ ] Set all environment variables in Railway dashboard
- [ ] Generate a strong SECRET_KEY (32+ random characters)
- [ ] Set secure ADMIN_USERNAME and ADMIN_PASSWORD
- [ ] Configure Gmail app password for CAMP_EMAIL_PASSWORD
- [ ] Verify no .env files with real credentials are committed
- [ ] Confirm all secrets are in environment variables, not code

## 🛡️ Security Best Practices

### Gmail App Password Setup:
1. Go to Google Account settings
2. Enable 2-factor authentication
3. Generate an "App Password" for Gmail
4. Use this app password, not your regular Gmail password

### Strong SECRET_KEY Generation:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Secure Admin Credentials:
- Use a unique username (not "admin")
- Use a strong password with mixed case, numbers, symbols
- Consider using a password manager

## 🔍 Files Audited and Secured

- ✅ `/registration_form/app.py` - Admin credentials moved to env vars
- ✅ `/gmail_diagnostic.py` - Hardcoded password removed
- ✅ All `.env.*` files - Only contain example/test values
- ✅ Database connections - Use env vars for production
- ✅ Email configuration - All credentials from env vars

## ⚡ Quick Railway Deploy Commands

```bash
# 1. Commit security fixes
git add .
git commit -m "Security: Move all credentials to environment variables"
git push origin main

# 2. Deploy to Railway (after setting env vars in dashboard)
railway up --environment production
```

## 🆘 Security Issue Response

If you suspect a security issue:
1. Immediately rotate all passwords and API keys
2. Check Railway logs for suspicious activity
3. Update environment variables with new credentials
4. Review recent commits for any accidentally committed secrets

---

**✅ All security vulnerabilities have been identified and fixed. The system is now production-ready.**