# CampPowerUp - Nintendo Switch Gaming Camp Registration

[![CI Pipeline](https://github.com/fowler013/CampPowerUp/actions/workflows/ci.yml/badge.svg)](https://github.com/fowler013/CampPowerUp/actions/workflows/ci.yml)
[![Deploy](https://github.com/fowler013/CampPowerUp/actions/workflows/deploy.yml/badge.svg)](https://github.com/fowler013/CampPowerUp/actions/workflows/deploy.yml)
[![Test Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](./htmlcov/index.html)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎮 About

Professional registration and management system for Camp Power Up - a Nintendo Switch gaming summer camp for kids aged 6-12. Built with Flask, applying computer science principles from college coursework (CYBV 301, APCV 360, CYBV 302).

**Production**: https://camppowerup-registration.up.railway.app  
**Staging**: https://camppowerup-staging.up.railway.app

## ✨ Features

- 📝 **Online Registration** - Parent registration with payment integration
- 👨‍💼 **Admin Dashboard** - Manage registrations, payments, attendance
- 📊 **Attendance Tracking** - Daily check-in system for Nov 24-25 camp
- 💳 **Payment Management** - Track payment status and generate receipts
- 📧 **Email Notifications** - Automated confirmation and receipt emails
- 🎮 **Game Library** - Nintendo Switch game catalog for camp activities
- 💬 **Parent Communication** - Message system for parent-admin communication

## 🏗️ Architecture

Built using **MVC pattern** with modern software engineering practices:

```
CampPowerUp/
├── src/                    # Application code (NEW - Phase 2)
│   ├── config/            # ✅ Configuration management (CYBV 301, APCV 360)
│   ├── shared/            # ✅ Shared utilities (database, auth, email)
│   ├── registration/      # Registration module
│   ├── admin/             # Admin dashboard
│   ├── attendance/        # Attendance tracking
│   └── communication/     # Parent communication
├── tests/                 # Testing framework (CYBV 302)
│   ├── unit/             # Unit tests (80%+ coverage target)
│   ├── integration/      # Integration tests
│   └── security/         # Security tests (CYBV 301)
├── docs/                  # Documentation
├── scripts/               # ✅ Database backup/restore/maintenance (APCV 360)
├── .github/               # ✅ CI/CD workflows
└── .kit/                  # ✅ Kit AI bot configuration
```

**Legend**: ✅ = Complete | 🔄 = In Progress

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip
- virtualenv
- SQLite3

### Installation

```bash
# Clone repository
git clone https://github.com/fowler013/CampPowerUp.git
cd CampPowerUp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (if any)
python scripts/database/maintenance.py

# Start development server
python registration_form/app.py
```

Visit http://localhost:5000

### Using VS Code (Recommended)

1. Open workspace in VS Code
2. Install recommended extensions (when prompted)
3. Press `Cmd+Shift+P` → "Tasks: Run Task" → "🚀 Start Registration Server"
4. Or press `F5` to start with debugger

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term --cov-report=html

# Run specific test suites
pytest tests/unit          # Unit tests only
pytest tests/integration   # Integration tests
pytest tests/security      # Security tests (CYBV 301)

# View coverage report
open htmlcov/index.html
```

**VS Code**: Press `Cmd+Shift+T` or use "🧪 Run All Tests" task

## 📊 Code Quality

```bash
# Format code
black src/ tests/ scripts/
isort src/ tests/ scripts/ --profile=black

# Lint
pylint src/

# Type checking
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/
safety check
```

**VS Code**: Use "✅ Run All Quality Checks" task

## 💾 Database Management

Professional database tools applying **APCV 360** principles:

```bash
# Create backup
python scripts/database/backup.py

# List available backups
python scripts/database/restore.py --list

# Restore from latest backup
python scripts/database/restore.py --latest

# Run maintenance (VACUUM, ANALYZE, integrity check)
python scripts/database/maintenance.py

# Check for missing indexes
python scripts/database/maintenance.py --check-indexes
```

## 🔒 Security (CYBV 301)

- ✅ **Input Validation** - All user input sanitized and validated
- ✅ **SQL Injection Prevention** - Parameterized queries only
- ✅ **XSS Protection** - Template auto-escaping (Jinja2)
- ✅ **CSRF Protection** - CSRF tokens on all forms
- ✅ **Authentication** - Secure password hashing (bcrypt)
- ✅ **Session Management** - 30-minute timeout, secure cookies
- ✅ **HTTPS Enforcement** - Production uses HTTPS only

## 🎓 Computer Science Principles Applied

### CYBV 301 - Cybersecurity Fundamentals

- Configuration security (SECRET_KEY, session management)
- Authentication and authorization
- Input validation and sanitization
- HTTPS enforcement and secure cookies

### APCV 360 - Database Design & Management

- Database normalization (3NF)
- Connection pooling and optimization
- Transaction management (ACID compliance)
- Backup and recovery procedures
- Query optimization (VACUUM, ANALYZE)

### CYBV 302 - System Integration

- MVC architecture pattern
- Service layer abstraction
- Error handling and logging
- CI/CD pipeline automation
- API design and testing

## 🤖 Automation (Kit AI Bot)

Integrated with Kit AI bot for:

- 🔄 **GitHub Integration** - Auto-create issues from logs
- ✅ **PR Auto-Review** - Code quality, testing, security checks
- 🚀 **Auto-Deployment** - Deploy to staging/production
- 📊 **Monitoring** - Performance tracking and alerts
- 🎓 **Learning Tracking** - Map code to course concepts

Configuration: `.kit/config.yaml`

## 📈 CI/CD Pipeline

**GitHub Actions** workflows:

### CI Pipeline (`.github/workflows/ci.yml`)

- Code formatting (black, isort)
- Linting (pylint, flake8, mypy)
- Testing (pytest with 80% coverage)
- Security scanning (bandit, safety)

### Deployment (`.github/workflows/deploy.yml`)

- Auto-deploy to **staging** (develop branch)
- Auto-deploy to **production** (main branch)
- Database backups before deployment
- Health checks and rollback on failure

## 📝 Pull Request Guidelines

Use our PR templates:

- **Feature**: `.github/PULL_REQUEST_TEMPLATE/feature.md`
- **Bugfix**: `.github/PULL_REQUEST_TEMPLATE/bugfix.md`

**Requirements**:

- [ ] All tests passing
- [ ] Code coverage ≥ 80%
- [ ] Code formatted (black, isort)
- [ ] No security vulnerabilities (bandit)
- [ ] Documentation updated
- [ ] CS principles documented

## 🌳 Git Workflow

```
main (production)
  ├── develop (staging)
  │   ├── feature/project-reorganization (current)
  │   ├── feature/<new-feature>
  │   └── bugfix/<bug-name>
  └── hotfix/<critical-fix>
```

### Branch Strategy

- **main** → Production (auto-deploy to Railway)
- **develop** → Staging (auto-deploy to staging)
- **feature/** → New features (PR to develop)
- **bugfix/** → Bug fixes (PR to develop)
- **hotfix/** → Critical fixes (PR to main)

## 📚 Documentation

- **Architecture**: `docs/architecture/ARCHITECTURE_DIAGRAM.md`
- **Reorganization Plan**: `PROJECT_REORGANIZATION_PLAN.md`
- **Integration Strategy**: `MASTER_PROJECT_MANAGEMENT.md`
- **Progress Report**: `PHASE1_PROGRESS_REPORT.md`
- **Quick Reference**: `QUICK_REFERENCE.md`

## 🚢 Deployment

### Railway (Current)

```bash
# Deploy to staging
git push origin develop

# Deploy to production
git push origin main
```

### Manual Deployment

```bash
# Set environment variables
export FLASK_ENV=production
export SECRET_KEY=<your-secret-key>
export SENDGRID_API_KEY=<your-sendgrid-key>

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 registration_form.app:app
```

## 🛠️ Tech Stack

- **Backend**: Flask (Python 3.11+)
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: HTML5, CSS3, JavaScript, Jinja2 templates
- **Email**: SendGrid
- **Hosting**: Railway
- **CI/CD**: GitHub Actions
- **Testing**: pytest, coverage
- **Code Quality**: black, isort, pylint, mypy, bandit

## 📊 Project Status

| Metric                   | Status          |
| ------------------------ | --------------- |
| **Phase 1** (Foundation) | 🟡 70% Complete |
| **Code Coverage**        | 🔄 Target: 80%  |
| **Security Audit**       | 🟢 Passing      |
| **Production Status**    | 🟢 Live         |
| **Test Suite**           | 🔄 In Progress  |

See `PHASE1_PROGRESS_REPORT.md` for detailed progress.

## 🤝 Contributing

1. Create a feature branch from `develop`
2. Make your changes
3. Write tests (maintain 80%+ coverage)
4. Run quality checks: `python -m pytest && black src/ && pylint src/`
5. Create PR using appropriate template
6. Wait for CI/CD checks to pass
7. Request review

## 📧 Contact

**Email**: camppowerup2025@gmail.com  
**Production**: https://camppowerup-registration.up.railway.app

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built applying principles from CYBV 301, APCV 360, CYBV 302 courses
- Automated with Kit AI bot
- Deployed on Railway
- Thanks to all camp participants and parents!

---

**Last Updated**: December 2, 2024  
**Version**: 2.0.0 (Reorganization in progress)  
**Branch**: feature/project-reorganization

🎮 **Ready for Summer 2025!** 🎮
