# CampPowerUp Scripts

Utility scripts for managing, testing, and debugging the CampPowerUp system.

## Structure

```
scripts/
├── setup/              # Deployment and startup
│   ├── *.sh            # Shell scripts for deploy/start/stop
│   ├── *.py            # Python setup utilities
│   └── project-manager.sh
├── debug/              # Diagnostics
│   ├── health_check.py
│   ├── *_diagnostic.py
│   └── check_status.py
├── test/               # Testing
│   ├── *_test.py
│   └── test_*.py
└── archive/            # Old/backup files (for reference)
```

## Common Commands

### Start Services
```bash
# All services
python scripts/setup/start_services.py

# Individual scripts
bash scripts/setup/start.sh
bash scripts/setup/start_production.sh
```

### Testing
```bash
python scripts/test/complete_system_test.py
python scripts/test/test_login.py
python scripts/test/live_security_test.py
```

### Diagnostics
```bash
python scripts/debug/health_check.py
python scripts/debug/check_status.py
python scripts/debug/gmail_diagnostic.py
```

### Database
```bash
python scripts/setup/migrate_database.py
bash scripts/setup/backup_databases.sh
```

## Archive Folder

The `archive/` folder contains old versions of files kept for reference:
- `app_old.py`, `app_clean.py` - Previous app versions
- `production_builder_*.py` - Old build scripts

These are not actively used but preserved for rollback reference.
