# Camp Power-Up Registration Form

A modern, standalone registration form system for Camp Power-Up 2025 that integrates seamlessly with the main dashboard.

## 🌟 Features

- **Modern Design**: Mobile-friendly, responsive interface
- **Smart Validation**: Real-time form validation and error handling
- **Google Form Integration**: Based on the actual Google Form structure
- **Database Integration**: Syncs with main camp management system
- **Admin Dashboard**: View and manage all registrations
- **Payment Tracking**: Track payment status and generate reminders
- **Auto-calculations**: Automatic fee calculation for returning vs new campers

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Flask and Flask-CORS installed
- Main camp database accessible

### Installation & Running

1. Navigate to the registration form directory:
```bash
cd registration_form
```

2. Install dependencies (if not already installed):
```bash
pip install flask flask-cors
```

3. Run the application:
```bash
python3 app.py
```

4. Access the applications:
   - **Registration Form**: http://127.0.0.1:5001
   - **Admin Dashboard**: http://127.0.0.1:5001/admin

## 📋 Form Fields

The registration form captures the following information:

### Child Information
- Name (First & Last)
- Age and Grade
- Gaming preferences and behavior
- Special dietary restrictions
- Sensory processing needs

### Parent/Guardian Information
- Contact email and phone
- Emergency contact details
- Payment preferences

### Camp-Specific Information
- Returning camper status (affects pricing)
- Equipment needs (Nintendo Switch)
- Special accommodations
- Additional notes

## 🔧 Admin Features

### Dashboard Overview
- Total registration count
- Returning vs new camper breakdown
- Special needs tracking
- Equipment requirements

### Registration Management
- View all submissions with detailed information
- Search and filter capabilities
- Payment status tracking
- Email reminder system (coming soon)
- Data export functionality (coming soon)

## 💰 Pricing Structure

- **New Campers**: $200
- **Returning Campers**: $180

Fees are automatically calculated based on camper status.

## 🗄️ Database Structure

The registration form creates and maintains its own SQLite database (`registration_submissions.db`) while also syncing key data with the main camp management database.

### Registration Table Fields
- Submission ID (unique identifier)
- Timestamp
- Child and parent information
- Camp preferences and requirements
- Payment status
- Special needs and accommodations

## 🔄 Integration with Main Dashboard

The registration form is designed to work both as:

1. **Standalone Application**: Independent registration system
2. **Integrated Component**: Part of the main camp management dashboard

Data flows seamlessly between the registration system and the main dashboard for comprehensive camp management.

## 🛠️ Development

### File Structure
```
registration_form/
├── app.py                 # Main Flask application
├── templates/
│   ├── registration_form.html   # Main registration form
│   ├── confirmation.html        # Registration confirmation
│   └── admin_dashboard.html     # Admin interface
├── static/
│   └── (CSS, JS, images)
└── README.md             # This file
```

### Key Components

1. **app.py**: Core Flask application with routes and database logic
2. **registration_form.html**: Modern, responsive registration form
3. **admin_dashboard.html**: Comprehensive admin interface
4. **confirmation.html**: Registration success page

## 🔐 Security & Privacy

- Form validation on both client and server side
- Secure database storage
- Privacy-conscious data handling
- Integration with main camp security measures

## 🚧 Future Enhancements

- [ ] Email notification system
- [ ] Payment processing integration
- [ ] PDF receipt generation
- [ ] Advanced reporting features
- [ ] Real-time Google Forms sync
- [ ] Mobile app integration

## 📞 Support

For technical support or questions about the registration system, please contact the camp administration team.

---

**Camp Power-Up 2025** - Empowering young gamers through technology and community! 🎮⚡
