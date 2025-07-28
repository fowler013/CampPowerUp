# Registration Management Guide

## How to Check Camp Registrations

### 1. Command Line Query
Use this Python script to view all registrations:

```python
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python -c "
import sqlite3
from datetime import datetime

conn = sqlite3.connect('registration_submissions.db')
cursor = conn.cursor()

# Get all registrations
cursor.execute('''
    SELECT submission_id, child_first_name, child_last_name, child_age, 
           parent_email, is_returning_camper, timestamp, tshirt_size
    FROM registrations 
    ORDER BY timestamp DESC
''')

registrations = cursor.fetchall()

print('🏕️ CAMP POWER-UP REGISTRATIONS')
print('=' * 50)

if registrations:
    print(f'Total Registrations: {len(registrations)}')
    print()
    
    for i, reg in enumerate(registrations, 1):
        submission_id, first_name, last_name, age, email, is_returning, timestamp, tshirt = reg
        returning_status = 'Returning' if is_returning else 'New'
        print(f'{i}. {first_name} {last_name} (Age {age})')
        print(f'   📧 {email}')
        print(f'   🎯 {returning_status} Camper | 👕 {tshirt or \"Not specified\"}')
        print(f'   📅 Registered: {timestamp}')
        print(f'   🔖 ID: {submission_id}')
        print()
else:
    print('No registrations found.')

conn.close()
"
```

### 2. API Endpoint
Get registration data in JSON format:
```bash
curl http://127.0.0.1:5001/api/registrations
```

### 3. Admin Dashboard
Visit the web interface in your browser:
- **URL**: http://127.0.0.1:5001/admin
- Shows formatted list of all registrations
- Allows viewing detailed information for each camper

### 4. Database Direct Access
Connect directly to the SQLite database:
- **Database File**: `registration_submissions.db`
- **Table**: `registrations`
- **Tools**: Any SQLite browser (DB Browser for SQLite, SQLiteStudio, etc.)

### 5. Registration Analytics
Get detailed statistics:

```python
/Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python -c "
import sqlite3

conn = sqlite3.connect('registration_submissions.db')
cursor = conn.cursor()

# Get analytics
cursor.execute('SELECT COUNT(*) FROM registrations')
total = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM registrations WHERE is_returning_camper = 1')
returning = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM registrations WHERE is_returning_camper = 0')
new_campers = cursor.fetchone()[0]

cursor.execute('SELECT AVG(child_age) FROM registrations')
avg_age = cursor.fetchone()[0]

print('📊 REGISTRATION ANALYTICS')
print('=' * 30)
print(f'Total Registrations: {total}')
print(f'New Campers: {new_campers}')
print(f'Returning Campers: {returning}')
print(f'Average Age: {avg_age:.1f}' if avg_age else 'N/A')

conn.close()
"
```

## Database Schema

The `registrations` table contains the following key fields:
- `submission_id`: Unique ID (format: CP_YYYYMMDD_HHMMSS_XXX)
- `child_first_name`, `child_last_name`: Camper name
- `child_age`, `child_grade`, `child_gender`: Demographics
- `parent_email`, `parent_phone`: Contact information
- `is_returning_camper`: Boolean (1 for returning, 0 for new)
- `gaming_behavior`, `favorite_games`, `games_owned`: Gaming preferences
- `has_allergies`, `allergy_details`: Health information
- `tshirt_size`: For camp materials
- `timestamp`: Registration date/time
- `raw_form_data`: Complete form submission backup

## Running the Registration System

1. **Start Main Dashboard** (port 5000):
   ```bash
   cd /Users/tevinfowler/Documents/CampPowerUp
   /Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python app.py
   ```

2. **Start Registration Form** (port 5001):
   ```bash
   cd /Users/tevinfowler/Documents/CampPowerUp/registration_form
   /Users/tevinfowler/Documents/CampPowerUp/.venv/bin/python -c "
   import sys, os
   os.chdir('/Users/tevinfowler/Documents/CampPowerUp/registration_form')
   sys.path.insert(0, '.')
   from app import app
   app.run(host='127.0.0.1', port=5001, debug=True, use_reloader=False)
   "
   ```

## Troubleshooting

- **Port conflicts**: Use `lsof -i :5001` to check what's running
- **Database errors**: Ensure `registration_submissions.db` exists and has proper schema
- **Template issues**: Verify Flask template folder is set to `./templates`
