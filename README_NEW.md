# Camp Power-Up Registration System

A professional event registration and management system built with Flask, applying software engineering best practices from UAT coursework.

## 🎯 Project Overview
Complete registration system for Camp Power-Up Nintendo Switch gaming camp with:
- Online registration with payment tracking
- Admin dashboard with CRUD operations
- Daily attendance check-in system
- Historical camper database
- Email notifications via SendGrid
- Fraud prevention for returning camper discounts

## 🏗️ Architecture
Built using MVC architecture with separation of concerns:
- **Models**: Database entities and business logic
- **Views**: HTML templates with Jinja2
- **Controllers**: Flask routes and request handlers
- **Services**: Business logic layer
- **Security**: Defense-in-depth implementation (CYBV 301)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (production) or SQLite (development)
- SendGrid API key for emails

### Installation
```bash
# Clone repository
git clone <repository-url>
cd CampPowerUp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/database/init_db.py

# Run development server
python app.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/security/
```

## 📁 Project Structure
```
CampPowerUp/
├── src/                  # Application source code
│   ├── registration/     # Registration module
│   ├── admin/            # Admin dashboard
│   ├── attendance/       # Attendance tracking
│   └── shared/           # Shared utilities
├── tests/                # Test suites
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── infrastructure/       # IaC and deployment
└── requirements/         # Dependencies
```

## 🔐 Security Features (CYBV 301 Principles)
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF token implementation
- Rate limiting
- Secure session management
- Audit logging
- Password hashing with bcrypt

## 📊 Database Schema (APCV 360 Design)
- **registrations**: Camper registration data
- **attendance**: Daily check-in tracking
- **users**: Admin authentication
- **audit_log**: Security audit trail

## 🚢 Deployment

### Development
```bash
python app.py
```

### Production (Railway)
```bash
# Automatic deployment via GitHub integration
git push origin main
```

### Docker
```bash
docker-compose up
```

## 📖 Documentation
- [Architecture Guide](docs/architecture/README.md)
- [Deployment Guide](docs/deployment/README.md)
- [Security Guide](docs/security/README.md)
- [API Documentation](docs/api/README.md)

## 🧪 Testing Strategy (CYBV 302)
- **Unit Tests**: Individual component testing
- **Integration Tests**: Module interaction testing
- **Security Tests**: Vulnerability scanning
- **Performance Tests**: Load and stress testing

## 🤖 AI Integration
Managed by Kit AI bot for:
- Automated issue tracking
- PR reviews and merging
- Code quality checks
- Documentation generation
- Deployment automation

## 📈 Monitoring & Logging
- Application logs: `logs/app.log`
- Error tracking: Sentry integration
- Performance monitoring: Railway metrics
- Security audit logs: `logs/security.log`

## 🔄 CI/CD Pipeline
- **GitHub Actions**: Automated testing
- **Railway**: Automatic deployment
- **Code Quality**: Automated linting and formatting
- **Security Scanning**: Dependency vulnerability checks

## 🛠️ Development Tools
- **Testing**: pytest, pytest-cov
- **Linting**: pylint, flake8
- **Formatting**: black, isort
- **Type Checking**: mypy
- **Security**: bandit, safety

## 📝 Contributing
1. Create feature branch: `git checkout -b feature/name`
2. Make changes following code standards
3. Write tests for new features
4. Run test suite: `pytest`
5. Submit pull request

## 📜 License
Proprietary - Camp Power-Up 2025

## 👥 Team
- **Developer**: Tevin Fowler
- **AI Assistant**: GitHub Copilot
- **Project Management**: Kit AI Bot

## 📞 Support
- Email: camppowerup2025@gmail.com
- Issues: GitHub Issues
- Docs: `/docs` directory

---
**Applying CS Principles from:**
- CYBV 301: Cybersecurity Fundamentals
- CYBV 302: System Integration
- CYBV 303: Windows Security
- APCV 360: Database Design
- CYBV 326: Network Security
- CYBV 381: Incident Response
