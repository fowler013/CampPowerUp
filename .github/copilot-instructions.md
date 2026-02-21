# CampPowerUp - Copilot Instructions

## Build & Run Commands

```bash
# Setup virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run main dashboard
python app.py               # http://127.0.0.1:5000

# Run registration system
cd registration_form
python app.py               # http://127.0.0.1:5001

# Run all services
python scripts/setup/start_services.py

# Run tests
python -m pytest scripts/test/
python scripts/test/complete_system_test.py
```

## Project Structure

```
CampPowerUp/
├── app.py                  # Main Flask dashboard
├── config.py               # App configuration
├── camp_config.py          # Camp-specific settings
├── security.py             # Security utilities
├── *.py                    # Service modules (email, payment, game_library, etc.)
├── registration_form/      # Registration sub-app (separate Flask app)
│   ├── app.py              # Registration Flask app
│   └── templates/          # Registration templates
├── communication/          # Communication sub-app
├── templates/              # Main app templates
├── data/                   # CSV data files (gitignored)
├── docs/                   # Documentation
│   ├── deployment/         # Railway, Docker guides
│   ├── security/           # Security documentation
│   └── development/        # Dev guides, roadmaps
├── scripts/                # Utility scripts
│   ├── setup/              # Deploy, start, restore scripts
│   ├── debug/              # Diagnostic scripts
│   ├── test/               # Test scripts
│   └── archive/            # Old/backup files
└── config/                 # Config files (Docker, env templates, etc.)
```

## Architecture

CampPowerUp is a multi-service Flask application for camp registration management.

### Core Services

| File | Purpose |
|------|---------|
| `app.py` | Main dashboard - camper analytics, insights |
| `registration_form/app.py` | Registration system with fraud prevention |
| `communication/app.py` | Parent/camper communication tools |
| `game_library.py` | Game library management |
| `email_service.py` | Email notifications (SendGrid) |
| `payment_processor.py` | Payment handling |
| `security.py` | Authentication, CSRF, session management |

### Data Flow

1. **Registration**: Parent submits form → `registration_form/app.py` → SQLite DB
2. **Dashboard**: `app.py` reads from CSV + SQLite → renders analytics
3. **Admin**: `/admin` routes in registration app → verification workflows

### Database

- **Historical data**: `data/Camp_Power_Up_past_forms - Sheet1.csv`
- **New registrations**: `registration_form/registration_submissions.db` (SQLite)
- **Main DB**: `camp_power_up.db` (SQLite)
- **Production**: PostgreSQL on Railway

## Conventions

### Flask Patterns

- **Blueprints**: Not currently used (consider for future refactoring)
- **Templates**: Jinja2 in `templates/` directories
- **Static files**: `registration_form/static/`

### Security Patterns

```python
# CSRF protection
from security import csrf_protect
@app.route('/submit', methods=['POST'])
@csrf_protect
def submit():
    ...

# Session management
from flask import session
session['user_id'] = user.id
session.permanent = True
```

### Database Patterns

```python
# SQLite connection
import sqlite3
conn = sqlite3.connect('camp_power_up.db')
cursor = conn.cursor()
try:
    cursor.execute("SELECT * FROM campers")
    results = cursor.fetchall()
finally:
    conn.close()
```

### Configuration

```python
# camp_config.py - Camp-specific settings
CAMP_YEAR = 2025
PRICING = {
    'new_camper': 200,
    'returning_camper': 170
}

# config.py - Flask settings
SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
```

## Environment Variables

Required for production (Railway):
```
SECRET_KEY=...
DATABASE_URL=postgresql://...
SENDGRID_API_KEY=...
ADMIN_USERNAME=...
ADMIN_PASSWORD=...
```

## Deployment

- **Platform**: Railway (automatic deploys from main branch)
- **Production URL**: https://camppowerup-production.up.railway.app/
- **Config files**: `config/railway.json`, `config/Procfile`

```bash
# Local Docker testing
docker-compose -f config/docker-compose.yml up
```

## Key Features

### Fraud Prevention
The registration system validates "returning camper" claims against historical data.
- See `registration_form/app.py` for verification logic
- Admin tools at `/admin/verify-returning-campers`

### Analytics Dashboard
Main `app.py` provides:
- Age/grade distribution
- Game popularity analysis
- Special needs tracking
- Revenue metrics

## Related Repositories

- **Kit**: AI chatbot (Go) - could integrate for camp notifications
- **Scince**: Academic coursework - Python patterns reference

## Python Guidelines

Follow `docs/development/PYTHON_GUIDELINES.md` (if created) or these conventions:
- Use type hints for function signatures
- Docstrings for all public functions
- Error handling with try/except for DB operations
- Logging with descriptive messages
