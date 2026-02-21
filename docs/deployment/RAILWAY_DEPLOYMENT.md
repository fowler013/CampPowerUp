# 🚀 Railway Deployment Guide for Camp Power-Up

## Overview
This guide covers deploying Camp Power-Up to Railway with both **Staging** and **Production** environments.

## 📋 Pre-Deployment Checklist

### ✅ Files Ready for Deployment
- `railway.json` - Railway configuration with environment-specific settings
- `requirements.txt` - Python dependencies including PostgreSQL support
- `start_production.sh` - Production startup script with Gunicorn
- `.env.production.example` - Production environment variables template
- `.env.staging.example` - Staging environment variables template
- `registration_form/db_config.py` - Database configuration utility

## 🔧 Railway Setup

### 1. Environment Configuration

#### Production Environment Variables:
```bash
# Security
SECRET_KEY=your_super_secret_production_key_32_chars_minimum
FLASK_ENV=production
DEBUG=false

# Database (Auto-configured by Railway)
DATABASE_URL=postgresql://... (automatically set)

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
CAMP_EMAIL=camppowerup2025@gmail.com
CAMP_EMAIL_PASSWORD=your_gmail_app_password
SENDER_NAME=Camp Power-Up

# Admin
ADMIN_USERNAME=campadmin
ADMIN_PASSWORD=your_secure_production_password

# Features
USE_TLS=true
ENABLE_EMAIL_NOTIFICATIONS=true
```

#### Staging Environment Variables:
```bash
# Security
SECRET_KEY=different_staging_secret_key
FLASK_ENV=staging
DEBUG=true

# Email (Optional - can disable for testing)
CAMP_EMAIL=camppowerup2025+staging@gmail.com
ENABLE_EMAIL_NOTIFICATIONS=false

# Admin
ADMIN_USERNAME=stagingadmin
ADMIN_PASSWORD=staging_password
```

### 2. Database Setup

Railway will automatically:
- ✅ Provision PostgreSQL database
- ✅ Set `DATABASE_URL` environment variable
- ✅ Handle database backups and scaling

### 3. Deployment Process

1. **Push to GitHub**: Ensure latest code is pushed
2. **Railway Auto-Deploy**: Railway will automatically deploy when you push to main branch
3. **Environment Variables**: Set the variables above in Railway dashboard
4. **Custom Domains**: Configure your domains in Railway settings

## 🔍 Monitoring & Logs

### Check Deployment Status:
- Railway Dashboard → Your Project → Deployments
- View real-time logs during deployment
- Monitor resource usage and performance

### Log Monitoring:
```bash
# Railway CLI (if installed)
railway logs --environment production
railway logs --environment staging
```

## 🚨 Security Considerations

### Production Security:
- ✅ Strong SECRET_KEY (32+ characters)
- ✅ Secure admin credentials  
- ✅ Gmail App Password (not regular password)
- ✅ HTTPS enabled (Railway provides this)
- ✅ Environment variables (never commit secrets)

### Database Security:
- ✅ PostgreSQL with encrypted connections
- ✅ Railway manages database security
- ✅ Regular automated backups

## 📊 Performance Optimization

### Production Settings:
- **Gunicorn**: 2 workers for production
- **Timeout**: 300 seconds for large operations
- **Logging**: Info level for production
- **Health Checks**: Configured for Railway load balancer

### Staging Settings:
- **Gunicorn**: 1 worker with reload for testing
- **Logging**: Debug level for troubleshooting
- **Features**: Some features disabled for testing

## 🔄 Environment Promotion

To promote staging to production:
1. Test thoroughly in staging
2. Update production environment variables if needed
3. Deploy to production branch/environment
4. Monitor deployment and test critical paths

## 🆘 Troubleshooting

### Common Issues:
1. **Database Connection**: Check DATABASE_URL is set
2. **Email Issues**: Verify Gmail App Password and SMTP settings
3. **Port Issues**: Railway automatically sets PORT environment variable
4. **Static Files**: Ensure templates and static files are properly referenced

### Debug Commands:
```bash
# Check environment
railway run env

# Test database connection
railway run python registration_form/db_config.py

# Check service health
curl https://your-app.railway.app/
```

## 📞 Support

### Railway Resources:
- [Railway Documentation](https://docs.railway.app/)
- [Railway Community](https://community.railway.app/)
- [Railway Status](https://status.railway.app/)

### Application Support:
- Check application logs in Railway dashboard
- Verify environment variables are set correctly
- Test database connectivity and email configuration

---

## 🎯 Quick Deploy Checklist

- [ ] Set all environment variables in Railway dashboard
- [ ] Configure Gmail App Password for email functionality
- [ ] Test staging environment thoroughly
- [ ] Deploy to production
- [ ] Verify all services are working (registration, admin, email)
- [ ] Set up monitoring and alerting
- [ ] Configure custom domain (if needed)

Your Camp Power-Up system is now ready for production deployment on Railway! 🏕️