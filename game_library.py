#!/usr/bin/env python3
"""
Game Library Management System for Camp Power-Up
Tracks games owned by campers, popularity, and availability
"""

import sqlite3
import json
from collections import Counter
import re

DATABASE_PATH = 'camp_power_up.db'

def initialize_game_library():
    """Initialize the game library database tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create games table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            normalized_name TEXT NOT NULL,
            platform TEXT DEFAULT 'Nintendo Switch',
            genre TEXT,
            rating TEXT,
            total_owned INTEGER DEFAULT 0,
            camp_copies INTEGER DEFAULT 0,
            availability_status TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create camper_games junction table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS camper_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camper_id INTEGER,
            game_id INTEGER,
            owns_game BOOLEAN DEFAULT 0,
            brings_to_camp BOOLEAN DEFAULT 0,
            skill_level TEXT DEFAULT 'Beginner',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Game library database initialized")

def normalize_game_name(game_name):
    """Normalize game names for consistent matching"""
    if not game_name:
        return ""
    
    # Convert to lowercase and remove extra spaces
    normalized = re.sub(r'\s+', ' ', game_name.strip().lower())
    
    # Common game name mappings
    mappings = {
        'mario kart 8': 'mario kart 8 deluxe',
        'mario kart': 'mario kart 8 deluxe',
        'smash bros': 'super smash bros ultimate',
        'smash brothers': 'super smash bros ultimate',
        'super smash bros': 'super smash bros ultimate',
        'animal crossing': 'animal crossing new horizons',
        'zelda': 'the legend of zelda breath of the wild',
        'breath of the wild': 'the legend of zelda breath of the wild',
        'botw': 'the legend of zelda breath of the wild',
        'pokemon': 'pokemon sword/shield',
        'splatoon': 'splatoon 3',
        'minecraft': 'minecraft',
        'roblox': 'roblox',
        'fortnite': 'fortnite'
    }
    
    # Apply mappings
    for key, value in mappings.items():
        if key in normalized:
            return value
    
    return normalized

def extract_games_from_text(text):
    """Extract game names from free-form text"""
    if not text or text.strip() == '':
        return []
    
    # Common game patterns
    game_patterns = [
        r'mario kart\s*\d*',
        r'super smash bros?\s*\w*',
        r'animal crossing\s*\w*',
        r'legend of zelda\s*\w*',
        r'breath of the wild',
        r'pokemon\s*\w*',
        r'splatoon\s*\d*',
        r'minecraft',
        r'roblox',
        r'fortnite',
        r'sonic\s*\w*',
        r'kirby\s*\w*',
        r'luigi\s*\w*',
        r'metroid\s*\w*',
        r'donkey kong\s*\w*'
    ]
    
    found_games = []
    text_lower = text.lower()
    
    for pattern in game_patterns:
        matches = re.findall(pattern, text_lower)
        found_games.extend(matches)
    
    # Also split by common delimiters and check individual words
    words = re.split(r'[,;/&\n\r]+', text_lower)
    for word in words:
        word = word.strip()
        if len(word) > 3:  # Ignore very short words
            found_games.append(word)
    
    # Normalize and deduplicate
    normalized_games = []
    for game in found_games:
        normalized = normalize_game_name(game)
        if normalized and normalized not in normalized_games:
            normalized_games.append(normalized)
    
    return normalized_games

def add_or_update_game(game_name, platform='Nintendo Switch', genre=None, rating=None, camp_copies=0):
    """Add a new game or update existing game in the library"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    normalized_name = normalize_game_name(game_name)
    
    # Check if game exists
    cursor.execute('SELECT id FROM games WHERE normalized_name = ?', (normalized_name,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing game
        cursor.execute('''
            UPDATE games 
            SET camp_copies = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (camp_copies, existing[0]))
        game_id = existing[0]
    else:
        # Insert new game
        cursor.execute('''
            INSERT INTO games (name, normalized_name, platform, genre, rating, camp_copies)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (game_name, normalized_name, platform, genre, rating, camp_copies))
        game_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return game_id

SAMPLE_GAMES = [
    ('Mario Kart 8 Deluxe', 45, 5),
    ('Super Smash Bros Ultimate', 38, 3),
    ('Animal Crossing New Horizons', 32, 2),
    ('Minecraft', 28, 4),
    ('Pokemon Sword/Shield', 24, 2),
    ('Splatoon 3', 19, 2),
    ('Fortnite', 17, 0),
    ('Roblox', 15, 0),
    ('The Legend of Zelda Breath of the Wild', 12, 1),
    ('Kirby and the Forgotten Land', 9, 1),
]


def seed_sample_games():
    """Seed an empty game library with sample data when no registration data exists."""
    initialize_game_library()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) FROM games')
        if cursor.fetchone()[0] > 0:
            print("ℹ️ Game library already contains data; skipping sample seed")
            return

        cursor.execute('DELETE FROM camper_games')

        next_camper_id = 1
        for name, total_owned, camp_copies in SAMPLE_GAMES:
            normalized = normalize_game_name(name)
            cursor.execute(
                'INSERT INTO games (name, normalized_name, total_owned, camp_copies) VALUES (?, ?, ?, ?)',
                (name, normalized, total_owned, camp_copies)
            )
            game_id = cursor.lastrowid

            for ownership_index in range(total_owned):
                cursor.execute(
                    '''
                    INSERT INTO camper_games (camper_id, game_id, owns_game, brings_to_camp)
                    VALUES (?, ?, 1, ?)
                    ''',
                    (
                        next_camper_id,
                        game_id,
                        1 if ownership_index < camp_copies else 0,
                    )
                )
                next_camper_id += 1
        conn.commit()
    finally:
        conn.close()
    print(f"✅ Seeded {len(SAMPLE_GAMES)} sample games")


def registrations_table_exists():
    """Check whether the registrations table exists in the main database."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='registrations'"
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def process_camper_games():
    """Process existing registration data to populate game library.

    Falls back to seeding sample data if no registrations table exists.
    """
    # Initialize game library tables first so the dashboard always works
    initialize_game_library()

    if not registrations_table_exists():
        print("⚠️ No registrations table found — seeding sample game data instead")
        seed_sample_games()
        return Counter({name.lower(): count for name, count, _ in SAMPLE_GAMES})

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all camper game data
    cursor.execute('''
        SELECT 
            ROW_NUMBER() OVER (ORDER BY childs_first_name) as camper_id,
            childs_first_name,
            childs_last_name,
            what_games_do_they_enjoy_playing,
            list_your_child_s_top_5_games_they_like_to_play,
            what_games_has_your_child_played_on_those_systems,
            will_your_child_be_bringing_their_own_personal_switch
        FROM registrations 
        WHERE childs_first_name IS NOT NULL
    ''')
    
    campers = cursor.fetchall()
    conn.close()
    
    game_counts = Counter()
    camper_game_data = []
    
    for camper in campers:
        all_games_text = f"{camper['what_games_do_they_enjoy_playing'] or ''} {camper['list_your_child_s_top_5_games_they_like_to_play'] or ''} {camper['what_games_has_your_child_played_on_those_systems'] or ''}"
        
        games = extract_games_from_text(all_games_text)
        brings_switch = camper['will_your_child_be_bringing_their_own_personal_switch'] == 'Yes'
        
        for game in games:
            game_counts[game] += 1
            camper_game_data.append({
                'camper_id': camper['camper_id'],
                'camper_name': f"{camper['childs_first_name']} {camper['childs_last_name']}",
                'game': game,
                'brings_switch': brings_switch
            })
    
    # Add games to library
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    for game, count in game_counts.items():
        game_id = add_or_update_game(game)
        
        # Update total_owned count
        cursor.execute('UPDATE games SET total_owned = ? WHERE id = ?', (count, game_id))
    
    # Add camper-game relationships
    for data in camper_game_data:
        cursor.execute('SELECT id FROM games WHERE normalized_name = ?', (data['game'],))
        game_result = cursor.fetchone()
        
        if game_result:
            game_id = game_result[0]
            cursor.execute('''
                INSERT OR IGNORE INTO camper_games 
                (camper_id, game_id, owns_game, brings_to_camp)
                VALUES (?, ?, 1, ?)
            ''', (data['camper_id'], game_id, data['brings_switch']))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Processed {len(camper_game_data)} camper-game relationships")
    print(f"✅ Found {len(game_counts)} unique games")
    return game_counts

def get_game_library_stats():
    """Get comprehensive game library statistics"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all games with stats
    cursor.execute('''
        SELECT 
            g.*,
            COUNT(cg.id) as campers_who_own,
            SUM(CASE WHEN cg.brings_to_camp = 1 THEN 1 ELSE 0 END) as copies_at_camp
        FROM games g
        LEFT JOIN camper_games cg ON g.id = cg.game_id
        GROUP BY g.id
        ORDER BY g.total_owned DESC
    ''')
    
    games = cursor.fetchall()
    
    # Get summary stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_games,
            SUM(total_owned) as total_ownership_instances,
            SUM(camp_copies) as total_camp_copies,
            AVG(total_owned) as avg_ownership
        FROM games
    ''')
    
    summary = cursor.fetchone()
    conn.close()
    
    return {
        'games': [dict(game) for game in games],
        'summary': dict(summary)
    }

if __name__ == '__main__':
    print("🎮 Processing Game Library Data...")
    game_counts = process_camper_games()
    
    print("\n📊 Top 10 Most Popular Games:")
    for game, count in game_counts.most_common(10):
        print(f"   {game}: {count} campers")
    
    stats = get_game_library_stats()
    print(f"\n📈 Library Summary:")
    print(f"   Total Games: {stats['summary']['total_games']}")
    print(f"   Total Ownership Instances: {stats['summary']['total_ownership_instances']}")
    print(f"   Average Ownership per Game: {stats['summary']['avg_ownership']:.1f}")
