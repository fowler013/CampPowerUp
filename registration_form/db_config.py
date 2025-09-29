#!/usr/bin/env python3
"""
Database configuration utility for Camp Power-Up
Supports both SQLite (local development) and PostgreSQL (Railway production)
"""

import os
import sqlite3
from urllib.parse import urlparse

def get_database_config():
    """Get database configuration based on environment."""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production: Use PostgreSQL from Railway
        print("🐘 Using PostgreSQL database (Production)")
        return {
            'type': 'postgresql',
            'url': database_url,
            'config': parse_database_url(database_url)
        }
    else:
        # Development: Use SQLite
        print("📁 Using SQLite database (Development)")
        return {
            'type': 'sqlite',
            'file': 'registration_submissions.db',
            'config': None
        }

def parse_database_url(url):
    """Parse PostgreSQL database URL."""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],  # Remove leading slash
        'username': parsed.username,
        'password': parsed.password
    }

def get_db_connection():
    """Get appropriate database connection."""
    config = get_database_config()
    
    if config['type'] == 'postgresql':
        try:
            # psycopg2 is only needed for PostgreSQL connections (Railway production)
            import psycopg2  # type: ignore[import-untyped]
            return psycopg2.connect(config['url'])
        except ImportError as e:
            print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
            print("   This is only needed for PostgreSQL connections (Railway production)")
            raise e
    else:
        return sqlite3.connect(config['file'])

def initialize_database():
    """Initialize database with proper schema."""
    config = get_database_config()
    
    if config['type'] == 'postgresql':
        print("🔧 Initializing PostgreSQL database...")
        # PostgreSQL initialization logic would go here
        # For now, assume tables are created via migrations
        return True
    else:
        print("🔧 Initializing SQLite database...")
        # Existing SQLite initialization
        return initialize_sqlite_database()

def initialize_sqlite_database():
    """Initialize SQLite database (existing logic)."""
    try:
        conn = sqlite3.connect('registration_submissions.db')
        cursor = conn.cursor()
        
        # Your existing table creation logic here
        cursor.execute('''CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT UNIQUE,
            child_first_name TEXT,
            child_last_name TEXT,
            parent_email TEXT,
            timestamp TEXT,
            is_returning_camper BOOLEAN DEFAULT 0
            -- Add other columns as needed
        )''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == '__main__':
    # Test database connection
    config = get_database_config()
    print(f"Database type: {config['type']}")
    
    if initialize_database():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")