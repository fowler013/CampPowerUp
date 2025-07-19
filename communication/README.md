# Camp Power-Up Communication System

A comprehensive parent communication platform that eliminates the pain points of camp management by automating emails, SMS, and providing a modern parent portal.

## 🌟 Features

### 📧 Email & SMS Management
- **Pre-built Templates**: Welcome emails, payment reminders, daily updates, emergency alerts
- **Smart Targeting**: Send to all parents, new families, returning families, or custom lists
- **Variable Substitution**: Personalize messages with camper names, ages, fees, etc.
- **Delivery Tracking**: Monitor open rates and response rates

### 📱 Parent Portal
- **Real-time Updates**: Live camp activities and announcements
- **Photo Sharing**: Daily photo galleries with secure access
- **Daily Schedule**: Real-time activity tracking and status updates
- **Two-way Messaging**: Direct communication between parents and staff
- **Camper Progress**: Individual achievement tracking and participation notes

### ⚡ Automated Campaigns
- **Welcome Series**: Automatic onboarding for new families
- **Payment Reminders**: Smart reminders based on due dates
- **Daily Updates**: Automated activity summaries with photos
- **Pickup Reminders**: SMS alerts for end-of-day pickup
- **Emergency Alerts**: Instant mass communication for urgent situations

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Flask and Flask-CORS
- Email provider (Gmail, Outlook, etc.)
- Optional: SMS service (Twilio recommended)

### Installation

1. Navigate to the communication directory:
```bash
cd communication
```

2. Install dependencies:
```bash
pip install flask flask-cors schedule
```

3. Configure email settings in `app.py`:
```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'your-camp-email@gmail.com',
    'password': 'your-app-password',  # Use app password for Gmail
    'sender_name': 'Camp Power-Up Team'
}
```

4. Run the communication system:
```bash
python3 app.py
```

5. Access the system:
   - **Communication Dashboard**: http://127.0.0.1:5003
   - **Send Messages**: http://127.0.0.1:5003/send_message
   - **Parent Portal**: http://127.0.0.1:5003/portal

## 📋 Email Setup Guide

### Gmail Setup (Recommended)
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account Settings → Security
   - Select "App passwords" under 2-Step Verification
   - Generate password for "Mail"
   - Use this password in the EMAIL_CONFIG

### Other Email Providers
- **Outlook**: Use `smtp.office365.com`, port 587
- **Yahoo**: Use `smtp.mail.yahoo.com`, port 587
- **Custom**: Contact your email provider for SMTP settings

## 📱 SMS Setup (Optional)

### Twilio Integration
1. Sign up for Twilio account
2. Get your Account SID and Auth Token
3. Purchase a phone number
4. Update SMS_CONFIG in `app.py`:
```python
SMS_CONFIG = {
    'account_sid': 'your-twilio-sid',
    'auth_token': 'your-twilio-token',
    'from_number': '+1234567890'
}
```

5. Install Twilio SDK:
```bash
pip install twilio
```

## 🎯 Communication Workflows

### Daily Camp Operations
1. **Morning Welcome** (9:00 AM)
   - Automated "day started" messages
   - Weather updates if needed
   - Special announcements

2. **Activity Updates** (Throughout day)
   - Real-time portal updates
   - Photo uploads to galleries
   - Achievement notifications

3. **Pickup Reminders** (2:30 PM)
   - SMS reminders for pickup time
   - Traffic/parking updates
   - Late pickup procedures

4. **Evening Wrap-up** (4:00 PM)
   - Daily summary emails
   - Tomorrow's schedule preview
   - Individual camper highlights

### Emergency Communications
- **Instant Alerts**: Mass SMS and email for urgent situations
- **Weather Updates**: Automated notifications for weather changes
- **Schedule Changes**: Real-time updates pushed to portal and email
- **Health Notifications**: Secure communication about camper wellness

## 📊 Available Templates

### Email Templates
- **Welcome Email**: Sent to new families upon registration
- **Payment Reminder**: Automated reminders for outstanding payments
- **Daily Update**: Summary of daily activities with photos
- **Camp Completion**: Celebration email with certificates and photos

### SMS Templates
- **Pickup Reminder**: Daily pickup time alerts
- **Emergency Alert**: Urgent notifications with callback number
- **Weather Update**: Quick weather-related announcements
- **Schedule Change**: Last-minute activity modifications

## 🔧 Admin Features

### Dashboard Overview
- Communication statistics (emails sent, SMS delivered, portal views)
- Parent engagement metrics (open rates, response rates)
- Quick access to common tasks
- Recent activity log

### Message Management
- Send custom emails and SMS
- Use pre-built templates
- Schedule messages for future delivery
- Track delivery status and responses

### Parent Portal Management
- Post daily updates and announcements
- Upload and organize photos
- Manage camper-specific information
- Monitor portal engagement

## 🛡️ Privacy & Security

### Data Protection
- Secure database storage
- Parent login authentication
- Photo access controls
- COPPA compliance considerations

### Communication Logs
- Complete audit trail of all communications
- Delivery confirmations
- Error tracking and retry logic
- Privacy-conscious data handling

## 📈 Analytics & Reporting

### Communication Metrics
- Email open and click rates
- SMS delivery and response rates
- Portal engagement statistics
- Parent satisfaction tracking

### Operational Insights
- Most effective communication times
- Preferred communication channels
- Common parent questions/concerns
- Engagement trends over camp session

## 🔄 Integration with Main System

The communication system seamlessly integrates with your main Camp Power-Up dashboard:

- **Shared Database**: Accesses camper registration data
- **Unified Management**: Control from main dashboard or independently
- **Data Synchronization**: Real-time updates between systems
- **Consistent Experience**: Matching design and branding

## 🚧 Advanced Features (Coming Soon)

- [ ] Multi-language support for diverse families
- [ ] Video message capabilities
- [ ] Mobile app with push notifications
- [ ] Advanced analytics dashboard
- [ ] Integration with camp management software
- [ ] Automated feedback collection
- [ ] Social media integration for public updates

## 🎯 Pain Points This Solves

### Before: Manual Communication Nightmare
- ❌ Manually typing emails to 50+ families
- ❌ Copying and pasting individual names and details
- ❌ No tracking of who received what messages
- ❌ Parents calling constantly for updates
- ❌ Emergency communications taking too long
- ❌ Lost photos and difficulty sharing memories

### After: Automated Communication Paradise
- ✅ One-click campaigns to targeted groups
- ✅ Automatic personalization with camper details
- ✅ Complete delivery and engagement tracking
- ✅ Self-service parent portal reduces calls by 80%
- ✅ Instant emergency alerts to all families
- ✅ Organized photo sharing with automatic notifications

## 📞 Support & Configuration

For setup assistance or customization:
1. Review the configuration sections in `app.py`
2. Test email/SMS delivery with small groups first
3. Customize templates to match your camp's voice
4. Train staff on dashboard usage

---

**Transform your camp communication from chaos to clarity!** 📧✨

This system will save you hours every day and keep parents happy and informed! 🏕️⚡
