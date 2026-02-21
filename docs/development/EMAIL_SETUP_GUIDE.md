# 📧 Email Configuration Setup Guide

## Gmail Setup (Recommended)

### Step 1: Gmail Account Setup
1. **Use existing Gmail** or **create new account** for the camp:
   - Recommendation: `camppowerup2025@gmail.com` or similar
   - Keep credentials secure and separate from personal accounts

### Step 2: Enable App Passwords (Required for SMTP)
1. **Go to Google Account settings**: https://myaccount.google.com/
2. **Security** → **2-Step Verification** (must be enabled first)
3. **App passwords** → **Generate app password for "Mail"**
4. **Copy the generated password** (16 characters, like: `abcd efgh ijkl mnop`)

### Step 3: Update Configuration
Replace the EMAIL_CONFIG in `communication/app.py`:

```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'YOUR_CAMP_EMAIL@gmail.com',      # Replace with actual email
    'password': 'YOUR_APP_PASSWORD',           # Replace with 16-char app password
    'sender_name': 'Camp Power-Up Team'
}
```

### Step 4: Test Email Sending
We'll create a test script to verify email delivery works.

---

## Alternative: SendGrid Setup (Professional Option)

### Step 1: Create SendGrid Account
1. **Sign up**: https://sendgrid.com/free/
2. **Free tier**: 100 emails/day forever
3. **Verify your sender identity** (email address)

### Step 2: Get API Key
1. **Settings** → **API Keys** → **Create API Key**
2. **Full Access** or **Restricted** (with Mail Send permissions)
3. **Copy the API key** (starts with `SG.`)

### Step 3: Update Configuration for SendGrid
```python
# For SendGrid, we'd use their API instead of SMTP
SENDGRID_CONFIG = {
    'api_key': 'YOUR_SENDGRID_API_KEY',
    'from_email': 'camp@yourdomain.com',
    'sender_name': 'Camp Power-Up Team'
}
```

---

## Next Steps After Email Setup
1. **Update configuration** with real credentials
2. **Test email sending** with a simple test
3. **Send test email** to your own email address
4. **Verify delivery** and check spam folder
5. **Update camp staff** with new email address for communications

---

**Ready to proceed? Which email provider would you like to use?**
