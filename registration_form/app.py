#!/usr/bin/env python3
"""
Camp Power-Up Registration Form Application
==========================================

A modern, improved registration form for Camp Power-Up that can work standalone
or integrate with the main dashboard system.

Features:
- Modern, mobile-friendly design
- Real-time validation
- Auto-save functionality
- Integration with main dashboard
- Payment tracking
- Email notifications
- Dynamic session configuration
"""

import os
import sqlite3
import json
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import re
from camp_config import CAMP_CONFIG, get_camp_title, get_camp_subtitle, get_pricing_text, validate_config

app = Flask(__name__, template_folder='./templates')
app.secret_key = 'camp_power_up_registration_2025'

# Admin credentials - in production, store these securely
ADMIN_USERNAME = 'campadmin'
ADMIN_PASSWORD = 'PowerUp2025!'  # Change this in production

def check_admin_auth():
    """Check if user is authenticated as admin."""
    return session.get('admin_authenticated', False)

def require_admin_auth(f):
    """Decorator to require admin authentication."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_admin_auth():
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'camp.db')
DB_PATH = '../camp_power_up.db'  # Connect to main database
REGISTRATION_DB = os.path.join(os.path.dirname(__file__), 'registration_submissions.db')

def init_registration_db():
    """Initialize the registration-specific database."""
    conn = sqlite3.connect(REGISTRATION_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT UNIQUE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            payment_status TEXT DEFAULT 'pending',
            
            -- Contact Information
            parent_email TEXT NOT NULL,
            parent_phone TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            
            -- Camper Information
            child_first_name TEXT NOT NULL,
            child_last_name TEXT NOT NULL,
            child_age INTEGER,
            child_grade TEXT,
            child_gender TEXT,
            
            -- Camp Information
            is_returning_camper BOOLEAN DEFAULT FALSE,
            previous_year TEXT,  -- When they last attended
            previous_instructor TEXT,  -- Staff they remember
            returning_camper_details TEXT,  -- Memories/activities from previous years
            camp_weeks TEXT,  -- JSON array of selected weeks
            
            -- Gaming Information
            gaming_behavior TEXT,
            game_restrictions TEXT,
            bringing_own_switch BOOLEAN DEFAULT FALSE,
            favorite_games TEXT,
            games_owned TEXT,  -- New field for explicit game ownership
            console_experience TEXT,
            
            -- Health & Safety
            has_allergies BOOLEAN DEFAULT FALSE,
            allergy_details TEXT,
            has_sensory_issues BOOLEAN DEFAULT FALSE,
            sensory_details TEXT,
            medical_conditions TEXT,
            
            -- Permissions
            photo_permission BOOLEAN DEFAULT FALSE,
            marketing_permission BOOLEAN DEFAULT FALSE,
            
            -- Additional Information
            tshirt_size TEXT,
            how_heard_about_camp TEXT,
            additional_notes TEXT,
            
            -- Form Data (raw JSON backup)
            raw_form_data TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def check_returning_camper_validity(child_first_name, child_last_name, parent_email):
    """Check if a camper claiming to be returning actually has past registrations."""
    import csv
    
    # First check current registration database
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'registration_submissions.db'))
    cursor = conn.cursor()
    
    # Check for exact name and email match in current registrations
    # Look for registrations from previous years/seasons (more than 30 days ago)
    cursor.execute('''
        SELECT COUNT(*) FROM registrations 
        WHERE LOWER(child_first_name) = LOWER(?) 
        AND LOWER(child_last_name) = LOWER(?) 
        AND LOWER(parent_email) = LOWER(?)
        AND timestamp < datetime('now', '-30 days')  -- Must be from a previous camp session
    ''', (child_first_name.strip(), child_last_name.strip(), parent_email.strip()))
    
    exact_matches_db = cursor.fetchone()[0]
    
    # Also check for just name match in current registrations (in case email changed)
    cursor.execute('''
        SELECT COUNT(*) FROM registrations 
        WHERE LOWER(child_first_name) = LOWER(?) 
        AND LOWER(child_last_name) = LOWER(?)
        AND timestamp < datetime('now', '-30 days')  -- Must be from a previous camp session
    ''', (child_first_name.strip(), child_last_name.strip()))
    
    name_matches_db = cursor.fetchone()[0]
    conn.close()
    
    # Now check historical CSV data
    historical_csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'Camp_Power_Up_past_forms - Sheet1.csv')
    exact_matches_csv = 0
    name_matches_csv = 0
    
    try:
        with open(historical_csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Get the field names (handling possible variations)
                first_name_field = None
                last_name_field = None
                email_field = None
                
                for field in row.keys():
                    if 'first name' in field.lower() or 'childs first' in field.lower():
                        first_name_field = field
                    elif 'last name' in field.lower() or 'childs last' in field.lower():
                        last_name_field = field
                    elif 'email' in field.lower():
                        email_field = field
                
                if first_name_field and last_name_field and email_field:
                    csv_first = row.get(first_name_field, '').strip()
                    csv_last = row.get(last_name_field, '').strip()
                    csv_email = row.get(email_field, '').strip()
                    
                    # Check for exact match (name + email)
                    if (csv_first.lower() == child_first_name.strip().lower() and 
                        csv_last.lower() == child_last_name.strip().lower() and 
                        csv_email.lower() == parent_email.strip().lower()):
                        exact_matches_csv += 1
                    
                    # Check for name-only match
                    elif (csv_first.lower() == child_first_name.strip().lower() and 
                          csv_last.lower() == child_last_name.strip().lower()):
                        name_matches_csv += 1
                        
    except (FileNotFoundError, Exception) as e:
        # If we can't read the historical data, just log it but don't fail
        print(f"Warning: Could not read historical camper data: {e}")
    
    # Combine results from both sources
    total_exact_matches = exact_matches_db + exact_matches_csv
    total_name_matches = name_matches_db + name_matches_csv
    
    return {
        'exact_matches': total_exact_matches,
        'name_matches': total_name_matches,
        'exact_matches_current': exact_matches_db,
        'name_matches_current': name_matches_db,
        'exact_matches_historical': exact_matches_csv,
        'name_matches_historical': name_matches_csv,
        'is_likely_returning': total_exact_matches > 0 or total_name_matches > 0
    }

def validate_form_data(data):
    """Validate form submission data."""
    errors = []
    warnings = []
    
    # Required fields
    required_fields = [
        ('parent_email', 'Parent email'),
        ('child_first_name', 'Child first name'),
        ('child_last_name', 'Child last name'),
        ('child_age', 'Child age')
    ]
    
    for field, label in required_fields:
        if not data.get(field) or str(data.get(field)).strip() == '':
            errors.append(f"{label} is required")
    
    # Email validation
    if data.get('parent_email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['parent_email']):
            errors.append("Please enter a valid email address")
    
    # Age validation
    if data.get('child_age'):
        try:
            age = int(data['child_age'])
            if age < 5 or age > 18:
                errors.append("Child age must be between 5 and 18 years")
        except ValueError:
            errors.append("Please enter a valid age")
    
    # Phone validation (if provided)
    if data.get('parent_phone'):
        phone = re.sub(r'[^\d]', '', data['parent_phone'])
        if len(phone) != 10:
            errors.append("Please enter a valid 10-digit phone number")
    
    # Returning camper validation
    if data.get('is_returning_camper') == 'true':
        # Require verification fields for returning campers
        if not data.get('previous_year') or str(data.get('previous_year')).strip() == '':
            errors.append("Please specify when your child last attended Camp Power-Up.")
        
        # Check against database
        if data.get('child_first_name') and data.get('child_last_name') and data.get('parent_email'):
            validation_result = check_returning_camper_validity(
                data['child_first_name'], 
                data['child_last_name'], 
                data['parent_email']
            )
            
            if not validation_result['is_likely_returning']:
                errors.append("⚠️ VALIDATION ERROR: No previous registration found for this camper. Please select 'No - This is my child's first time' if this is their first time at Camp Power-Up. If you believe this is an error, please contact us directly.")
    
    return errors, warnings

@app.route('/')
def registration_form():
    """Display the registration form with dynamic configuration."""
    try:
        validate_config()
        pricing = get_pricing_text()
        
        return render_template('registration_form.html', 
                             camp_title=get_camp_title(),
                             camp_subtitle=get_camp_subtitle(),
                             pricing=pricing,
                             config=CAMP_CONFIG)
    except ValueError as e:
        return f"Configuration Error: {e}", 500

@app.route('/submit', methods=['POST'])
def submit_registration():
    """Handle form submission."""
    try:
        # Get form data
        form_data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate data
        errors, warnings = validate_form_data(form_data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Generate submission ID
        submission_id = f"CP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form_data['child_last_name'][:3].upper()}"
        
        # Save to database
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO registrations (
                submission_id, status, payment_status, parent_email, parent_phone, emergency_contact_name,
                emergency_contact_phone, child_first_name, child_last_name,
                child_age, child_grade, child_gender, is_returning_camper,
                previous_year, previous_instructor, returning_camper_details,
                camp_weeks, gaming_behavior, game_restrictions, bringing_own_switch,
                favorite_games, games_owned, console_experience, has_allergies, allergy_details,
                has_sensory_issues, sensory_details, medical_conditions,
                photo_permission, marketing_permission, tshirt_size,
                how_heard_about_camp, additional_notes, raw_form_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission_id,
            'pending',  # status
            'pending',  # payment_status
            form_data.get('parent_email'),
            form_data.get('parent_phone'),
            form_data.get('emergency_contact_name'),
            form_data.get('emergency_contact_phone'),
            form_data.get('child_first_name'),
            form_data.get('child_last_name'),
            int(form_data.get('child_age', 0)),
            form_data.get('child_grade'),
            form_data.get('child_gender'),
            form_data.get('is_returning_camper') == 'true',
            form_data.get('previous_year') if form_data.get('is_returning_camper') == 'true' else None,
            form_data.get('previous_instructor') if form_data.get('is_returning_camper') == 'true' else None,
            form_data.get('returning_camper_details') if form_data.get('is_returning_camper') == 'true' else None,
            json.dumps(form_data.get('camp_weeks', [])),
            form_data.get('gaming_behavior'),
            form_data.get('game_restrictions'),
            form_data.get('bringing_own_switch') == 'true',
            form_data.get('favorite_games'),
            form_data.get('games_owned'),  # New field
            form_data.get('console_experience'),
            form_data.get('has_allergies') == 'true',
            form_data.get('allergy_details'),
            form_data.get('has_sensory_issues') == 'true',
            form_data.get('sensory_details'),
            form_data.get('medical_conditions'),
            form_data.get('photo_permission') == 'true',
            form_data.get('marketing_permission') == 'true',
            form_data.get('tshirt_size'),
            form_data.get('how_heard_about_camp'),
            form_data.get('additional_notes'),
            json.dumps(form_data)
        ))
        
        conn.commit()
        conn.close()
        
        # Also sync to main database for dashboard integration
        sync_to_main_database(form_data, submission_id)
        
        return jsonify({
            'success': True,
            'submission_id': submission_id,
            'message': 'Registration submitted successfully!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'errors': [str(e)]}), 500

def sync_to_main_database(form_data, submission_id):
    """Sync registration data to main dashboard database."""
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            
            # Check if campers table exists, if not, create it
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    age INTEGER,
                    grade TEXT,
                    is_returning TEXT,
                    email TEXT,
                    has_allergies TEXT,
                    allergy_description TEXT,
                    has_sensory_issues TEXT,
                    sensory_description TEXT,
                    favorite_games TEXT,
                    bringing_switch TEXT,
                    game_behavior TEXT,
                    rating_restrictions TEXT,
                    social_media_consent TEXT
                )
            ''')
            
            # Insert camper data
            cursor.execute('''
                INSERT INTO campers (
                    submission_id, first_name, last_name, age, grade, is_returning,
                    email, has_allergies, allergy_description, has_sensory_issues,
                    sensory_description, favorite_games, bringing_switch,
                    game_behavior, rating_restrictions, social_media_consent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                submission_id,
                form_data.get('child_first_name'),
                form_data.get('child_last_name'),
                int(form_data.get('child_age', 0)),
                form_data.get('child_grade'),
                'Yes' if form_data.get('is_returning_camper') == 'true' else 'No',
                form_data.get('parent_email'),
                'Yes' if form_data.get('has_allergies') == 'true' else 'No',
                form_data.get('allergy_details', ''),
                'Yes' if form_data.get('has_sensory_issues') == 'true' else 'No',
                form_data.get('sensory_details', ''),
                form_data.get('favorite_games', ''),
                'Yes' if form_data.get('bringing_own_switch') == 'true' else 'No',
                form_data.get('gaming_behavior', ''),
                form_data.get('game_restrictions', ''),
                'Yes' if form_data.get('photo_permission') == 'true' else 'No'
            ))
            
            # Get the camper_id for game library integration
            camper_id = cursor.lastrowid
            
            # Process game data for game library integration
            process_camper_games_for_library(cursor, camper_id, form_data, submission_id)
            
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Error syncing to main database: {e}")

def process_camper_games_for_library(cursor, camper_id, form_data, submission_id):
    """Process and add camper's games to the game library system."""
    try:
        # Ensure game library tables exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                total_owned INTEGER DEFAULT 0,
                available INTEGER DEFAULT 0,
                checked_out INTEGER DEFAULT 0,
                category TEXT DEFAULT 'Unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camper_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camper_id INTEGER,
                game_id INTEGER,
                submission_id TEXT,
                source TEXT DEFAULT 'registration',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (camper_id) REFERENCES campers (id),
                FOREIGN KEY (game_id) REFERENCES games (id),
                UNIQUE(camper_id, game_id)
            )
        ''')
        
        # Extract games from both games_owned and favorite_games fields
        games_owned = form_data.get('games_owned', '')
        favorite_games = form_data.get('favorite_games', '')
        console_experience = form_data.get('console_experience', '')
        
        # Prioritize explicit games_owned field, then supplement with other fields
        primary_game_text = games_owned.strip()
        supplementary_text = f"{favorite_games} {console_experience}".strip()
        
        games = []
        
        # Process explicit games_owned field first (higher confidence)
        if primary_game_text:
            owned_games = extract_games_from_text(primary_game_text, high_confidence=True)
            games.extend(owned_games)
            print(f"🎮 Found {len(owned_games)} games from 'games_owned' field")
        
        # Then process other fields (lower confidence, avoid duplicates)
        if supplementary_text:
            additional_games = extract_games_from_text(supplementary_text, high_confidence=False)
            # Only add games not already found
            new_games = [g for g in additional_games if g not in games]
            games.extend(new_games)
            print(f"🎯 Found {len(new_games)} additional games from other fields")
            
            for game_name in games:
                # Insert or update game in games table
                cursor.execute('''
                    INSERT OR IGNORE INTO games (name, total_owned, available) 
                    VALUES (?, 1, 1)
                ''', (game_name,))
                
                # Update count if game already exists
                cursor.execute('''
                    UPDATE games 
                    SET total_owned = total_owned + 1, available = available + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ? AND id NOT IN (
                        SELECT game_id FROM camper_games WHERE camper_id = ?
                    )
                ''', (game_name, camper_id))
                
                # Get game_id
                cursor.execute('SELECT id FROM games WHERE name = ?', (game_name,))
                game_result = cursor.fetchone()
                if game_result:
                    game_id = game_result[0]
                    
                    # Link camper to game
                    cursor.execute('''
                        INSERT OR IGNORE INTO camper_games 
                        (camper_id, game_id, submission_id, source) 
                        VALUES (?, ?, ?, 'registration')
                    ''', (camper_id, game_id, submission_id))
                    
        print(f"✅ Processed games for camper {camper_id}: {len(games) if 'games' in locals() else 0} games found")
        
    except Exception as e:
        print(f"❌ Error processing games for library: {e}")

def extract_games_from_text(text, high_confidence=True):
    """Extract game names from free-form text input."""
    if not text:
        return []
    
    # Common game names and patterns
    known_games = [
        'Minecraft', 'Fortnite', 'Roblox', 'Among Us', 'Fall Guys',
        'Super Mario', 'Pokemon', 'Zelda', 'Smash Bros', 'Mario Kart',
        'Overwatch', 'Rocket League', 'Splatoon', 'Animal Crossing',
        'Stardew Valley', 'Terraria', 'Valorant', 'Apex Legends',
        'Destiny', 'Call of Duty', 'FIFA', 'NBA 2K', 'Madden',
        'Monopoly', 'Scrabble', 'Chess', 'Checkers', 'UNO',
        'Settlers of Catan', 'Catan', 'Risk', 'Clue', 'Sorry',
        'Yahtzee', 'Battleship', 'Connect 4', 'Jenga', 'Twister',
        'Pictionary', 'Trivial Pursuit', 'Life', 'Apples to Apples',
        'Cards Against Humanity', 'Exploding Kittens', 'Ticket to Ride'
    ]
    
    games_found = []
    text_lower = text.lower()
    
    # Look for known games first (high confidence)
    for game in known_games:
        if game.lower() in text_lower:
            games_found.append(game)
    
    if high_confidence:
        # For explicit "games owned" field, be more aggressive in extraction
        # Split by common separators
        import re
        
        # Split by commas, newlines, semicolons
        potential_games = re.split(r'[,\n;]+', text)
        
        for item in potential_games:
            item = item.strip()
            if len(item) > 2 and item not in games_found:
                # Clean up the game name
                cleaned = re.sub(r'^\W+|\W+$', '', item)  # Remove leading/trailing punctuation
                if len(cleaned) > 2:
                    games_found.append(cleaned.title())  # Title case for consistency
    else:
        # For other fields, be more conservative
        potential_games = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
        
        # Filter out common non-game words
        exclude_words = ['Yes', 'No', 'The', 'And', 'Or', 'But', 'Very', 'Really', 'Pretty', 'Good', 'Bad', 'Fun', 'Great', 'Love', 'Like', 'Play', 'Game', 'Games', 'Nintendo', 'Switch', 'Xbox', 'PlayStation']
        
        for potential in potential_games:
            if (potential not in exclude_words and 
                len(potential) > 3 and 
                potential not in games_found):
                games_found.append(potential)
    
    return list(set(games_found))  # Remove duplicates

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            session.permanent = True
            flash('Successfully logged in as admin', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_authenticated', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@require_admin_auth
def admin_dashboard():
    """Admin dashboard for viewing registrations."""
    conn = sqlite3.connect(REGISTRATION_DB)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute('''
        SELECT * FROM registrations 
        ORDER BY timestamp DESC
    ''')
    
    registrations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return render_template('admin_dashboard.html', registrations=registrations)

@app.route('/admin/historical')
@require_admin_auth
def admin_historical():
    """Admin page for viewing historical registrations for verification."""
    # Get historical data from main database
    historical_data = []
    main_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'camp_power_up.db')
    
    if os.path.exists(main_db_path):
        conn = sqlite3.connect(main_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('''
            SELECT first_name, last_name, email, age, grade, 
                   is_returning, has_allergies, bringing_switch, favorite_games
            FROM registrations 
            ORDER BY first_name, last_name
        ''')
        historical_data = [dict(row) for row in cursor.fetchall()]
        conn.close()
    
    # Also get CSV data
    csv_data = []
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'Camp_Power_Up_past_forms - Sheet1.csv')
    
    if os.path.exists(csv_path):
        import csv
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Extract relevant fields
                    first_name = ''
                    last_name = ''
                    email = ''
                    
                    for field, value in row.items():
                        if 'first name' in field.lower() or 'childs first' in field.lower():
                            first_name = value.strip()
                        elif 'last name' in field.lower() or 'childs last' in field.lower():
                            last_name = value.strip()
                        elif 'email' in field.lower():
                            email = value.strip()
                    
                    if first_name and last_name:
                        csv_data.append({
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'source': 'CSV'
                        })
        except Exception as e:
            print(f"Error reading CSV: {e}")
    
    return render_template('admin_historical.html', 
                         historical_data=historical_data, 
                         csv_data=csv_data)

@app.route('/admin/config')
@require_admin_auth
def admin_config():
    """Admin interface for updating camp configuration."""
    try:
        validate_config()
        return render_template('admin_config.html', config=CAMP_CONFIG)
    except ValueError as e:
        return f"Configuration error: {e}", 500

@app.route('/admin/update-config', methods=['POST'])
@require_admin_auth
def update_config():
    """Update the camp configuration."""
    try:
        data = request.get_json()
        
        # Update CAMP_CONFIG with new values
        CAMP_CONFIG["camp_name"] = data.get("camp_name", CAMP_CONFIG["camp_name"])
        CAMP_CONFIG["camp_subtitle"] = data.get("camp_subtitle", CAMP_CONFIG["camp_subtitle"])
        CAMP_CONFIG["camp_dates"] = data.get("camp_dates", CAMP_CONFIG["camp_dates"])
        CAMP_CONFIG["camp_days"] = int(data.get("camp_days", CAMP_CONFIG["camp_days"]))
        CAMP_CONFIG["daily_hours"] = data.get("daily_hours", CAMP_CONFIG["daily_hours"])
        CAMP_CONFIG["final_payment_due"] = data.get("final_payment_due", CAMP_CONFIG["final_payment_due"])
        
        # Update pricing
        CAMP_CONFIG["pricing"]["returning_camper"]["deposit"] = int(data.get("returning_deposit", 50))
        CAMP_CONFIG["pricing"]["returning_camper"]["final_payment"] = int(data.get("returning_final", 130))
        CAMP_CONFIG["pricing"]["returning_camper"]["total"] = (
            CAMP_CONFIG["pricing"]["returning_camper"]["deposit"] + 
            CAMP_CONFIG["pricing"]["returning_camper"]["final_payment"]
        )
        
        CAMP_CONFIG["pricing"]["new_camper"]["deposit"] = int(data.get("new_deposit", 50))
        CAMP_CONFIG["pricing"]["new_camper"]["final_payment"] = int(data.get("new_final", 150))
        CAMP_CONFIG["pricing"]["new_camper"]["total"] = (
            CAMP_CONFIG["pricing"]["new_camper"]["deposit"] + 
            CAMP_CONFIG["pricing"]["new_camper"]["final_payment"]
        )
        
        # Write updated config back to file
        update_config_file()
        
        validate_config()
        
        return jsonify({"success": True, "message": "Configuration updated successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def update_config_file():
    """Write the current CAMP_CONFIG back to the camp_config.py file."""
    import json
    
    config_content = f'''#!/usr/bin/env python3
"""
Camp Power-Up Session Configuration
==================================

This file contains the dynamic camp session information that changes
between different camp offerings throughout the year.

Update this file for each new camp session rather than modifying templates.
LAST UPDATED: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from datetime import datetime

# Current Camp Session Configuration
CAMP_CONFIG = {json.dumps(CAMP_CONFIG, indent=4)}

# Dynamic text generation functions
def get_camp_title():
    """Get the formatted camp title."""
    return CAMP_CONFIG["camp_name"]

def get_camp_subtitle():
    """Get the camp subtitle/description."""
    return CAMP_CONFIG["camp_subtitle"]

def get_pricing_text():
    """Generate the pricing information text."""
    returning = CAMP_CONFIG["pricing"]["returning_camper"]
    new = CAMP_CONFIG["pricing"]["new_camper"]
    
    return {{
        "returning_text": f"Returning Campers: ${{returning['deposit']}} deposit + ${{returning['final_payment']}} final payment = ${{returning['total']}} total",
        "new_text": f"New Campers: ${{new['deposit']}} deposit + ${{new['final_payment']}} final payment = ${{new['total']}} total",
        "payment_deadline": f"Final payment due before {{CAMP_CONFIG['final_payment_due']}}. Camp runs {{CAMP_CONFIG['camp_dates']}}, {{CAMP_CONFIG['daily_hours']}} daily."
    }}

def get_session_summary():
    """Get a complete session summary for admin reference."""
    pricing = get_pricing_text()
    return {{
        "title": get_camp_title(),
        "subtitle": get_camp_subtitle(),
        "dates": CAMP_CONFIG["camp_dates"],
        "duration": f"{{CAMP_CONFIG['camp_days']}} days",
        "daily_schedule": CAMP_CONFIG["daily_hours"],
        "pricing": pricing,
        "features": CAMP_CONFIG.get("special_features", []),
        "status": "Open" if CAMP_CONFIG.get("registration_open", True) else "Closed"
    }}

def validate_config():
    """Validate that all required config fields are present."""
    required_fields = ["camp_name", "camp_dates", "camp_days", "daily_hours", "pricing"]
    missing_fields = []
    
    for field in required_fields:
        if field not in CAMP_CONFIG or not CAMP_CONFIG[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required config fields: {{missing_fields}}")
    
    # Validate pricing structure
    for camper_type in ["returning_camper", "new_camper"]:
        pricing = CAMP_CONFIG["pricing"][camper_type]
        total = pricing["deposit"] + pricing["final_payment"]
        if total != pricing["total"]:
            raise ValueError(f"Pricing calculation error for {{camper_type}}: {{total}} != {{pricing['total']}}")
    
    return True
'''
    
    with open('camp_config.py', 'w') as f:
        f.write(config_content)

@app.route('/api/registrations')
def api_registrations():
    """API endpoint for getting registration data."""
    conn = sqlite3.connect(REGISTRATION_DB)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute('''
        SELECT * FROM registrations 
        ORDER BY timestamp DESC
    ''')
    
    registrations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(registrations)

@app.route('/confirmation/<submission_id>')
def confirmation(submission_id):
    """Show confirmation page with registration details"""
    try:
        conn = sqlite3.connect(REGISTRATION_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM registrations WHERE submission_id = ?
        ''', (submission_id,))
        
        registration = cursor.fetchone()
        conn.close()
        
        if not registration:
            return "Registration not found", 404
        
        # Convert row to dictionary
        columns = [
            'id', 'submission_id', 'timestamp', 'child_first_name', 'child_last_name',
            'child_age', 'child_grade', 'parent_email', 'parent_phone',
            'emergency_contact_name', 'emergency_contact_phone', 'is_returning_camper',
            'bringing_own_switch', 'has_allergies', 'allergy_details',
            'has_sensory_issues', 'sensory_details', 'favorite_games',
            'gaming_behavior', 'game_restrictions', 'additional_notes', 'payment_status'
        ]
        
        registration_dict = dict(zip(columns, registration))
        
        return render_template('confirmation.html', registration=registration_dict)
        
    except Exception as e:
        return f"Error retrieving registration: {str(e)}", 500

@app.route('/admin/verify-returning-campers')
@require_admin_auth
def verify_returning_campers():
    """Admin tool to review returning camper claims."""
    conn = sqlite3.connect(REGISTRATION_DB)
    cursor = conn.cursor()
    
    # Get all registrations claiming to be returning campers
    cursor.execute('''
        SELECT 
            id, submission_id, child_first_name, child_last_name, parent_email,
            previous_year, previous_instructor, returning_camper_details,
            timestamp
        FROM registrations 
        WHERE is_returning_camper = 1
        ORDER BY timestamp DESC
    ''')
    
    returning_campers = cursor.fetchall()
    verified_campers = []
    
    for camper in returning_campers:
        # Check if this camper has previous registrations
        validation_result = check_returning_camper_validity(
            camper[2], camper[3], camper[4]  # first_name, last_name, email
        )
        
        verified_campers.append({
            'id': camper[0],
            'submission_id': camper[1],
            'name': f"{camper[2]} {camper[3]}",
            'email': camper[4],
            'previous_year': camper[5],
            'previous_instructor': camper[6],
            'details': camper[7],
            'timestamp': camper[8],
            'validation': validation_result,
            'verified': validation_result['is_likely_returning']
        })
    
    conn.close()
    
    # Create simple HTML response
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Returning Camper Verification</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .verified { background: #d4edda; border-left: 4px solid #28a745; }
            .unverified { background: #f8d7da; border-left: 4px solid #dc3545; }
            .camper { padding: 15px; margin: 10px 0; border-radius: 5px; }
            .warning { color: #721c24; font-weight: bold; }
            .details { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 3px; }
            .back-btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🔍 Returning Camper Verification Report</h1>
        <a href="/admin" class="back-btn">← Back to Admin Panel</a>
        <p>This report shows all registrations claiming returning camper status and their verification status.</p>
    '''
    
    if not verified_campers:
        html += '<p><em>No returning camper registrations found.</em></p>'
    
    for camper in verified_campers:
        status_class = 'verified' if camper['verified'] else 'unverified'
        status_text = '✅ VERIFIED' if camper['verified'] else '⚠️ NEEDS REVIEW'
        
        html += f'''
        <div class="camper {status_class}">
            <h3>{camper['name']} - {status_text}</h3>
            <p><strong>Email:</strong> {camper['email']}</p>
            <p><strong>Registration ID:</strong> {camper['submission_id']}</p>
            <p><strong>Submitted:</strong> {camper['timestamp']}</p>
            
            <div class="details">
                <p><strong>Previous Year Claimed:</strong> {camper['previous_year'] or 'Not provided'}</p>
                <p><strong>Staff Remembered:</strong> {camper['previous_instructor'] or 'Not provided'}</p>
                <p><strong>Previous Experience:</strong> {camper['details'] or 'Not provided'}</p>
            </div>
            
            <p><strong>Database Check:</strong> 
                {camper['validation']['exact_matches']} exact matches, 
                {camper['validation']['name_matches']} name matches
            </p>
            
            {f'<p class="warning">⚠️ ACTION REQUIRED: Contact this family to verify attendance or request additional payment.</p>' if not camper['verified'] else ''}
        </div>
        '''
    
    html += '''
        <div style="margin-top: 30px; padding: 20px; background: #e7f3ff; border-radius: 5px;">
            <h3>📋 Action Items for Unverified Claims:</h3>
            <ol>
                <li>Contact the family directly to verify previous attendance</li>
                <li>Check with previous year staff if names are provided</li>
                <li>Request payment adjustment if claim is invalid</li>
                <li>Update registration record with verification status</li>
            </ol>
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/admin/registration-stats')
@require_admin_auth
def registration_stats():
    """Show registration statistics including pricing breakdown."""
    conn = sqlite3.connect(REGISTRATION_DB)
    cursor = conn.cursor()
    
    # Get counts
    cursor.execute('SELECT COUNT(*) FROM registrations WHERE is_returning_camper = 1')
    returning_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM registrations WHERE is_returning_camper = 0')
    new_count = cursor.fetchone()[0]
    
    # Calculate potential revenue impact
    new_price = CAMP_CONFIG['pricing']['new_camper']['total']
    returning_price = CAMP_CONFIG['pricing']['returning_camper']['total']
    
    total_registrations = returning_count + new_count
    current_revenue = (returning_count * returning_price) + (new_count * new_price)
    if_all_new_revenue = total_registrations * new_price
    potential_lost_revenue = if_all_new_revenue - current_revenue
    
    return jsonify({
        'total_registrations': total_registrations,
        'returning_campers': returning_count,
        'new_campers': new_count,
        'pricing': {
            'new_camper_price': new_price,
            'returning_camper_price': returning_price,
            'discount_amount': new_price - returning_price
        },
        'revenue': {
            'current_total': current_revenue,
            'potential_if_all_new': if_all_new_revenue,
            'potential_lost': potential_lost_revenue
        }
    })

if __name__ == '__main__':
    init_registration_db()
    print("🏕️ Camp Power-Up Registration Form")
    print("=" * 40)
    
    # Use PORT environment variable for Railway, fallback to 5008 for local development
    port = int(os.environ.get('PORT', 5008))
    host = '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1'
    
    print(f"📝 Registration form available at: http://{host}:{port}")
    print(f"🔧 Admin dashboard available at: http://{host}:{port}/admin")
    app.run(debug=False, host=host, port=port)
else:
    # When imported by gunicorn, just initialize the database
    try:
        init_registration_db()
        print("✅ Registration database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        # Continue anyway - don't crash the app
