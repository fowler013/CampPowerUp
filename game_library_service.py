#!/usr/bin/env python3
"""
Game Library Web Service for Camp Power-Up
Web interface for the game library management
"""

from flask import Flask, render_template_string, jsonify, request
import sqlite3
import json
from collections import Counter
import os

app = Flask(__name__)
DATABASE_PATH = 'camp_power_up.db'

def get_db_connection():
    """Get database connection with proper timeout"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_game_library():
    """Initialize the game library database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create games table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            normalized_name TEXT NOT NULL UNIQUE,
            platform TEXT,
            genre TEXT,
            rating TEXT,
            camp_copies INTEGER DEFAULT 0,
            total_campers INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def game_library_home():
    """Game library home page"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎮 Camp Power-Up - Game Library</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 20px; min-height: 100vh; color: white;
            }
            .container { 
                max-width: 1200px; margin: 0 auto; 
                background: rgba(255,255,255,0.1); 
                backdrop-filter: blur(10px);
                border-radius: 20px; padding: 30px;
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            }
            h1 { text-align: center; margin-bottom: 30px; font-size: 2.5em; }
            .stats-grid { 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; margin-bottom: 30px;
            }
            .stat-card { 
                background: rgba(255,255,255,0.2); 
                padding: 20px; border-radius: 15px; text-align: center;
            }
            .stat-number { font-size: 2em; font-weight: bold; color: #FFD700; }
            .game-list { 
                background: rgba(255,255,255,0.1); 
                border-radius: 15px; padding: 20px;
            }
            .game-item { 
                background: rgba(255,255,255,0.1); 
                margin: 10px 0; padding: 15px; border-radius: 10px;
                display: flex; justify-content: space-between; align-items: center;
            }
            .nav-links { text-align: center; margin-bottom: 20px; }
            .nav-links a { 
                color: white; text-decoration: none; margin: 0 15px;
                background: rgba(255,255,255,0.2); padding: 10px 20px;
                border-radius: 25px; transition: all 0.3s ease;
            }
            .nav-links a:hover { background: rgba(255,255,255,0.3); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 Camp Power-Up Game Library</h1>
            
            <div class="nav-links">
                <a href="/">🏠 Library Home</a>
                <a href="/api/games">📊 API Data</a>
                <a href="/api/stats">📈 Statistics</a>
                <a href="http://localhost:5009/admin/dashboard">🔙 Admin Portal</a>
            </div>
            
            <div class="stats-grid" id="stats">
                <div class="stat-card">
                    <div class="stat-number" id="total-games">Loading...</div>
                    <div>Total Games</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-campers">Loading...</div>
                    <div>Total Ownership Instances</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="avg-ownership">Loading...</div>
                    <div>Avg Ownership per Game</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">✅</div>
                    <div>Service Status</div>
                </div>
            </div>
            
            <div class="game-list">
                <h2>🏆 Popular Games</h2>
                <div id="games-list">Loading games...</div>
            </div>
        </div>
        
        <script>
            // Load game statistics
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-games').textContent = data.total_games || 0;
                    document.getElementById('total-campers').textContent = data.total_ownership_instances || 0;
                    document.getElementById('avg-ownership').textContent = (data.avg_ownership || 0).toFixed(1);
                })
                .catch(error => {
                    console.error('Error loading stats:', error);
                    document.getElementById('total-games').textContent = 'Error';
                    document.getElementById('total-campers').textContent = 'Error';
                    document.getElementById('avg-ownership').textContent = 'Error';
                });
            
            // Load games list
            fetch('/api/games')
                .then(response => response.json())
                .then(data => {
                    const gamesList = document.getElementById('games-list');
                    if (data.length === 0) {
                        gamesList.innerHTML = '<p>No games found. Import game data to see results.</p>';
                        return;
                    }
                    
                    gamesList.innerHTML = data.slice(0, 10).map(game => `
                        <div class="game-item">
                            <div>
                                <strong>${game.name}</strong><br>
                                <small>${game.platform || 'Unknown Platform'} - ${game.genre || 'Unknown Genre'}</small>
                            </div>
                            <div>
                                <span style="background: rgba(255,255,255,0.3); padding: 5px 15px; border-radius: 15px;">
                                    ${game.total_campers || 0} campers
                                </span>
                            </div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    console.error('Error loading games:', error);
                    document.getElementById('games-list').innerHTML = '<p>Error loading games.</p>';
                });
        </script>
    </body>
    </html>
    ''')

@app.route('/api/games')
def api_games():
    """API endpoint for games data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM games 
            ORDER BY total_campers DESC, name ASC
        ''')
        
        games = []
        for row in cursor.fetchall():
            games.append({
                'id': row['id'],
                'name': row['name'],
                'platform': row['platform'],
                'genre': row['genre'],
                'rating': row['rating'],
                'camp_copies': row['camp_copies'],
                'total_campers': row['total_campers']
            })
        
        conn.close()
        return jsonify(games)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for game library statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) as total_games FROM games')
        total_games = cursor.fetchone()['total_games']
        
        cursor.execute('SELECT SUM(total_campers) as total_ownership FROM games')
        total_ownership = cursor.fetchone()['total_ownership'] or 0
        
        avg_ownership = total_ownership / total_games if total_games > 0 else 0
        
        conn.close()
        
        return jsonify({
            'total_games': total_games,
            'total_ownership_instances': total_ownership,
            'avg_ownership': avg_ownership
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'game_library',
        'port': 5000
    })

if __name__ == '__main__':
    print("🎮 Initializing Game Library Web Service...")
    initialize_game_library()
    print("✅ Game Library database initialized")
    print("🚀 Starting Game Library Web Service on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
