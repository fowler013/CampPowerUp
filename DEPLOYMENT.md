# Camp Power-Up Deployment Guide 🏕️

This guide will help you deploy Camp Power-Up to a production environment where parents can access the registration form.

## Quick Start Options

### Option 1: Railway (Easiest - Recommended for beginners)
1. Go to [Railway.app](https://railway.app) and sign up
2. Click "Deploy from GitHub repo"
3. Connect your GitHub account and select this repository
4. Railway will automatically detect and deploy your app
5. Add environment variables in Railway dashboard
6. Your app will be live at: `https://your-app-name.railway.app`

### Option 2: DigitalOcean App Platform
1. Go to [DigitalOcean](https://www.digitalocean.com/products/app-platform)
2. Create new app from GitHub repository
3. Configure environment variables
4. Deploy with managed database

### Option 3: Local Docker (For testing)
```bash
# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start with Docker
docker-compose up -d

# Your app will be at http://localhost:5002
```

## Environment Variables Setup

Copy `.env.production` to `.env` and configure:

### Required Settings:
- `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
- `DATABASE_URL`: Your PostgreSQL connection string
- `MAIL_USERNAME` & `MAIL_PASSWORD`: Gmail app password for notifications

### Optional Settings:
- `ADMIN_EMAIL`: Your admin email
- `CAMP_NAME`: Your camp name
- `CAMP_YEAR`: Camp year

## Database Migration

If you have existing SQLite data:

```bash
# Set production database URL
export PRODUCTION_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Run migration
python migrate_database.py
```

## SSL/HTTPS Setup

### For Railway/DigitalOcean:
- SSL is automatic and included

### For custom servers:
1. Get SSL certificate (Let's Encrypt recommended)
2. Configure web server (Nginx/Apache)
3. Set `HTTPS_ONLY=True` in environment

## Custom Domain

### Railway:
1. Go to app settings → Custom Domain
2. Add your domain (e.g., `camppowerup.com`)
3. Update DNS records as instructed

### DigitalOcean:
1. Go to Apps → Settings → Domains
2. Add custom domain
3. Update DNS records

## Email Setup (Gmail)

1. Enable 2-factor authentication on Gmail
2. Generate app password: Google Account → Security → App passwords
3. Use app password (not regular password) in `MAIL_PASSWORD`

## Post-Deployment Checklist

- [ ] App loads successfully
- [ ] Registration form works
- [ ] Admin panel accessible
- [ ] Email notifications working
- [ ] SSL certificate active
- [ ] Custom domain working (if applicable)
- [ ] Database backups configured

## Sharing the Registration Form

Once deployed, share this URL with parents:
- **Registration Form:** `https://your-domain.com` (port 5008 in local)
- **Admin Dashboard:** `https://your-domain.com/admin`

## Troubleshooting

### Common Issues:

1. **Database Connection Error**
   - Check `DATABASE_URL` format
   - Verify database credentials
   - Ensure database is running

2. **Email Not Working**
   - Verify Gmail app password
   - Check `MAIL_USERNAME` is full email
   - Ensure 2FA is enabled on Gmail

3. **App Won't Start**
   - Check logs for specific error
   - Verify all required environment variables
   - Check Python version compatibility

## Support

For deployment help, check:
1. Railway Documentation: https://docs.railway.app
2. DigitalOcean App Platform: https://docs.digitalocean.com/products/app-platform/
3. Flask Deployment: https://flask.palletsprojects.com/en/3.0.x/deploying/

## Estimated Costs

- **Railway**: $5/month (includes database)
- **DigitalOcean**: $12/month (app + database)
- **Custom Domain**: $10-15/year

Choose the option that best fits your technical comfort level and budget!