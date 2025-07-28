# Camp Power-Up Registration Management Guide

## Overview
This guide covers all aspects of managing the Camp Power-Up registration system, including viewing registrations, handling payments, and preventing fraud.

## Ways to Check Registrations

### 1. **Admin Dashboard** (Primary Method)
- **URL:** `http://localhost:5001/admin`
- **Features:**
  - View all registrations in chronological order
  - Search by name, email, or submission ID
  - Export registration data
  - **NEW: Fraud prevention verification tools**
  - Real-time registration statistics

### 2. **Direct Database Access**
```bash
cd /Users/tevinfowler/Documents/CampPowerUp/registration_form
python3 -c "
import sqlite3
conn = sqlite3.connect('registration_submissions.db')
cursor = conn.cursor()
cursor.execute('SELECT child_first_name, child_last_name, parent_email, is_returning_camper, timestamp FROM registrations ORDER BY timestamp DESC')
for row in cursor.fetchall():
    print(f'{row[0]} {row[1]} ({row[2]}) - Returning: {row[3]} - {row[4]}')
conn.close()
"
```

### 3. **Command Line Registration Count**
```bash
cd /Users/tevinfowler/Documents/CampPowerUp/registration_form
python3 -c "
import sqlite3
conn = sqlite3.connect('registration_submissions.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM registrations')
print(f'Total registrations: {cursor.fetchone()[0]}')
conn.close()
"
```

### 4. **Registration Statistics API**
- **URL:** `http://localhost:5001/admin/registration-stats`
- **Returns:** JSON with counts, pricing breakdown, and revenue analysis

## 🛡️ FRAUD PREVENTION & VERIFICATION

### The Problem
Some families may fraudulently select "returning camper" to get the discounted price, even if their child has never attended Camp Power-Up before.

### Prevention Measures Implemented

#### 1. **Database Validation**
- The system automatically checks each "returning camper" claim against the registration database
- Blocks submissions if no previous registration is found for that name/email combination
- Displays clear error message directing users to select "new camper" option

#### 2. **Additional Verification Fields**
When someone selects "returning camper," they must provide:
- **Previous year attended** (required field)
- **Staff members they remember** (optional but helpful)
- **Memories/activities from previous years** (helps verify authenticity)

#### 3. **Admin Verification Tools**
- **URL:** `http://localhost:5001/admin/verify-returning-campers`
- **Features:**
  - Lists all registrations claiming returning camper status
  - Shows verification status (verified vs. needs review)
  - Displays the verification information provided by families
  - Highlights registrations that need manual review

#### 4. **Visual Warnings**
- Clear pricing display on the form
- Warning message about verification process
- Required verification fields for returning campers

### How to Handle Suspected Fraud

1. **Access the Verification Tool**
   - Go to `http://localhost:5001/admin/verify-returning-campers`
   - Review all unverified returning camper claims

2. **Contact the Family**
   - Email or call families with unverified claims
   - Ask specific questions about their previous camp experience
   - Verify against staff records if possible

3. **Take Action**
   - If claim is invalid: Request payment of the price difference
   - If claim is valid but not in database: Update records and allow discount
   - Document your findings for future reference

### Red Flags to Watch For
- **No previous year specified** or vague responses
- **Can't remember any staff members** from previous years
- **Generic responses** about camp activities
- **Database shows no previous registrations** for that name/email

## Registration Workflow

### For New Registrations
1. Parent fills out registration form at `http://localhost:5001`
2. System validates all required fields
3. **If claiming returning camper:**
   - System checks database for previous registrations
   - Requires additional verification information
   - May block submission if no previous records found
4. Registration is saved to database
5. Confirmation email is sent (if email system is configured)
6. Registration appears in admin dashboard

### For Admin Review
1. Access admin dashboard at `http://localhost:5001/admin`
2. **Check for fraud alerts** using the verification tool
3. Review registration details
4. Contact families for payment or clarification as needed
5. Update payment status once received

## Database Schema
The registration database includes these key fields:
- `child_first_name`, `child_last_name` - Camper identification
- `parent_email` - Primary contact and verification key
- `is_returning_camper` - Boolean flag for pricing tier
- `previous_year` - When they claim to have attended
- `previous_instructor` - Staff they remember
- `returning_camper_details` - Their camp memories/experiences
- `timestamp` - When registration was submitted

## Troubleshooting

### Registration Not Appearing
1. Check if the registration form service is running: `http://localhost:5001`
2. Verify database file exists: `registration_submissions.db`
3. Check for database errors in the terminal output

### False Fraud Alerts
- Sometimes legitimate returning campers may have changed email addresses
- Check for name matches even without email matches
- Manually verify with camp records from previous years

### System Access
- **Registration Form:** `http://localhost:5001`
- **Admin Dashboard:** `http://localhost:5001/admin`
- **Fraud Verification:** `http://localhost:5001/admin/verify-returning-campers`
- **Statistics API:** `http://localhost:5001/admin/registration-stats`

## Security Notes
- The fraud prevention system is not foolproof - manual review is still important
- Always verify high-value transactions or suspicious patterns
- Keep backup records of previous camp attendees for verification
- Consider implementing additional verification methods for future camps (photos, certificates, etc.)

---

**Last Updated:** July 28, 2025  
**System Version:** Camp Power-Up Registration v2.1 with Fraud Prevention
