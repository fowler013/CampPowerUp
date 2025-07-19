import pandas as pd
import sqlite3
import re
from flask import Flask, jsonify, render_template
import os

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

if __name__ == '__main__':
    print("🏕️ Camp Power-Up Data Management System")
    print("=" * 50)
    clean_and_combine_data()
    print("\n🚀 Starting web server...")
    print("📱 Dashboard available at: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
