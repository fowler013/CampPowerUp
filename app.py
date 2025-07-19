import pandas as pd
import sqlite3
import re
import json
from flask import Flask, jsonify, render_template, request
import os
import math
from collections import Counter, defaultdict

app = Flask(__name__)

# Configuration
CSV_FILE_PATH = 'data/Camp_Power_Up_past_forms - Sheet1.csv'
DB_FILE = 'camp_power_up.db'

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

@app.route('/api/stats')
def get_stats():
    """Get basic statistics about the campers."""
    conn = sqlite3.connect(DB_FILE)
    
    total_query = "SELECT COUNT(*) FROM campers"
    total_campers = conn.execute(total_query).fetchone()[0]
    
    returning_query = "SELECT COUNT(*) FROM campers WHERE is_returning = 'Yes'"
    returning_campers = conn.execute(returning_query).fetchone()[0]
    
    allergies_query = "SELECT COUNT(*) FROM campers WHERE has_allergies = 'Yes'"
    with_allergies = conn.execute(allergies_query).fetchone()[0]
    
    sensory_query = "SELECT COUNT(*) FROM campers WHERE has_sensory_issues = 'Yes'"
    with_sensory = conn.execute(sensory_query).fetchone()[0]
    
    switch_query = "SELECT COUNT(*) FROM campers WHERE bringing_switch = 'Yes'"
    bringing_switch = conn.execute(switch_query).fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_campers': total_campers,
        'returning_campers': returning_campers,
        'with_allergies': with_allergies,
        'with_sensory_issues': with_sensory,
        'bringing_switch': bringing_switch
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
    """Get the full list of campers."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute("""
        SELECT first_name, last_name, age, grade, is_returning, 
               bringing_switch, has_allergies, has_sensory_issues
        FROM campers 
        ORDER BY first_name, last_name
    """)
    
    campers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(campers)

@app.route('/api/special_needs')
def get_special_needs():
    """Get campers with special needs (allergies or sensory issues)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    special_needs = []
    
    # Get campers with allergies
    allergy_cursor = conn.execute("""
        SELECT first_name, last_name, allergy_description 
        FROM campers 
        WHERE has_allergies = 'Yes' AND allergy_description != ''
    """)
    
    for row in allergy_cursor:
        special_needs.append({
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
        special_needs.append({
            'name': f"{row['first_name']} {row['last_name']}",
            'type': 'Sensory Issues',
            'description': row['sensory_description']
        })
    
    conn.close()
    return jsonify(special_needs)

@app.route('/api/games')
def get_games():
    """Get detailed game preferences for campers."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute("""
        SELECT first_name, last_name, favorite_games, top_5_games, console_games, rating_restrictions, game_behavior
        FROM campers 
        WHERE favorite_games != '' OR top_5_games != '' OR console_games != '' OR game_behavior != 'Not specified'
        ORDER BY first_name, last_name
    """)
    
    games_data = []
    for row in cursor.fetchall():
        games_data.append({
            'name': f"{row['first_name']} {row['last_name']}",
            'favorite_games': row['favorite_games'],
            'top_5_games': row['top_5_games'], 
            'console_games': row['console_games'],
            'rating_restrictions': row['rating_restrictions'],
            'game_behavior': row['game_behavior']
        })
    
    conn.close()
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

if __name__ == '__main__':
    print("🏕️ Camp Power-Up Data Management System")
    print("=" * 50)
    clean_and_combine_data()
    print("\n🚀 Starting web server...")
    print("📱 Dashboard available at: http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
