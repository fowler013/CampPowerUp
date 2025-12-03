# CampPowerUp Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CampPowerUp System                          │
│                     (MVC Architecture + Services)                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Templates   │  │   Static     │  │   Forms      │            │
│  │  (Jinja2)    │  │   Assets     │  │  (WTForms)   │            │
│  │              │  │  CSS/JS      │  │              │            │
│  │ - index.html │  │ - style.css  │  │ - validators │            │
│  │ - admin.html │  │ - scripts.js │  │ - CSRF       │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CONTROLLER LAYER                            │
│                          (Flask Routes)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  src/registration/routes.py                                  │  │
│  │  - /register (GET/POST)                                      │  │
│  │  - /confirmation/<id>                                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  src/admin/routes.py                                         │  │
│  │  - /admin/dashboard                                          │  │
│  │  - /admin/attendance                                         │  │
│  │  - /admin/mark-paid/<id>                                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  src/communication/routes.py                                 │  │
│  │  - /messages                                                 │  │
│  │  - /parent-portal                                            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          SERVICE LAYER                              │
│                    (Business Logic + Services)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Registration     │  │  Email Service   │  │  Auth Service   │ │
│  │  Service         │  │  (SendGrid)      │  │  (bcrypt)       │ │
│  │                  │  │                  │  │                 │ │
│  │ - validate_form  │  │ - send_confirm   │  │ - login()       │ │
│  │ - create_reg     │  │ - send_receipt   │  │ - logout()      │ │
│  │ - update_payment │  │ - notify_admin   │  │ - check_auth()  │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  Attendance      │  │  Communication   │  │  Game Library   │ │
│  │  Service         │  │  Service         │  │  Service        │ │
│  │                  │  │                  │  │                 │ │
│  │ - mark_present   │  │ - send_message   │  │ - get_games()   │ │
│  │ - get_attendance │  │ - get_threads    │  │ - add_game()    │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            MODEL LAYER                              │
│                        (Data Access Objects)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Registration     │  │  Attendance      │  │  Communication  │ │
│  │  Model           │  │  Model           │  │  Model          │ │
│  │                  │  │                  │  │                 │ │
│  │ - find_by_id()   │  │ - find_by_date() │  │ - find_all()    │ │
│  │ - find_all()     │  │ - create()       │  │ - create()      │ │
│  │ - create()       │  │ - update()       │  │ - mark_read()   │ │
│  │ - update()       │  │                  │  │                 │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATABASE LAYER                              │
│                 (Connection Management + Utilities)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  src/shared/database.py (DatabaseManager)                    │  │
│  │  ✅ IMPLEMENTED                                              │  │
│  │                                                               │  │
│  │  - get_connection()      → Connection pooling                │  │
│  │  - execute_query()       → SELECT queries                    │  │
│  │  - execute_update()      → INSERT/UPDATE/DELETE              │  │
│  │  - transaction()         → Context manager                   │  │
│  │  - backup()              → Create backup                     │  │
│  │  - vacuum()              → Optimize                          │  │
│  │  - analyze()             → Update statistics                 │  │
│  │                                                               │  │
│  │  APCV 360 Principles:                                        │  │
│  │  • Connection pooling                                        │  │
│  │  • Transaction management                                    │  │
│  │  • Query optimization                                        │  │
│  │  • Backup & recovery                                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────┐                             │
│  │  Database: camp_power_up.db      │                             │
│  │                                   │                             │
│  │  Tables:                          │                             │
│  │  - registrations                  │                             │
│  │  - attendance                     │                             │
│  │  - messages                       │                             │
│  │  - users                          │                             │
│  └──────────────────────────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        SHARED UTILITIES                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Configuration    │  │  Authentication  │  │  Email Service  │ │
│  │ (src/config)     │  │  (src/shared)    │  │  (src/shared)   │ │
│  │                  │  │                  │  │                 │ │
│  │ ✅ COMPLETE      │  │ 🔄 NEXT          │  │ 🔄 NEXT         │ │
│  │                  │  │                  │  │                 │ │
│  │ - Dev config     │  │ - login()        │  │ - send_email()  │ │
│  │ - Test config    │  │ - logout()       │  │ - templates     │ │
│  │ - Staging config │  │ - hash_password()│  │ - attachments   │ │
│  │ - Prod config    │  │ - verify()       │  │                 │ │
│  │                  │  │                  │  │                 │ │
│  │ CYBV 301 & 360   │  │ CYBV 301         │  │ CYBV 302        │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐                       │
│  │  Logging         │  │  Validators      │                       │
│  │  (src/shared)    │  │  (src/shared)    │                       │
│  │                  │  │                  │                       │
│  │ 🔄 NEXT          │  │ 🔄 PHASE 2       │                       │
│  │                  │  │                  │                       │
│  │ - log_request()  │  │ - email_valid()  │                       │
│  │ - log_error()    │  │ - phone_valid()  │                       │
│  │ - log_db()       │  │ - sanitize()     │                       │
│  │                  │  │                  │                       │
│  │ CYBV 381         │  │ CYBV 301         │                       │
│  └──────────────────┘  └──────────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INTEGRATIONS                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  SendGrid        │  │  Railway         │  │  Kit AI Bot     │ │
│  │  (Email)         │  │  (Hosting)       │  │  (Automation)   │ │
│  │                  │  │                  │  │                 │ │
│  │ - Confirmation   │  │ - Production     │  │ - GitHub        │ │
│  │ - Receipts       │  │ - Staging        │  │ - CI/CD         │ │
│  │ - Notifications  │  │ - Auto-deploy    │  │ - Monitoring    │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        CI/CD PIPELINE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  GitHub Actions Workflow                                    │   │
│  │  ✅ IMPLEMENTED                                             │   │
│  │                                                              │   │
│  │  [Push to GitHub]                                           │   │
│  │         │                                                    │   │
│  │         ├──> CI Pipeline (.github/workflows/ci.yml)         │   │
│  │         │    - Lint (black, isort, pylint, mypy)            │   │
│  │         │    - Test (pytest, 80% coverage)                  │   │
│  │         │    - Security (bandit, safety)                    │   │
│  │         │    - Build verification                           │   │
│  │         │                                                    │   │
│  │         └──> Deploy Pipeline (.github/workflows/deploy.yml) │   │
│  │              - Backup database                              │   │
│  │              - Deploy to Railway                            │   │
│  │              - Health checks                                │   │
│  │              - Rollback on failure                          │   │
│  │                                                              │   │
│  │  Kit AI Bot monitors all steps and creates issues          │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        TESTING STRATEGY                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  Unit Tests      │  │  Integration     │  │  Security Tests │ │
│  │  (tests/unit)    │  │  (tests/int)     │  │  (tests/sec)    │ │
│  │                  │  │                  │  │                 │ │
│  │ 🔄 PHASE 1       │  │ 🔄 PHASE 2       │  │ 🔄 PHASE 3      │ │
│  │                  │  │                  │  │                 │ │
│  │ - test_config.py │  │ - test_api.py    │  │ - test_xss.py   │ │
│  │ - test_db.py     │  │ - test_email.py  │  │ - test_sqli.py  │ │
│  │ - test_auth.py   │  │ - test_forms.py  │  │ - test_csrf.py  │ │
│  │                  │  │                  │  │                 │ │
│  │ Target: 80%+     │  │ CYBV 302         │  │ CYBV 301        │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      DATA FLOW EXAMPLE                              │
│                   (Registration Submission)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. User fills form → /register (POST)                             │
│                       │                                             │
│  2. Controller        │                                             │
│     (routes.py) ──────┴──> Validate form (CYBV 301)                │
│                       │                                             │
│  3. Service Layer     │                                             │
│     (service.py) ─────┴──> Business logic                          │
│                       │    - Calculate fees                        │
│                       │    - Generate confirmation ID              │
│                       │                                             │
│  4. Model Layer       │                                             │
│     (models.py) ──────┴──> Save to database                        │
│                       │    via DatabaseManager                     │
│                       │                                             │
│  5. Database Layer    │                                             │
│     (database.py) ────┴──> Transaction with rollback               │
│                       │    Connection pooling (APCV 360)           │
│                       │                                             │
│  6. Email Service     │                                             │
│     (email.py) ───────┴──> Send confirmation (CYBV 302)            │
│                       │                                             │
│  7. Response          │                                             │
│     (template) ───────┴──> Render confirmation page                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       SECURITY LAYERS                               │
│                        (CYBV 301)                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 1: Input Validation                                         │
│  ├─ Form validators (WTForms)                                      │
│  ├─ Email/phone format validation                                  │
│  └─ Sanitization of user input                                     │
│                                                                     │
│  Layer 2: Authentication                                           │
│  ├─ Password hashing (bcrypt)                                      │
│  ├─ Session management (30-min timeout)                            │
│  └─ Role-based access control (admin/parent)                       │
│                                                                     │
│  Layer 3: CSRF Protection                                          │
│  ├─ CSRF tokens on all forms                                       │
│  └─ Token validation on POST requests                              │
│                                                                     │
│  Layer 4: SQL Injection Prevention                                 │
│  ├─ Parameterized queries only                                     │
│  └─ No dynamic SQL construction                                    │
│                                                                     │
│  Layer 5: XSS Protection                                           │
│  ├─ Template auto-escaping (Jinja2)                                │
│  └─ Content Security Policy headers                                │
│                                                                     │
│  Layer 6: HTTPS Enforcement                                        │
│  ├─ Secure cookies in production                                   │
│  └─ HSTS headers                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   DATABASE SCHEMA (APCV 360)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  registrations                    attendance                        │
│  ├─ id (PK)                       ├─ id (PK)                       │
│  ├─ confirmation_id               ├─ registration_id (FK)          │
│  ├─ parent_name                   ├─ date                          │
│  ├─ parent_email                  ├─ present                       │
│  ├─ parent_phone                  ├─ check_in_time                 │
│  ├─ child_name                    └─ notes                         │
│  ├─ child_age                                                       │
│  ├─ returning_camper              messages                         │
│  ├─ nintendo_account              ├─ id (PK)                       │
│  ├─ total_fee                     ├─ parent_email                  │
│  ├─ payment_method                ├─ subject                       │
│  ├─ payment_status (NEW)          ├─ body                          │
│  ├─ registration_date             ├─ sent_date                     │
│  └─ camp_date                     ├─ read                          │
│                                   └─ admin_response                 │
│  users                                                              │
│  ├─ id (PK)                       Indexes:                         │
│  ├─ username                      - registrations.payment_status   │
│  ├─ password_hash                 - attendance.registration_id     │
│  ├─ email                         - attendance.date                │
│  ├─ role                          - messages.parent_email          │
│  └─ created_at                    - messages.read                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Legend:
✅ Complete and tested
🔄 In progress / Next phase
─ Connection/flow
└ Child item
```

## CS Principles Mapping

### CYBV 301 - Cybersecurity Fundamentals
- **Configuration**: Security settings, secrets management
- **Authentication**: Login/logout, password hashing, sessions
- **Validation**: Input sanitization, CSRF protection
- **Security Testing**: XSS, SQLi, CSRF tests

### APCV 360 - Database Design & Management
- **Schema Design**: Normalized tables, proper indexes
- **Connection Management**: Pooling, resource cleanup
- **Transactions**: ACID compliance, rollback on errors
- **Optimization**: VACUUM, ANALYZE, query performance
- **Backup & Recovery**: Automated backups, restore procedures

### CYBV 302 - System Integration
- **Architecture**: MVC pattern, separation of concerns
- **Services**: Email service, external API integration
- **Error Handling**: Try/except, logging, graceful degradation
- **Testing**: Unit tests, integration tests
- **CI/CD**: Automated testing, deployment pipelines
