import pandas as pd
import sqlite3
import re
import json
from datetime import datetime, time
from flask import Flask, jsonify, render_template, request
import os
import math
from collections import Counter, defaultdict

app = Flask(__name__)

# Configuration
CSV_FILE_PATH = 'data/Camp_Power_Up_past_forms - Sheet1.csv'
DB_FILE = 'camp_power_up.db'
REGISTRATION_DB = 'registration_form/registration_submissions.db'


def get_challenge_db_path():
    """Use the shared registration DB for challenge leaderboard and signups."""
    return REGISTRATION_DB

LEADERBOARD_CHALLENGES = {
    'dk_bannooza': {
        'label': 'Donkey Kong Bananaza',
        'metric': 'Bananas in 10 minutes',
        'score_unit': 'bananas',
        'score_direction': 'desc',
        'show_starting_zone': True,
        'show_level_detail': False,
        'time_window': '10:00am – 11:30am',
        'rules': 'Pick a starting zone. Find as many bananas as possible in 10 minutes. Highest count wins. Tie-break: fastest completion time wins. Winners announced at 2:00pm.'
    },
    'mario_kart_world': {
        'label': 'Mario Kart World - Knockout Tour',
        'metric': 'Final placement / points',
        'score_unit': 'points',
        'score_direction': 'asc',
        'show_starting_zone': False,
        'show_level_detail': False,
        'show_race_round': True,
        'time_window': '11:30am – 1:30pm',
        'rules': 'Each kid gets ONE turn with up to 3 races. Score is cumulative placement points (lower is better). Example: 3rd + 2nd + 1st = 6 points. Tie-break: fastest completion time wins. Winners announced at 2:00pm.'
    },
    'hollow_knight_boss_rush': {
        'label': 'Hollow Knight Boss Rush',
        'metric': 'Bosses defeated',
        'score_unit': 'bosses',
        'score_direction': 'desc',
        'show_starting_zone': False,
        'show_level_detail': True,
        'time_window': '1:30pm – 3:00pm',
        'rules': 'Enter Pantheon mode at your chosen difficulty. Score = bosses defeated before losing all health. Tie-break: fastest completion time wins. Record level/difficulty. Winners announced at 2:00pm.'
    }
}


def ensure_leaderboard_table():
    """Create leaderboard table if it does not already exist."""
    conn = sqlite3.connect(get_challenge_db_path())
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS challenge_leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camper_name TEXT NOT NULL,
                challenge_key TEXT NOT NULL,
                score INTEGER NOT NULL,
                starting_zone TEXT,
                level_detail TEXT,
                race_round INTEGER,
                completion_time_seconds INTEGER,
                run_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Backward-compatible migration for existing DBs.
        existing_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(challenge_leaderboard)").fetchall()
        }
        if 'completion_time_seconds' not in existing_cols:
            conn.execute(
                'ALTER TABLE challenge_leaderboard ADD COLUMN completion_time_seconds INTEGER'
            )
        if 'race_round' not in existing_cols:
            conn.execute(
                'ALTER TABLE challenge_leaderboard ADD COLUMN race_round INTEGER'
            )

        conn.commit()
    finally:
        conn.close()


def parse_completion_time_to_seconds(raw_value):
    """Parse completion time as seconds. Accepts '', integer seconds, or mm:ss."""
    if raw_value is None:
        return None

    value = str(raw_value).strip()
    if not value:
        return None

    if re.fullmatch(r'\d+', value):
        seconds = int(value)
        if seconds < 0:
            raise ValueError('Completion time must be 0 or greater.')
        return seconds

    match = re.fullmatch(r'(\d{1,2}):(\d{2})', value)
    if match:
        minutes = int(match.group(1))
        secs = int(match.group(2))
        if secs >= 60:
            raise ValueError('Use mm:ss format with seconds from 00 to 59.')
        return (minutes * 60) + secs

    raise ValueError('Completion time must be seconds (e.g. 95) or mm:ss (e.g. 1:35).')


def parse_completion_hms_to_seconds(hours_raw, minutes_raw, seconds_raw):
    """Parse completion time from hour/minute/second fields."""
    h_val = str(hours_raw or '').strip()
    m_val = str(minutes_raw or '').strip()
    s_val = str(seconds_raw or '').strip()

    if not h_val and not m_val and not s_val:
        return None

    if h_val and not re.fullmatch(r'\d+', h_val):
        raise ValueError('Hours must be a whole number.')
    if m_val and not re.fullmatch(r'\d+', m_val):
        raise ValueError('Minutes must be a whole number.')
    if s_val and not re.fullmatch(r'\d+', s_val):
        raise ValueError('Seconds must be a whole number.')

    hours = int(h_val) if h_val else 0
    minutes = int(m_val) if m_val else 0
    seconds = int(s_val) if s_val else 0

    if minutes >= 60 or seconds >= 60:
        raise ValueError('Minutes and seconds must be between 0 and 59.')

    return (hours * 3600) + (minutes * 60) + seconds


def is_submission_locked_after_2pm():
    """Return True after 2:00pm local server time."""
    return datetime.now().time() >= time(14, 0)


def fetch_leaderboard_data():
    """Fetch ranked leaderboard entries for all configured challenges."""
    ensure_leaderboard_table()
    conn = sqlite3.connect(get_challenge_db_path())
    conn.row_factory = sqlite3.Row
    try:
        leaderboard = {}
        for challenge_key, challenge_info in LEADERBOARD_CHALLENGES.items():
            rows = conn.execute(
                '''
                SELECT id, camper_name, challenge_key, score, starting_zone, level_detail, race_round, completion_time_seconds, run_notes, created_at
                FROM challenge_leaderboard
                WHERE challenge_key = ?
                ''',
                (challenge_key,)
            ).fetchall()

            if challenge_info.get('show_race_round'):
                summary_map = {}
                for row in rows:
                    camper_key = row['camper_name'].strip().lower()
                    group = summary_map.setdefault(camper_key, {
                        'camper_name': row['camper_name'],
                        'total_score': 0,
                        'best_time_seconds': None,
                        'race_count': 0,
                        'race_breakdown': [],
                        'created_at': row['created_at']
                    })
                    group['total_score'] += int(row['score'])
                    if row['completion_time_seconds'] is not None:
                        current_time = row['completion_time_seconds']
                        if group['best_time_seconds'] is None or current_time < group['best_time_seconds']:
                            group['best_time_seconds'] = current_time
                    group['race_count'] += 1
                    group['race_breakdown'].append({
                        'race_round': row['race_round'],
                        'score': int(row['score']),
                        'completion_time_seconds': row['completion_time_seconds'],
                        'run_notes': row['run_notes'] or '',
                        'created_at': row['created_at']
                    })

                summary_entries = []
                grouped_rows = sorted(
                    summary_map.values(),
                    key=lambda item: (
                        item['total_score'],
                        item['best_time_seconds'] if item['best_time_seconds'] is not None else 10**9,
                        item['created_at']
                    )
                )
                for idx, group in enumerate(grouped_rows, start=1):
                    breakdown = sorted(group['race_breakdown'], key=lambda item: item['race_round'] or 0)
                    summary_entries.append({
                        'rank': idx,
                        'id': breakdown[-1]['created_at'] if breakdown else idx,
                        'camper_name': group['camper_name'],
                        'challenge_key': challenge_key,
                        'score': group['total_score'],
                        'total_score': group['total_score'],
                        'best_time_seconds': group['best_time_seconds'],
                        'race_count': group['race_count'],
                        'race_breakdown': breakdown,
                        'race_round': breakdown[-1]['race_round'] if breakdown else None,
                        'starting_zone': '',
                        'level_detail': '',
                        'completion_time_seconds': group['best_time_seconds'],
                        'run_notes': '',
                        'created_at': group['created_at']
                    })

                detail_rows = sorted(
                    rows,
                    key=lambda row: (
                        row['camper_name'].lower(),
                        row['race_round'] if row['race_round'] is not None else 99,
                        row['created_at']
                    )
                )
                entries = [
                    {
                        'rank': idx,
                        'id': row['id'],
                        'camper_name': row['camper_name'],
                        'challenge_key': row['challenge_key'],
                        'score': row['score'],
                        'starting_zone': row['starting_zone'] or '',
                        'level_detail': row['level_detail'] or '',
                        'race_round': row['race_round'],
                        'completion_time_seconds': row['completion_time_seconds'],
                        'run_notes': row['run_notes'] or '',
                        'created_at': row['created_at']
                    }
                    for idx, row in enumerate(detail_rows, start=1)
                ]

                leaderboard[challenge_key] = {
                    'challenge': challenge_info,
                    'entries': entries,
                    'summary_entries': summary_entries,
                    'trophy_winner': summary_entries[0] if summary_entries else None
                }
            else:
                reverse_scores = challenge_info.get('score_direction', 'desc') != 'asc'
                sorted_rows = sorted(
                    rows,
                    key=lambda row: (
                        row['score'],
                        row['completion_time_seconds'] if row['completion_time_seconds'] is not None else 10**9,
                        row['created_at']
                    ),
                    reverse=reverse_scores
                )

                if reverse_scores:
                    # Keep tie-break as fastest time even for descending score challenges.
                    sorted_rows = sorted(
                        sorted_rows,
                        key=lambda row: row['completion_time_seconds'] if row['completion_time_seconds'] is not None else 10**9
                    )
                    sorted_rows = sorted(
                        sorted_rows,
                        key=lambda row: row['score'],
                        reverse=True
                    )

                entries = []
                for idx, row in enumerate(sorted_rows, start=1):
                    entries.append({
                        'rank': idx,
                        'id': row['id'],
                        'camper_name': row['camper_name'],
                        'challenge_key': row['challenge_key'],
                        'score': row['score'],
                        'starting_zone': row['starting_zone'] or '',
                        'level_detail': row['level_detail'] or '',
                        'race_round': row['race_round'],
                        'completion_time_seconds': row['completion_time_seconds'],
                        'run_notes': row['run_notes'] or '',
                        'created_at': row['created_at']
                    })

                leaderboard[challenge_key] = {
                    'challenge': challenge_info,
                    'entries': entries,
                    'trophy_winner': entries[0] if entries else None
                }

        return leaderboard
    finally:
        conn.close()

def get_combined_camper_data():
    """Get combined camper data from both historical CSV and new registrations."""
    combined_data = []
    
    # 1. Load historical data from main database
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='campers'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT first_name, last_name, email, age, grade, is_returning, 
                           has_allergies, allergy_description, has_sensory_issues, sensory_description,
                           bringing_switch, favorite_games, game_behavior
                    FROM campers
                """)
                historical_records = cursor.fetchall()
                
                for record in historical_records:
                    combined_data.append({
                        'first_name': record[0] or '',
                        'last_name': record[1] or '',
                        'email': record[2] or '',
                        'age': record[3] or 0,
                        'grade': record[4] or '',
                        'is_returning': record[5] == 'Yes',
                        'has_allergies': record[6] == 'Yes',
                        'allergy_details': record[7] or '',
                        'has_sensory_issues': record[8] == 'Yes', 
                        'sensory_details': record[9] or '',
                        'bringing_switch': record[10] == 'Yes',
                        'favorite_games': record[11] or '',
                        'game_behavior': record[12] or '',
                        'source': 'historical',
                        'submission_id': None,
                        'timestamp': None,
                        'status': 'historical'
                    })
        except Exception as e:
            print(f"Warning: Could not load historical data: {e}")
        finally:
            conn.close()
    
    # 2. Load new registration data
    if os.path.exists(REGISTRATION_DB):
        conn = sqlite3.connect(REGISTRATION_DB)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT child_first_name, child_last_name, parent_email, child_age, child_grade,
                       is_returning_camper, has_allergies, allergy_details, has_sensory_issues, 
                       sensory_details, bringing_own_switch, favorite_games, gaming_behavior,
                       submission_id, timestamp, status
                FROM registrations
                ORDER BY timestamp DESC
            """)
            new_records = cursor.fetchall()
            
            for record in new_records:
                combined_data.append({
                    'first_name': record[0] or '',
                    'last_name': record[1] or '', 
                    'email': record[2] or '',
                    'age': record[3] or 0,
                    'grade': record[4] or '',
                    'is_returning': bool(record[5]),
                    'has_allergies': bool(record[6]),
                    'allergy_details': record[7] or '',
                    'has_sensory_issues': bool(record[8]),
                    'sensory_details': record[9] or '',
                    'bringing_switch': bool(record[10]),
                    'favorite_games': record[11] or '',
                    'game_behavior': record[12] or '',
                    'source': 'new_registration',
                    'submission_id': record[13],
                    'timestamp': record[14],
                    'status': record[15] or 'pending'
                })
        except Exception as e:
            print(f"Warning: Could not load new registration data: {e}")
        finally:
            conn.close()
    
    return combined_data

def clean_and_combine_data():
    """Loads, cleans, and combines data from the CSV file."""
    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ Error: File not found at {CSV_FILE_PATH}")
        return

    print(f"📁 Reading data from {CSV_FILE_PATH}...")
    df = pd.read_csv(CSV_FILE_PATH)
    
    print(f"📊 Original dataset has {len(df)} rows and {len(df.columns)} columns")
    
    # Remove duplicate rows based on child's name and email
    initial_count = len(df)
    df = df.drop_duplicates(subset=['Email Address', 'Childs First Name?', 'Childs Last Name?'], keep='last')
    removed_duplicates = initial_count - len(df)
    if removed_duplicates > 0:
        print(f"🧹 Removed {removed_duplicates} duplicate entries")
    
    # Create a clean, standardized dataset
    clean_df = pd.DataFrame()
    
    # Basic information - combine and clean
    clean_df['first_name'] = df['Childs First Name?'].str.strip()
    clean_df['last_name'] = df['Childs Last Name?'].str.strip()
    clean_df['email'] = df['Email Address'].str.strip().str.lower()
    
    # Age - convert to numeric and handle various formats
    clean_df['age'] = pd.to_numeric(df['Age?'], errors='coerce')
    
    # Grade - standardize grade formats
    grade_col = df['Grade?'].fillna('').astype(str).str.strip()
    clean_df['grade'] = grade_col.replace('', 'Unknown')
    
    # Returning camper status
    returning_col = df['Has your Child attended Camp Power-Up before?'].fillna('No')
    clean_df['is_returning'] = returning_col.str.strip()
    
    # Game behavior description
    behavior_col = df['Can you describe what your child is like playing video games around others? Are they good at taking turns? Are they a good sport?']
    clean_df['game_behavior'] = behavior_col.fillna('Not specified').str.strip()
    
    # Game ratings restrictions
    rating_col = df['Is there a rating of games your child is not allowed to play?']
    clean_df['rating_restrictions'] = rating_col.fillna('Not specified').str.strip()
    
    # Switch bringing status
    switch_col = df['Will your child be bringing their own personal Switch?']
    clean_df['bringing_switch'] = switch_col.fillna('Not specified').str.strip()
    
    # Social media consent
    social_col = df['do you consent for your childs image to be used on social media platforms to promote the Camp Power Up?']
    clean_df['social_media_consent'] = social_col.fillna('Not specified').str.strip()
    
    # Sensory issues
    sensory_col = df['any sensory issues?']
    sensory_desc_col = df['If yes please describe?  ']
    clean_df['has_sensory_issues'] = sensory_col.fillna('No').str.strip()
    clean_df['sensory_description'] = sensory_desc_col.fillna('').str.strip()
    
    # Allergies
    allergy_col = df['allergies?']
    allergy_desc_col = df['If yes, please list any medical conditions or allergies']
    clean_df['has_allergies'] = allergy_col.fillna('No').str.strip()
    clean_df['allergy_description'] = allergy_desc_col.fillna('').str.strip()
    
    # Games they enjoy
    games_col = df['What games do they enjoy playing?']
    top_games_col = df['List your child\'s top 5 games they like to play']
    clean_df['favorite_games'] = games_col.fillna('').str.strip()
    clean_df['top_5_games'] = top_games_col.fillna('').str.strip()
    
    # Console experience
    console_col = df['Has your child played on any of these consoles?']
    console_games_col = df['What games has your child played on those systems?']
    clean_df['console_experience'] = console_col.fillna('').str.strip()
    clean_df['console_games'] = console_games_col.fillna('').str.strip()
    
    # Remove rows where essential data is missing
    clean_df = clean_df.dropna(subset=['first_name', 'last_name'])
    clean_df = clean_df[clean_df['first_name'].str.strip() != '']
    clean_df = clean_df[clean_df['last_name'].str.strip() != '']
    
    print(f"✅ Cleaned dataset has {len(clean_df)} complete records")
    
    # Save to database
    conn = sqlite3.connect(DB_FILE)
    clean_df.to_sql('campers', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"💾 Data saved to {DB_FILE}")
    
    # Print summary statistics
    print(f"\n📈 Summary Statistics:")
    print(f"   • Total campers: {len(clean_df)}")
    print(f"   • Returning campers: {len(clean_df[clean_df['is_returning'] == 'Yes'])}")
    print(f"   • Age range: {clean_df['age'].min():.0f} - {clean_df['age'].max():.0f} years")
    print(f"   • With sensory issues: {len(clean_df[clean_df['has_sensory_issues'] == 'Yes'])}")
    print(f"   • With allergies: {len(clean_df[clean_df['has_allergies'] == 'Yes'])}")
    print(f"   • Bringing own Switch: {len(clean_df[clean_df['bringing_switch'] == 'Yes'])}")

@app.route('/')
def index():
    """Serves the main dashboard page."""
    return render_template('index.html')

@app.route('/campers')
def campers_page():
    """Serves the interactive campers list page."""
    return render_template('campers.html')


@app.route('/leaderboard')
def leaderboard_page():
    """Serves the challenge leaderboard page."""
    return render_template('leaderboard.html')


@app.route('/api/leaderboard/challenges')
def get_leaderboard_challenges():
    """Get configured challenge metadata for the leaderboard UI."""
    return jsonify(LEADERBOARD_CHALLENGES)


@app.route('/api/leaderboard')
def get_leaderboard():
    """Get all leaderboard entries grouped by challenge."""
    return jsonify(fetch_leaderboard_data())


@app.route('/api/leaderboard/submit', methods=['POST'])
def submit_leaderboard_score():
    """Submit one camper score to the challenge leaderboard."""
    data = request.get_json(silent=True) or {}

    camper_name = str(data.get('camper_name', '')).strip()
    challenge_key = str(data.get('challenge_key', '')).strip()
    starting_zone = str(data.get('starting_zone', '')).strip()
    level_detail = str(data.get('level_detail', '')).strip()
    race_round_raw = data.get('race_round', '')
    completion_time = data.get('completion_time', '')
    completion_hours = data.get('completion_hours', '')
    completion_minutes = data.get('completion_minutes', '')
    completion_seconds_raw = data.get('completion_seconds', '')
    allow_after_deadline = bool(data.get('allow_after_deadline', False))
    run_notes = str(data.get('run_notes', '')).strip()

    if not camper_name:
        return jsonify({'error': 'Camper name is required.'}), 400

    if challenge_key not in LEADERBOARD_CHALLENGES:
        return jsonify({'error': 'Invalid challenge selected.'}), 400

    challenge_info = LEADERBOARD_CHALLENGES[challenge_key]
    race_round = None
    if challenge_info.get('show_race_round'):
        try:
            race_round = int(race_round_raw)
        except (TypeError, ValueError):
            return jsonify({'error': 'Race / Heat is required for Mario Kart.'}), 400
        if race_round < 1 or race_round > 3:
            return jsonify({'error': 'Race / Heat must be 1, 2, or 3.'}), 400

    if is_submission_locked_after_2pm() and not allow_after_deadline:
        return jsonify({'error': 'Score entry is locked after 2:00pm. Enable staff override to submit.'}), 400

    try:
        score = int(data.get('score'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Score must be a whole number.'}), 400

    if score < 0:
        return jsonify({'error': 'Score must be 0 or greater.'}), 400

    try:
        completion_time_seconds = parse_completion_hms_to_seconds(
            completion_hours,
            completion_minutes,
            completion_seconds_raw
        )
        if completion_time_seconds is None:
            completion_time_seconds = parse_completion_time_to_seconds(completion_time)
    except ValueError as err:
        return jsonify({'error': str(err)}), 400

    ensure_leaderboard_table()
    conn = sqlite3.connect(get_challenge_db_path())
    try:
        if race_round is not None:
            existing = conn.execute(
                '''
                SELECT COUNT(*)
                FROM challenge_leaderboard
                WHERE challenge_key = ? AND camper_name = ? AND race_round = ?
                ''',
                (challenge_key, camper_name, race_round)
            ).fetchone()[0]
            if existing:
                return jsonify({'error': 'That camper already has a score for this race number.'}), 400

        conn.execute(
            '''
            INSERT INTO challenge_leaderboard (camper_name, challenge_key, score, starting_zone, level_detail, race_round, completion_time_seconds, run_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                camper_name,
                challenge_key,
                score,
                starting_zone or None,
                level_detail or None,
                race_round,
                completion_time_seconds,
                run_notes or None
            )
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        'success': True,
        'message': 'Score submitted successfully.',
        'leaderboard': fetch_leaderboard_data()
    })


# ─────────────────────────────────────────────────────────
# Challenge Sign-Up Queue
# ─────────────────────────────────────────────────────────

def ensure_signups_table():
    """Create challenge_signups table if it does not already exist."""
    conn = sqlite3.connect(get_challenge_db_path())
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS challenge_signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camper_name TEXT NOT NULL,
                challenge_key TEXT NOT NULL,
                status TEXT DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    finally:
        conn.close()


def fetch_signup_queues():
    """Return all sign-up queues grouped by challenge, ordered by sign-up time."""
    ensure_signups_table()
    conn = sqlite3.connect(get_challenge_db_path())
    conn.row_factory = sqlite3.Row
    try:
        queues = {}
        for key, info in LEADERBOARD_CHALLENGES.items():
            rows = conn.execute(
                'SELECT id, camper_name, challenge_key, status, created_at FROM challenge_signups WHERE challenge_key = ? ORDER BY created_at ASC',
                (key,)
            ).fetchall()
            queues[key] = {
                'challenge': info,
                'entries': [dict(r) for r in rows]
            }
        return queues
    finally:
        conn.close()


@app.route('/api/signups')
def get_signups():
    return jsonify(fetch_signup_queues())


@app.route('/api/signups/add', methods=['POST'])
def add_signup():
    data = request.get_json(silent=True) or {}
    camper_name = str(data.get('camper_name', '')).strip()
    challenge_key = str(data.get('challenge_key', '')).strip()
    if not camper_name:
        return jsonify({'error': 'Camper name is required.'}), 400
    if challenge_key not in LEADERBOARD_CHALLENGES:
        return jsonify({'error': 'Invalid challenge.'}), 400
    conn = sqlite3.connect(get_challenge_db_path())
    try:
        conn.execute('INSERT INTO challenge_signups (camper_name, challenge_key, status) VALUES (?, ?, ?)', (camper_name, challenge_key, 'waiting'))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'queues': fetch_signup_queues()})


@app.route('/api/signups/<int:signup_id>/status', methods=['POST'])
def update_signup_status(signup_id):
    data = request.get_json(silent=True) or {}
    new_status = str(data.get('status', '')).strip()
    if new_status not in ('waiting', 'playing', 'done', 'skipped'):
        return jsonify({'error': 'Invalid status.'}), 400
    conn = sqlite3.connect(get_challenge_db_path())
    try:
        conn.execute('UPDATE challenge_signups SET status = ? WHERE id = ?', (new_status, signup_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'queues': fetch_signup_queues()})


@app.route('/api/signups/<int:signup_id>/remove', methods=['DELETE'])
def remove_signup(signup_id):
    conn = sqlite3.connect(get_challenge_db_path())
    try:
        conn.execute('DELETE FROM challenge_signups WHERE id = ?', (signup_id,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'queues': fetch_signup_queues()})


@app.route('/api/stats')
def get_stats():
    """Get basic statistics about the campers from combined data sources.
    
    Note: Sensitive medical data (allergies, sensory needs) is excluded from
    public stats for privacy. This info is available in admin dashboard only.
    """
    combined_data = get_combined_camper_data()
    
    if not combined_data:
        return jsonify({
            'total_campers': 0,
            'returning_campers': 0,
            'bringing_switch': 0,
            'new_registrations': 0,
            'historical_records': 0
        })
    
    # Calculate statistics from combined data
    # Sensitive data (allergies, sensory) excluded for privacy
    total_campers = len(combined_data)
    returning_campers = sum(1 for camper in combined_data if camper['is_returning'])
    bringing_switch = sum(1 for camper in combined_data if camper['bringing_switch'])
    
    # Additional stats for data sources
    new_registrations = sum(1 for camper in combined_data if camper['source'] == 'new_registration')
    historical_records = sum(1 for camper in combined_data if camper['source'] == 'historical')
    
    return jsonify({
        'total_campers': total_campers,
        'returning_campers': returning_campers,
        'bringing_switch': bringing_switch,
        'new_registrations': new_registrations,
        'historical_records': historical_records
    })

@app.route('/api/data/<query>')
def get_data(query):
    """API endpoint to fetch data for charts."""
    conn = sqlite3.connect(DB_FILE)
    
    if query == 'age_distribution':
        cursor = conn.execute("SELECT age, COUNT(*) FROM campers WHERE age IS NOT NULL GROUP BY age ORDER BY age")
    elif query == 'grade_distribution':
        cursor = conn.execute("SELECT grade, COUNT(*) FROM campers WHERE grade != 'Unknown' GROUP BY grade")
    elif query == 'returning_status':
        cursor = conn.execute("SELECT is_returning, COUNT(*) FROM campers GROUP BY is_returning")
    elif query == 'switch_status':
        cursor = conn.execute("SELECT bringing_switch, COUNT(*) FROM campers GROUP BY bringing_switch")
    elif query == 'consent_status':
        cursor = conn.execute("SELECT social_media_consent, COUNT(*) FROM campers GROUP BY social_media_consent")
    elif query == 'popular_games':
        # Get all game data and parse it
        cursor = conn.execute("""
            SELECT favorite_games, top_5_games, console_games, game_behavior 
            FROM campers 
            WHERE favorite_games != '' OR top_5_games != '' OR console_games != '' OR game_behavior != 'Not specified'
        """)
        
        game_counts = {}
        for row in cursor.fetchall():
            # Combine all game text and parse (including behavior descriptions)
            all_games_text = f"{row[0]} {row[1]} {row[2]} {row[3]}".lower()
            
            # Common game names to look for
            games_to_find = [
                'minecraft', 'roblox', 'mario kart', 'mario', 'pokemon', 'zelda',
                'fortnite', 'animal crossing', 'splatoon', 'smash bros', 'smash',
                'sonic', 'kirby', 'luigi', 'bowser', 'yoshi', 'pikmin', 'metroid'
            ]
            
            for game in games_to_find:
                if game in all_games_text:
                    game_counts[game] = game_counts.get(game, 0) + 1
        
        # Convert to format expected by frontend
        popular_games = [(game, count) for game, count in sorted(game_counts.items(), key=lambda x: x[1], reverse=True)]
        conn.close()
        return jsonify(popular_games[:10])  # Top 10 games
    else:
        conn.close()
        return jsonify({"error": "Invalid query"}), 400
    
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/campers')
def get_campers():
    """Get the list of campers from combined data sources.
    
    Note: Sensitive medical data (allergies, sensory needs) is excluded from
    public API for privacy. This info is available in admin dashboard only.
    """
    combined_data = get_combined_camper_data()
    
    # Format data - exclude sensitive medical information for privacy
    formatted_campers = []
    for camper in combined_data:
        formatted_camper = {
            'first_name': camper['first_name'],
            'last_name': camper['last_name'],
            'age': camper['age'],
            'grade': camper.get('grade', ''),
            'is_returning': 'Yes' if camper['is_returning'] else 'No',
            'bringing_switch': 'Yes' if camper['bringing_switch'] else 'No'
            # Note: has_allergies and has_sensory_issues removed for privacy
        }
        formatted_campers.append(formatted_camper)
    
    return jsonify(formatted_campers)

# Note: /api/special_needs endpoint has been removed for privacy.
# Sensitive medical data (allergies, sensory needs) is now only available
# through the authenticated admin dashboard at /admin.
# See registration_form/app.py for admin-only access to this data.

@app.route('/api/games')
def get_games():
    """Get detailed game preferences for campers from combined data."""
    combined_data = get_combined_camper_data()
    
    games_data = []
    for camper in combined_data:
        # Only include campers with game preferences
        has_preferences = any([
            camper.get('favorite_games'),
            camper.get('top_5_games'),  
            camper.get('console_games'),
            camper.get('game_behavior') and camper.get('game_behavior') != 'Not specified'
        ])
        
        if has_preferences:
            games_data.append({
                'name': f"{camper['first_name']} {camper['last_name']}",
                'favorite_games': camper.get('favorite_games', ''),
                'top_5_games': camper.get('top_5_games', ''),
                'console_games': camper.get('console_games', ''),
                'rating_restrictions': camper.get('rating_restrictions', ''),
                'game_behavior': camper.get('game_behavior', '')
            })
    
    return jsonify(games_data)


@app.route('/api/medical_alerts')
def medical_alerts():
    """Get campers with allergies/medical needs for easy reference."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    medical_needs = []
    
    # Get campers with allergies
    allergy_cursor = conn.execute("""
        SELECT first_name, last_name, allergy_description 
        FROM campers 
        WHERE has_allergies = 'Yes' AND allergy_description != ''
    """)
    
    for row in allergy_cursor:
        medical_needs.append({
            'name': f"{row['first_name']} {row['last_name']}",
            'type': 'Allergies',
            'description': row['allergy_description']
        })
    
    # Get campers with sensory issues
    sensory_cursor = conn.execute("""
        SELECT first_name, last_name, sensory_description 
        FROM campers 
        WHERE has_sensory_issues = 'Yes' AND sensory_description != ''
    """)
    
    for row in sensory_cursor:
        medical_needs.append({
            'name': f"{row['first_name']} {row['last_name']}",
            'type': 'Sensory Issues',
            'description': row['sensory_description']
        })
    
    conn.close()
    return jsonify(medical_needs)

def extract_games_from_text(text):
    """Extract and normalize game names from a given text."""
    if not text or text.strip() == '':
        return []
    
    # Simple normalization - lowercase and remove extra spaces
    normalized_text = re.sub(r'\s+', ' ', text.strip().lower())
    
    # Split by common delimiters, but keep 'and' for multi-game entries
    games = re.split(r',|;|&', normalized_text)
    
    # Further split by 'vs' or 'with' for competitive/cooperative games
    all_games = []
    for game in games:
        sub_games = re.split(r' vs | with ', game.strip())
        all_games.extend([g.strip() for g in sub_games if g.strip() != ''])
    
    return list(set(all_games))  # Unique games only

def assign_groups(target_group_size=8, max_group_size=10):
    """Intelligently assigns campers to balanced groups."""
    conn = sqlite3.connect(DB_FILE)
    
    # First, let's check what columns actually exist
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(registrations)")
    columns = [row[1] for row in cursor.fetchall()]
    print("Available columns:", columns)
    
    # Get all camper data using the correct column names
    query = """
    SELECT childs_first_name, childs_last_name, age, grade, returning_camper, bringing_switch, 
           allergies, sensory_issues, game_behavior, favorite_games
    FROM registrations 
    WHERE childs_first_name IS NOT NULL
    ORDER BY age, returning_camper DESC
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Combine first and last names
        df['camper_name'] = (df['childs_first_name'].astype(str) + ' ' + 
                             df['childs_last_name'].astype(str)).str.strip()
        
    except Exception as e:
        print(f"SQL Error: {e}")
        # Fallback: try to find the actual name columns
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations LIMIT 1")
        sample_row = cursor.fetchone()
        cursor.execute("PRAGMA table_info(registrations)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        
        print("Available columns for debugging:", columns)
        return []
    
    # Clean and prepare data
    df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(8)
    df['has_special_needs'] = (df['allergies'].notna() & (df['allergies'] != '')) | \
                             (df['sensory_issues'].notna() & (df['sensory_issues'] != ''))
    
    # Calculate number of groups needed
    total_campers = len(df)
    if total_campers == 0:
        return []
        
    num_groups = max(1, math.ceil(total_campers / target_group_size))
    
    # Initialize groups
    groups = [[] for _ in range(num_groups)]
    group_stats = [{'total': 0, 'age_sum': 0, 'returning': 0, 'special_needs': 0, 'switches': 0} 
                   for _ in range(num_groups)]
    
    # Sort campers by age for even distribution
    df_sorted = df.sort_values(['age', 'returning_camper'], ascending=[True, False])
    
    for idx, camper in df_sorted.iterrows():
        # Find the group with the least campers, considering balance
        best_group = 0
        best_score = float('inf')
        
        for i in range(num_groups):
            if len(groups[i]) >= max_group_size:
                continue
                
            # Calculate balance score (lower is better)
            current_avg_age = group_stats[i]['age_sum'] / max(1, group_stats[i]['total'])
            new_avg_age = (group_stats[i]['age_sum'] + camper['age']) / (group_stats[i]['total'] + 1)
            
            score = (
                len(groups[i]) * 10 +  # Prefer smaller groups
                abs(new_avg_age - df['age'].mean()) * 5 +  # Age balance
                (group_stats[i]['special_needs'] * 3 if camper['has_special_needs'] else 0)  # Distribute special needs
            )
            
            if score < best_score:
                best_score = score
                best_group = i
        
        # Assign camper to best group
        groups[best_group].append({
            'name': camper['camper_name'],
            'age': int(camper['age']) if camper['age'] > 0 else 8,
            'grade': camper['grade'] if pd.notna(camper['grade']) else 'Unknown',
            'returning': bool(camper['returning_camper']) if pd.notna(camper['returning_camper']) else False,
            'bringing_switch': bool(camper['bringing_switch']) if pd.notna(camper['bringing_switch']) else False,
            'has_allergies': bool(camper['allergies'] and str(camper['allergies']).strip()) if pd.notna(camper['allergies']) else False,
            'has_sensory_issues': bool(camper['sensory_issues'] and str(camper['sensory_issues']).strip()) if pd.notna(camper['sensory_issues']) else False,
            'special_needs': camper['has_special_needs'],
            'game_behavior': camper['game_behavior'] if pd.notna(camper['game_behavior']) else '',
            'favorite_games': camper['favorite_games'] if pd.notna(camper['favorite_games']) else ''
        })
        
        # Update group stats
        group_stats[best_group]['total'] += 1
        group_stats[best_group]['age_sum'] += camper['age']
        group_stats[best_group]['returning'] += 1 if (pd.notna(camper['returning_camper']) and camper['returning_camper']) else 0
        group_stats[best_group]['special_needs'] += 1 if camper['has_special_needs'] else 0
        group_stats[best_group]['switches'] += 1 if (pd.notna(camper['bringing_switch']) and camper['bringing_switch']) else 0
    
    # Create group summaries
    group_summaries = []
    for i, group in enumerate(groups):
        if not group:
            continue
            
        ages = [c['age'] for c in group if isinstance(c['age'], int)]
        avg_age = sum(ages) / len(ages) if ages else 8
        
        # Analyze group game preferences
        all_games = []
        for camper in group:
            if camper['favorite_games']:
                all_games.extend(extract_games_from_text(str(camper['favorite_games'])))
            if camper['game_behavior']:
                all_games.extend(extract_games_from_text(str(camper['game_behavior'])))
        
        popular_games = Counter(all_games).most_common(3)
        
        group_summaries.append({
            'group_id': i + 1,
            'group_name': f"Group {i + 1}",
            'campers': group,
            'stats': {
                'total_campers': len(group),
                'avg_age': round(avg_age, 1),
                'age_range': f"{min(ages) if ages else 8}-{max(ages) if ages else 8}",
                'returning_campers': sum(1 for c in group if c['returning']),
                'new_campers': sum(1 for c in group if not c['returning']),
                'switches_available': sum(1 for c in group if c['bringing_switch']),
                'switches_needed': len(group) - sum(1 for c in group if c['bringing_switch']),
                'special_needs_count': sum(1 for c in group if c['special_needs']),
                'popular_games': [{'game': game, 'count': count} for game, count in popular_games]
            }
        })
    
    return group_summaries

@app.route('/api/groups')
def get_groups():
    """API endpoint to get group assignments."""
    try:
        target_size = request.args.get('size', 8, type=int)
        max_size = request.args.get('max_size', 10, type=int)
        groups = assign_groups(target_size, max_size)
        return jsonify(groups)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/group_stats')
def get_group_stats():
    """API endpoint to get overall group statistics."""
    try:
        groups = assign_groups()
        
        total_groups = len(groups)
        total_campers = sum(g['stats']['total_campers'] for g in groups)
        total_special_needs = sum(g['stats']['special_needs_count'] for g in groups)
        total_switches_needed = sum(g['stats']['switches_needed'] for g in groups)
        
        return jsonify({
            'total_groups': total_groups,
            'total_campers': total_campers,
            'avg_group_size': round(total_campers / total_groups, 1) if total_groups > 0 else 0,
            'total_special_needs': total_special_needs,
            'total_switches_needed': total_switches_needed,
            'groups_with_special_needs': sum(1 for g in groups if g['stats']['special_needs_count'] > 0)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/game_library')
def game_library():
    """Game library management page."""
    return render_template('game_library.html')

@app.route('/api/game_library/stats')
def get_game_library_stats():
    """Get game library statistics."""
    try:
        from game_library import get_game_library_stats
        stats = get_game_library_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/game_library/process')
def process_game_library():
    """Process camper game data and populate library."""
    try:
        from game_library import process_camper_games
        game_counts = process_camper_games()
        return jsonify({
            "success": True,
            "message": f"Processed {len(game_counts)} unique games",
            "top_games": game_counts.most_common(10)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/game_library/update', methods=['POST'])
def update_game():
    """Update game availability or camp copies."""
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        camp_copies = data.get('camp_copies', 0)
        availability_status = data.get('availability_status', 'Available')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE games 
            SET camp_copies = ?, availability_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (camp_copies, availability_status, game_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Game updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🏕️ Camp Power-Up Data Management System")
    print("=" * 50)
    clean_and_combine_data()
    print("\n🚀 Starting web server...")
    print("📱 Dashboard available at: http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
