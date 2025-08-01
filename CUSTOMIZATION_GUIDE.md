# 🏕️ Camp Power-Up Customization Guide

## 🎨 **COMPLETE CAMP CUSTOMIZATION WALKTHROUGH**

This guide shows you how to customize every aspect of Camp Power-Up for your specific camp's needs, branding, and requirements.

---

## 📋 **TABLE OF CONTENTS**

1. [Camp Branding & Identity](#-camp-branding--identity)
2. [Registration Form Customization](#-registration-form-customization)
3. [Communication Templates](#-communication-templates)
4. [Game Library & Activities](#-game-library--activities)
5. [Admin Settings & Configuration](#-admin-settings--configuration)
6. [Security & Access Control](#-security--access-control)
7. [Database Customization](#-database-customization)
8. [Email & SMS Setup](#-email--sms-setup)
9. [Advanced Customization](#-advanced-customization)

---

## 🎨 **CAMP BRANDING & IDENTITY**

### **1. Update Camp Name & Logo**

**File:** `camp_config.py`
```python
# Change these to match your camp
CAMP_NAME = "Your Camp Name Here"
CAMP_TAGLINE = "Your Camp's Mission Statement"
CAMP_LOGO_URL = "/static/images/your-logo.png"
CAMP_COLORS = {
    'primary': '#2E7D32',      # Main green
    'secondary': '#FFA726',    # Orange accent
    'background': '#F5F5F5',   # Light background
    'text': '#212121'          # Dark text
}
```

**File:** `working_admin.py` (Lines 15-20)
```python
# Update the admin portal branding
CAMP_BRANDING = {
    'name': 'Your Camp Name',
    'subtitle': 'Administrative Portal',
    'year': '2025',
    'theme_color': '#2E7D32'
}
```

### **2. Custom CSS Styling**

**File:** `registration_form/static/css/style.css`
- Update colors, fonts, and layout
- Add your camp's visual identity
- Customize button styles and form appearance

**File:** `templates/` (All HTML files)
- Update headers and footers
- Add your camp logo
- Customize navigation and layout

---

## 📝 **REGISTRATION FORM CUSTOMIZATION**

### **3. Registration Fields**

**File:** `registration_form/app.py`

**Add Custom Fields:**
```python
# Around line 50, add new fields to the registration form
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Add your custom fields here
        dietary_restrictions = request.form.get('dietary_restrictions', '')
        emergency_contact_2 = request.form.get('emergency_contact_2', '')
        medical_conditions = request.form.get('medical_conditions', '')
        swimming_ability = request.form.get('swimming_ability', '')
        
        # Add to database insertion
```

**File:** `registration_form/templates/registration_form.html`
```html
<!-- Add custom form fields around line 80 -->
<div class="form-group">
    <label for="dietary_restrictions">Dietary Restrictions:</label>
    <textarea name="dietary_restrictions" class="form-control" rows="3"></textarea>
</div>

<div class="form-group">
    <label for="swimming_ability">Swimming Ability:</label>
    <select name="swimming_ability" class="form-control">
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
    </select>
</div>
```

### **4. Age Groups & Sessions**

**File:** `camp_config.py`
```python
# Customize age groups and sessions
AGE_GROUPS = {
    'little_explorers': {'min_age': 4, 'max_age': 6, 'name': 'Little Explorers'},
    'junior_adventurers': {'min_age': 7, 'max_age': 9, 'name': 'Junior Adventurers'},
    'senior_scouts': {'min_age': 10, 'max_age': 12, 'name': 'Senior Scouts'},
    'teen_leaders': {'min_age': 13, 'max_age': 15, 'name': 'Teen Leaders'}
}

CAMP_SESSIONS = {
    'session_1': {'dates': 'June 15-19, 2025', 'theme': 'Nature Explorers'},
    'session_2': {'dates': 'June 22-26, 2025', 'theme': 'Adventure Week'},
    'session_3': {'dates': 'June 29-July 3, 2025', 'theme': 'STEM Camp'},
    'session_4': {'dates': 'July 6-10, 2025', 'theme': 'Arts & Crafts'}
}
```

---

## 📧 **COMMUNICATION TEMPLATES**

### **5. Email Templates**

**File:** `communication/templates/send_message.html`

**Welcome Email Template:**
```html
<!-- Customize around line 40 -->
<div class="email-template" id="welcome-template">
    <h3>Welcome to [Your Camp Name]!</h3>
    <p>Dear [Parent Name],</p>
    <p>We're excited to welcome [Camper Name] to our camp family!</p>
    
    <!-- Add your camp-specific welcome information -->
    <ul>
        <li>Camp starts at 9:00 AM sharp</li>
        <li>Please pack a lunch and water bottle</li>
        <li>Pickup is at 3:00 PM</li>
        <li>Don't forget sunscreen and a hat!</li>
    </ul>
    
    <p>Looking forward to an amazing summer!</p>
    <p>The [Your Camp Name] Team</p>
</div>
```

**SMS Templates:**
```javascript
// Add custom SMS templates
const smsTemplates = {
    'pickup_reminder': 'Hi! Just a reminder that pickup for [Camper Name] is at 3:00 PM today. Thanks!',
    'weather_update': 'Weather Alert: Camp activities may be moved indoors today. [Camper Name] should bring a light jacket.',
    'photo_ready': 'Great news! Today\'s camp photos featuring [Camper Name] are ready to view at [PhotoLink]'
};
```

---

## 🎮 **GAME LIBRARY & ACTIVITIES**

### **6. Custom Activities**

**File:** `game_library.py`

**Add Your Camp's Activities:**
```python
# Around line 30, add your custom activities
CUSTOM_ACTIVITIES = [
    {
        'name': 'Nature Scavenger Hunt',
        'age_group': 'all',
        'duration': 45,
        'materials': ['clipboards', 'pencils', 'collection bags'],
        'description': 'Explore nature and find items on our special list!'
    },
    {
        'name': 'Canoe Building Challenge',
        'age_group': 'senior',
        'duration': 90,
        'materials': ['cardboard', 'duct tape', 'plastic wrap'],
        'description': 'Build and test your own mini canoe!'
    }
]
```

**Activity Categories:**
```python
ACTIVITY_CATEGORIES = {
    'outdoor': 'Outdoor Adventures',
    'arts': 'Arts & Crafts',
    'sports': 'Sports & Games',
    'science': 'Science Experiments',
    'cooking': 'Cooking & Nutrition',
    'team_building': 'Team Building'
}
```

---

## ⚙️ **ADMIN SETTINGS & CONFIGURATION**

### **7. System Configuration**

**File:** `working_admin.py`

**Customize Admin Dashboard:**
```python
# Around line 200, customize dashboard modules
ADMIN_MODULES = {
    'communication': {
        'name': 'Communication Center',
        'icon': '📧',
        'description': 'Send emails and SMS to parents',
        'enabled': True
    },
    'registration': {
        'name': 'Registration Management',
        'icon': '📋',
        'description': 'Manage camper registrations',
        'enabled': True
    },
    'activities': {
        'name': 'Activity Planning',
        'icon': '🎮',
        'description': 'Plan and track camp activities',
        'enabled': True
    }
}
```

### **8. User Roles & Permissions**

**Create Custom User Roles:**
```python
# Add to security.py
USER_ROLES = {
    'super_admin': {
        'permissions': ['all'],
        'description': 'Full system access'
    },
    'camp_director': {
        'permissions': ['registration', 'communication', 'reports'],
        'description': 'Camp management access'
    },
    'counselor': {
        'permissions': ['activities', 'attendance'],
        'description': 'Activity and attendance access'
    }
}
```

---

## 🔒 **SECURITY & ACCESS CONTROL**

### **9. Password Policies**

**File:** `security.py`
```python
# Customize password requirements
PASSWORD_POLICY = {
    'min_length': 12,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_numbers': True,
    'require_symbols': True,
    'password_history': 5  # Remember last 5 passwords
}
```

### **10. Session Management**

```python
# Customize session timeout and security
SESSION_CONFIG = {
    'timeout_minutes': 30,
    'require_https': True,  # For production
    'secure_cookies': True,
    'auto_logout_warning': 5  # Minutes before logout
}
```

---

## 🗄️ **DATABASE CUSTOMIZATION**

### **11. Custom Database Fields**

**Registration Database:**
```sql
-- Add to registration database schema
ALTER TABLE registrations ADD COLUMN dietary_restrictions TEXT;
ALTER TABLE registrations ADD COLUMN swimming_ability TEXT;
ALTER TABLE registrations ADD COLUMN emergency_contact_2 TEXT;
ALTER TABLE registrations ADD COLUMN medical_conditions TEXT;
```

**Activity Tracking:**
```sql
-- Add activity tracking tables
CREATE TABLE activity_participation (
    id INTEGER PRIMARY KEY,
    camper_id INTEGER,
    activity_name TEXT,
    participation_date DATE,
    notes TEXT,
    FOREIGN KEY (camper_id) REFERENCES registrations (id)
);
```

---

## 📱 **EMAIL & SMS SETUP**

### **12. Email Configuration**

**File:** `.env` (Create this file for production)
```env
# Your camp's email settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_camp_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_camp_email@gmail.com
FROM_NAME=Your Camp Name

# SMS Settings (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### **13. Message Personalization**

```python
# Add to communication system
MESSAGE_VARIABLES = {
    '[CAMPER_NAME]': 'camper_first_name',
    '[PARENT_NAME]': 'parent_name',
    '[CAMP_NAME]': 'Your Camp Name',
    '[SESSION_DATES]': 'session_dates',
    '[PICKUP_TIME]': 'pickup_time',
    '[DROP_OFF_TIME]': 'drop_off_time'
}
```

---

## 🚀 **ADVANCED CUSTOMIZATION**

### **14. Custom Reports**

**Add to analytics system:**
```python
def generate_custom_report(report_type):
    if report_type == 'dietary_summary':
        # Generate dietary restrictions summary
        pass
    elif report_type == 'activity_participation':
        # Track activity participation rates
        pass
    elif report_type == 'age_group_analysis':
        # Analyze enrollment by age group
        pass
```

### **15. Integration with External Systems**

**Photo Sharing Integration:**
```python
# Add photo sharing capabilities
PHOTO_SERVICES = {
    'google_photos': {
        'api_key': 'your_api_key',
        'album_template': '[Camp Name] - [Session] - [Date]'
    }
}
```

**Payment Processing:**
```python
# Add payment integration
PAYMENT_CONFIG = {
    'stripe_public_key': 'your_stripe_public_key',
    'stripe_secret_key': 'your_stripe_secret_key',
    'camp_fees': {
        'full_session': 250.00,
        'half_session': 150.00,
        'late_fee': 25.00
    }
}
```

---

## 🎯 **QUICK START CUSTOMIZATION CHECKLIST**

### **Essential Customizations (30 minutes):**
- [ ] Update camp name in `camp_config.py`
- [ ] Change admin password in security settings
- [ ] Add your camp logo to `static/images/`
- [ ] Customize email templates
- [ ] Update registration form fields

### **Intermediate Customizations (2 hours):**
- [ ] Add custom activities to game library
- [ ] Configure email/SMS settings
- [ ] Customize CSS styling
- [ ] Add custom database fields
- [ ] Set up user roles

### **Advanced Customizations (1 day):**
- [ ] Implement payment processing
- [ ] Add photo sharing integration
- [ ] Create custom reports
- [ ] Set up backup systems
- [ ] Configure production deployment

---

## 💡 **CUSTOMIZATION TIPS**

1. **Always backup** your database before making changes
2. **Test customizations** in development before production
3. **Document changes** for future reference
4. **Use version control** to track modifications
5. **Start small** and gradually add features

---

## 🆘 **NEED HELP?**

If you need assistance with any customization:

1. **Check the logs** in the admin portal
2. **Review the database** for data structure
3. **Test changes incrementally**
4. **Keep backups** of working configurations

---

## 📞 **SUPPORT RESOURCES**

- **System Logs:** Check admin portal → Security → Audit Logs
- **Database Browser:** Use SQLite browser for database inspection
- **Configuration Files:** All settings in `camp_config.py` and `.env`
- **Documentation:** Check `UNIFIED_SYSTEM_GUIDE.md` for technical details

---

*Last Updated: July 31, 2025*
*Version: 2.0 - Complete Unified System*
