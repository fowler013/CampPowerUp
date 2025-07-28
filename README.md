# 🏕️ Camp Power-Up Management System

A comprehensive camp management system for Camp Power-Up, featuring data analysis, registration processing, and fraud prevention capabilities.

## 🌟 System Components

### 📊 **Data Dashboard** (`/`)
- **Clean Data Processing**: Automatically removes duplicates and standardizes messy CSV data
- **Interactive Dashboard**: Beautiful web-based dashboard with charts and statistics
- **Game Analytics**: Analyzes favorite games and gaming behavior
- **Special Needs Tracking**: Highlights campers with allergies and sensory issues
- **Real-time Updates**: Live data processing and visualization

### 📝 **Registration System** (`/registration_form/`)
- **Modern Registration Form**: Mobile-friendly, responsive registration interface
- **Dynamic Pricing**: Automatic fee calculation for returning vs new campers
- **Real-time Validation**: Smart form validation and error handling
- **Admin Dashboard**: Comprehensive registration management interface
- **🛡️ Fraud Prevention**: Advanced verification system to prevent false returning camper claims

### 🛡️ **NEW: Fraud Prevention & Security**
- **Database Validation**: Automatically checks returning camper claims against historical data
- **Verification Fields**: Additional verification questions for returning campers
- **Admin Verification Tools**: Dedicated tools for reviewing suspicious registrations
- **Revenue Protection**: Prevents lost revenue from fraudulent discount claims
- **Manual Review System**: Streamlined process for handling edge cases

## 🎮 Key Insights & Analytics

The system provides insights into:
- Age and grade distribution
- Returning vs new campers with verification status
- Most popular games (Mario, Fortnite, Minecraft, etc.)
- Nintendo Switch ownership patterns
- Special dietary and sensory considerations
- Gaming behavior and social skills analysis
- **Revenue impact analysis** from pricing tiers and fraud prevention

## 🚀 Quick Start

### 📊 **Data Dashboard Setup**

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd CampPowerUp
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install flask pandas
   ```

4. **Run the main dashboard**
   ```bash
   python app.py
   ```
   View at: `http://127.0.0.1:5000`

### 📝 **Registration System Setup**

1. **Navigate to registration form**
   ```bash
   cd registration_form
   ```

2. **Run the registration system**
   ```bash
   python app.py
   ```

3. **Access the applications**
   - **Registration Form**: `http://127.0.0.1:5001`
   - **Admin Dashboard**: `http://127.0.0.1:5001/admin`
   - **🛡️ Fraud Verification**: `http://127.0.0.1:5001/admin/verify-returning-campers`

### 🛡️ **Fraud Prevention Features**

The system now includes comprehensive fraud prevention:
- **Automatic validation** of returning camper claims
- **Admin verification tools** for manual review
- **Revenue protection** from false discount claims
- **Detailed reporting** on verification status

## 📁 Project Structure

```
CampPowerUp/
├── app.py                      # Main Flask dashboard application
├── game_library.py             # Game library management system
├── camp_config.py              # Dynamic camp configuration
├── start_services.py           # Service startup script
├── templates/
│   ├── index.html              # Main dashboard template
│   └── game_library.html       # Game library interface
├── data/
│   └── *.csv                   # CSV data files (not tracked in git)
├── registration_form/          # Modern registration system
│   ├── app.py                  # Registration Flask application
│   ├── templates/
│   │   ├── registration_form.html
│   │   ├── admin_dashboard.html
│   │   └── confirmation.html
│   ├── REGISTRATION_GUIDE.md   # Registration management guide
│   ├── REGISTRATION_GUIDE_UPDATED.md  # Updated with fraud prevention
│   ├── update_database.py      # Database migration script
│   └── registration_submissions.db    # Registration database
├── communication/              # Communication system
│   └── app.py                  # Communication dashboard
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
├── CHANGELOG.md               # System version history and updates
└── README.md                  # This file
```

## 🛡️ Security & Fraud Prevention

### Problem Addressed
Some families may fraudulently claim "returning camper" status to receive discounted pricing, potentially causing significant revenue loss.

### Solution Implemented
- **Database Validation**: Automatic verification against previous registration records
- **Additional Verification**: Required fields for previous year, staff memories, and camp experiences
- **Admin Tools**: Dedicated verification dashboard for manual review
- **Clear Warnings**: User-facing messaging about verification requirements
- **Revenue Tracking**: Analytics showing potential revenue impact

### Admin Verification Process
1. Access verification tool: `http://localhost:5001/admin/verify-returning-campers`
2. Review flagged registrations requiring manual verification
3. Contact families to verify claims when necessary
4. Take appropriate action based on findings

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js
- **Data Processing**: Pandas
- **Database**: SQLite
- **Security**: Custom fraud prevention validation
- **Configuration**: Dynamic camp configuration system

## 📈 Current Statistics Overview

**Dashboard Insights:**
- 138 total campers (after deduplication)
- 65 returning campers (47% return rate)
- 14 campers with allergies
- 5 campers with sensory needs
- 97 campers bringing Nintendo Switch (70%)

**Registration System:**
- Real-time registration processing
- Fraud prevention verification active
- Revenue protection measures in place
- Admin verification tools operational

## 💰 Pricing & Revenue Protection

**Current Pricing Structure:**
- **New Campers**: $200 total
- **Returning Campers**: $170 total (15% discount)
- **Potential Savings from Fraud**: Up to $30 per false claim

**Revenue Protection Metrics:**
- Automatic validation prevents most fraudulent claims
- Admin tools identify edge cases requiring manual review
- System tracks potential revenue impact from discount abuse

## 🎯 Popular Games

Top games mentioned by campers:
1. Mario (15 mentions)
2. Fortnite (14 mentions) 
3. Minecraft (12 mentions)
4. Roblox (8 mentions)
5. Zelda (6 mentions)

## 🔧 Customization

The system is designed to be flexible:
- Modify game detection in `app.py` to track different games
- Update pricing in `camp_config.py` for different sessions
- Customize fraud prevention thresholds in registration system
- Adjust verification requirements based on camp needs

## 📚 Documentation

- **Main README**: This file - system overview and setup
- **Registration Guide**: `/registration_form/REGISTRATION_GUIDE.md` - comprehensive admin guide
- **Changelog**: `CHANGELOG.md` - version history and feature updates
- **Individual Component READMEs**: Component-specific documentation in each directory

## 🚀 Recent Updates (v2.1.0)

- **🛡️ Fraud Prevention System**: Comprehensive verification for returning camper claims
- **📊 Enhanced Analytics**: Revenue protection metrics and verification statistics  
- **🔧 Admin Tools**: Dedicated verification dashboard and workflow tools
- **📝 Documentation**: Updated guides with fraud prevention procedures

## 💡 Support & Contributing

For questions, issues, or contributions:
1. Check the documentation in each component directory
2. Review the changelog for recent updates
3. Test fraud prevention features in a development environment
4. Report issues with specific steps to reproduce

**Current Version**: 2.1.0 with Fraud Prevention  
**Last Updated**: July 28, 2025
- Update the HTML template for different styling
- Add new API endpoints for additional data analysis
- Extend the CSV processing for different data formats

## 📝 Data Privacy

This system processes camp registration data. Ensure you:
- Follow local data protection regulations
- Obtain proper consent for data processing
- Keep sensitive data secure
- Don't commit actual registration data to version control

## 🤝 Contributing

This is a camp management tool. Feel free to:
- Report issues
- Suggest improvements
- Add new features
- Improve documentation

## 📄 License

This project is for educational and camp management purposes.

---

**Built for Camp Power-Up 2025** 🎮✨
