# 🏕️ Camp Power-Up Registration System

[![Deployment Status](https://img.shields.io/badge/status-live-brightgreen)](https://camppowerup-registration.up.railway.app/)
[![Railway Deploy](https://img.shields.io/badge/deploy-automatic-blue)](https://railway.app)

**🌐 Live Registration Form**: https://camppowerup-registration.up.railway.app/

**👨‍💻 Admin Dashboard**: https://camppowerup-registration.up.railway.app/admin

A modern, production-ready camp registration system with automatic deployment and comprehensive management tools.

## 🚀 **Live System Features**

### � **Registration Form** 
- **Mobile-Friendly Design**: Works perfectly on all devices
- **Real-time Validation**: Instant feedback for form fields
- **Automatic Data Storage**: Submissions saved to secure database
- **Parent-Friendly Interface**: Simple, intuitive camp registration
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

### Registration administration

The deployed entry point is `wsgi_railway:app`, which loads
`registration_form\app.py` and `registration_form\camp_config.py`. The similarly
named root dashboard and backup application files are not this registration service.

- Sign in at `/admin` using `ADMIN_USERNAME` (default `campadmin`) and the
  deployment's `ADMIN_PASSWORD`. Set a strong, stable `SECRET_KEY` shared by all
  workers. Change passwords through Railway Variables, not source code.
- Select the exact **Camp session** before reading counts or exporting records.
  November 23-24 and November 23-25, 2026 remain separate labels. Text search
  filters visible cards; it does not change the selected session's summary or export.
- **Mark fully paid** records an administrator's confirmation; it does not charge
  a payment method or track partial deposits. Payment reminders require working
  email-provider configuration and known session pricing. Delivery failures are
  reported rather than counted as successful sends.
- **Configuration** saves validated settings in the SQLite `camp_configurations`
  table. All workers read saved settings on each request. Stale editor saves are
  rejected. Changing a camp name or dates preserves existing registrations and
  their previous label's configuration; it does not merge or migrate registrations.
  Fee edits for an unchanged label affect that label's displayed fee estimates.
- Metrics include imported history only in the all-sessions view. Unknown
  historical prices are not replaced with today's fees. Estimated fees are not
  payments collected. Returning-camper verification matches imported historical
  records; an unmatched record is not proof of fraud.
- Historical import/repair tools are separate from everyday navigation. Repair
  only considers unassigned legacy records with exact name, email and original
  timestamp matches. Back up before importing, repairing, clearing history or
  deleting registrations.
- Mutating registration/configuration/history admin requests require a signed-in
  session and its CSRF token (hidden `csrf_token` for forms or `X-CSRF-Token` for
  JSON requests). Read-only `/admin/export-json` remains compatible with Kit;
  omitting `session` exports all non-historical registrations.

**Before deploying:** verify that the actual SQLite database resides on a mounted,
persistent Railway volume and take a consistent database backup. An environment
variable alone does not prove a volume is mounted. The full SQLite backup includes
both registrations and saved configuration; JSON registration exports do not include
configuration. Do not redeploy an ephemeral database without first preserving its
data. These code changes do not configure production storage or reset passwords.

### Isolated registration checks

Run from the repository root with its Python dependencies and `pytest` installed:

```powershell
python scripts\test\run_registration_tests.py
```

The runner uses a temporary working directory and synthetic databases, disables
Railway/SendGrid environment selection, and mocks outgoing emails. Do not import
the registration app from a directory containing a live database just to run tests:
the application initializes its database during import.

Optional browser checks use Python Playwright and a local-only server, never the
live registration site:

```powershell
python -m pip install playwright
python -m playwright install chromium
python scripts\test\run_registration_tests.py scripts\test\test_admin_browser.py
```

Alternatively, set `CAMP_BROWSER_CHANNEL=msedge` when testing with an installed
Microsoft Edge browser. `CAMP_UI_ARTIFACT_DIR` optionally captures synthetic UI
screenshots. The browser checks include desktop and narrow layouts, session
selection, search, administrative actions, configuration saves and form submission.

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

## 📈 Historical Statistics Example

These example counts are historical, not live registration totals. Use the
session-filtered admin dashboard for current records.

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

**Default Thanksgiving 2026 pricing (November 23-24):**
- **New Campers**: $100 total ($50 deposit and $50 final payment)
- **Returning Campers**: $80 total ($50 deposit and $30 final payment)
- **Final payment due**: November 22, 2026

Saved administrator configuration overrides these defaults. Other historical
session labels must have their own known pricing; do not apply these fees to them.

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
- **Camp League Plan**: `/docs/development/CAMP_LEAGUE_PROJECT_PLAN.md` - Minecraft and Pokémon league roadmap
- **Camp League Data**: `/camp_league.py` - reusable rules, scoring, themes, and gym definitions
- **Individual Component READMEs**: Component-specific documentation in each directory

## 🎮 Camp League Program Planning

The project now includes a reusable rules engine for the camp league build process:
- Minecraft Build Battle themes and rubric
- Survival Challenge objectives and scoring
- November 8-gym Pokémon pilot league
- March and June refinement and flagship model
- Award definitions and flagship camp schedule

This foundation supports the active November pilot and the later seasonal expansion phases without duplicating rules across documents.

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
