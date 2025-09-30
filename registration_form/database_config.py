#!/usr/bin/env python3
"""
Database Configuration for Camp Power-Up
Handles both Railway PostgreSQL (production) and local SQLite (development)
"""

import os
import sqlite3
from contextlib import contextmanager

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')  # Railway provides this automatically
IS_PRODUCTION = bool(DATABASE_URL)

# Railway environment detection
RAILWAY_ENVIRONMENT = os.environ.get('RAILWAY_ENVIRONMENT')
IS_RAILWAY = bool(RAILWAY_ENVIRONMENT)

# Database paths for local development
LOCAL_REGISTRATION_DB = os.path.join(os.path.dirname(__file__), 'registration_submissions.db')
LOCAL_MAIN_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'camp_power_up.db')

# Debug logging
if IS_PRODUCTION:
    print(f"🚂 Railway PostgreSQL Mode - DATABASE_URL: {'Set' if DATABASE_URL else 'NOT SET'}")
else:
    print(f"💻 Local SQLite Mode - Registration DB: {LOCAL_REGISTRATION_DB}")

def get_database_type():
    """Returns 'PostgreSQL' for production, 'SQLite' for local development."""
    return 'PostgreSQL' if IS_PRODUCTION else 'SQLite'

@contextmanager  
def get_db_connection(db_type='registration'):
    """Context manager for database connections."""
    if IS_PRODUCTION and DATABASE_URL:
        # Use PostgreSQL on Railway
        try:
            import psycopg2
            from urllib.parse import urlparse
        except ImportError:
            print("❌ psycopg2 not installed - falling back to SQLite")
            conn = sqlite3.connect(LOCAL_REGISTRATION_DB)
        else:
            try:
                result = urlparse(DATABASE_URL)
                conn = psycopg2.connect(
                    database=result.path[1:],
                    user=result.username,
                    password=result.password,
                    host=result.hostname,
                    port=result.port
                )
                print("✅ PostgreSQL connection established")
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                print("🔄 Falling back to SQLite")
                conn = sqlite3.connect(LOCAL_REGISTRATION_DB)
    else:
        # Use SQLite locally
        if db_type == 'registration':
            conn = sqlite3.connect(LOCAL_REGISTRATION_DB)
        elif db_type == 'historical':
            conn = sqlite3.connect(LOCAL_MAIN_DB)
        else:
            raise ValueError(f"Unknown db_type: {db_type}")
    
    try:
        yield conn
        if hasattr(conn, 'commit'):
            conn.commit()
    except Exception as e:
        if hasattr(conn, 'rollback'):
            conn.rollback()
        raise e
    finally:
        conn.close()

def get_database_connection(db_type='registration'):
    """
    Get direct database connection (not context manager) for cases where manual control is needed.
    """
    if IS_PRODUCTION and DATABASE_URL:
        # Use PostgreSQL on Railway
        import psycopg2
        from urllib.parse import urlparse
        
        result = urlparse(DATABASE_URL)
        connection = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return connection
    else:
        # Use SQLite locally
        if db_type == 'registration':
            return sqlite3.connect(LOCAL_REGISTRATION_DB)
        elif db_type == 'historical':
            return sqlite3.connect(LOCAL_MAIN_DB)
        else:
            raise ValueError(f"Unknown db_type: {db_type}")

def init_postgresql_tables():
    """Initialize PostgreSQL tables on Railway."""
    if not IS_PRODUCTION:
        return False
        
    try:
        with get_db_connection('registration') as conn:
            cursor = conn.cursor()
            
            # Create registrations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registrations (
                    id SERIAL PRIMARY KEY,
                    submission_id VARCHAR(255) UNIQUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'pending',
                    payment_status VARCHAR(50) DEFAULT 'pending',
                    
                    -- Contact Information
                    parent_email VARCHAR(255) NOT NULL,
                    parent_phone VARCHAR(50),
                    emergency_contact_name VARCHAR(255),
                    emergency_contact_phone VARCHAR(50),
                    
                    -- Camper Information
                    child_first_name VARCHAR(255) NOT NULL,
                    child_last_name VARCHAR(255) NOT NULL,
                    child_age INTEGER,
                    child_grade VARCHAR(50),
                    child_gender VARCHAR(50),
                    
                    -- Camp Information
                    is_returning_camper BOOLEAN DEFAULT FALSE,
                    previous_year VARCHAR(10),
                    previous_instructor VARCHAR(255),
                    returning_camper_details TEXT,
                    camp_weeks JSON,
                    gaming_behavior TEXT,
                    game_restrictions TEXT,
                    bringing_own_switch BOOLEAN DEFAULT FALSE,
                    favorite_games TEXT,
                    games_owned TEXT,
                    console_experience TEXT,
                    
                    -- Health Information
                    has_allergies BOOLEAN DEFAULT FALSE,
                    allergy_details TEXT,
                    has_sensory_issues BOOLEAN DEFAULT FALSE,
                    sensory_details TEXT,
                    medical_conditions TEXT,
                    
                    -- Permissions
                    photo_permission BOOLEAN DEFAULT TRUE,
                    marketing_permission BOOLEAN DEFAULT TRUE,
                    tshirt_size VARCHAR(10),
                    
                    -- Additional
                    how_heard_about_camp TEXT,
                    additional_notes TEXT,
                    raw_form_data JSON
                )
            ''')
            
            # Create historical registrations table (from camp_power_up.db)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_registrations (
                    id SERIAL PRIMARY KEY,
                    childs_first_name VARCHAR(255),
                    childs_last_name VARCHAR(255),
                    email_address VARCHAR(255),
                    age INTEGER,
                    grade VARCHAR(50),
                    has_your_child_attended_camp_power_up_before VARCHAR(10),
                    allergies TEXT,
                    will_your_child_be_bringing_their_own_personal_switch VARCHAR(10),
                    what_games_do_they_enjoy_playing TEXT,
                    timestamp TIMESTAMP,
                    imported_from_sqlite BOOLEAN DEFAULT TRUE
                )
            ''')
            
            print("✅ PostgreSQL tables initialized successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error initializing PostgreSQL tables: {e}")
        return False

def migrate_sqlite_to_postgresql():
    """Migrate existing SQLite data to PostgreSQL (one-time operation)."""
    if not IS_PRODUCTION:
        print("Not in production environment, skipping PostgreSQL migration")
        return False
        
    try:
        # Check if data already exists
        with get_db_connection('registration') as pg_conn:
            cursor = pg_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM historical_registrations WHERE imported_from_sqlite = TRUE")
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f"✅ PostgreSQL already has {existing_count} migrated historical records")
                return True
        
        # Migration would happen here, but since we're deploying the SQLite files
        # alongside the code, we'll create a migration endpoint instead
        print("📋 Historical data migration will be handled via admin interface")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

# Export configuration
DB_CONFIG = {
    'is_production': IS_PRODUCTION,
    'database_url': DATABASE_URL,
    'local_registration_db': LOCAL_REGISTRATION_DB,
    'local_main_db': LOCAL_MAIN_DB
}

if __name__ == "__main__":
    print(f"Database Configuration:")
    print(f"  Production: {IS_PRODUCTION}")
    print(f"  Database URL: {'Set' if DATABASE_URL else 'Not Set'}")
    print(f"  Local Registration DB: {LOCAL_REGISTRATION_DB}")
    print(f"  Local Main DB: {LOCAL_MAIN_DB}")
    
    if IS_PRODUCTION:
        print("Initializing PostgreSQL tables...")
        init_postgresql_tables()