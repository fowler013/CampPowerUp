#!/usr/bin/env python3
"""
Database Migration Script for Camp Power-Up
==========================================

This script migrates data from SQLite to PostgreSQL for production deployment.
"""

import sqlite3
import psycopg2
import psycopg2.extras
import os
import sys
from urllib.parse import urlparse
from datetime import datetime

def parse_database_url(database_url):
    """Parse database URL into connection parameters"""
    if database_url.startswith('postgresql://'):
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password
        }
    elif database_url.startswith('sqlite:///'):
        return {'sqlite_path': database_url.replace('sqlite:///', '')}
    else:
        raise ValueError(f"Unsupported database URL: {database_url}")

def create_postgresql_tables(pg_conn):
    """Create PostgreSQL tables matching SQLite schema"""
    
    # Main campers table (historical data)
    campers_table_sql = """
    CREATE TABLE IF NOT EXISTS campers (
        id SERIAL PRIMARY KEY,
        timestamp VARCHAR(50),
        email_address VARCHAR(255),
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        is_returning VARCHAR(10),
        age INTEGER,
        grade VARCHAR(50),
        game_behavior TEXT,
        rating_restrictions TEXT,
        bringing_switch VARCHAR(10),
        consent_social_media VARCHAR(10),
        has_sensory_issues VARCHAR(10),
        sensory_description TEXT,
        has_allergies VARCHAR(10),
        allergy_description TEXT,
        favorite_games TEXT,
        top_5_games TEXT,
        console_games TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Registration submissions table (new registrations)
    registrations_table_sql = """
    CREATE TABLE IF NOT EXISTS registrations (
        id SERIAL PRIMARY KEY,
        submission_id VARCHAR(100) UNIQUE NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        parent_email VARCHAR(255) NOT NULL,
        parent_name VARCHAR(255),
        parent_phone VARCHAR(50),
        child_first_name VARCHAR(100) NOT NULL,
        child_last_name VARCHAR(100) NOT NULL,
        child_age INTEGER,
        child_grade VARCHAR(50),
        is_returning_camper BOOLEAN DEFAULT FALSE,
        emergency_contact_name VARCHAR(255),
        emergency_contact_phone VARCHAR(50),
        emergency_contact_relationship VARCHAR(100),
        medical_conditions TEXT,
        dietary_restrictions TEXT,
        allergies TEXT,
        medications TEXT,
        behavioral_considerations TEXT,
        pickup_instructions TEXT,
        consent_photos BOOLEAN DEFAULT FALSE,
        consent_social_media BOOLEAN DEFAULT FALSE,
        additional_info TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with pg_conn.cursor() as cursor:
        print("Creating PostgreSQL tables...")
        cursor.execute(campers_table_sql)
        cursor.execute(registrations_table_sql)
        pg_conn.commit()
        print("✅ Tables created successfully")

def migrate_sqlite_to_postgresql(sqlite_db_path, pg_conn, table_name, pg_table_name=None):
    """Migrate data from SQLite to PostgreSQL"""
    
    if not os.path.exists(sqlite_db_path):
        print(f"⚠️  SQLite database not found: {sqlite_db_path}")
        return
    
    if pg_table_name is None:
        pg_table_name = table_name
    
    print(f"Migrating {table_name} from {sqlite_db_path} to PostgreSQL...")
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    try:
        # Get data from SQLite
        cursor = sqlite_conn.cursor()
        
        if table_name == 'campers':
            # Use the actual column names from your historical data
            cursor.execute("""
                SELECT timestamp, email_address, childs_first_name, childs_last_name,
                       has_your_child_attended_camp_power_up_before, age, grade,
                       can_you_describe_what_your_child_is_like_playing_video_games_around_others_are_they_good_at_taking_turns_are_they_a_good_sport,
                       is_there_a_rating_of_games_your_child_is_not_allowed_to_play,
                       will_your_child_be_bringing_their_own_personal_switch,
                       do_you_consent_for_your_childs_image_to_be_used_on_social_media_platforms_to_promote_the_camp_power_up,
                       any_sensory_issues,
                       if_yes_please_describe,
                       allergies,
                       if_yes_please_list_any_medical_conditions_or_allergies,
                       what_games_do_they_enjoy_playing,
                       list_your_child_s_top_5_games_they_like_to_play,
                       has_your_child_played_on_any_of_these_consoles
                FROM registrations
            """)
        elif table_name == 'registrations':
            cursor.execute("SELECT * FROM registrations")
        else:
            print(f"❌ Unknown table: {table_name}")
            return
        
        rows = cursor.fetchall()
        
        if not rows:
            print(f"⚠️  No data found in {table_name}")
            return
        
        # Insert into PostgreSQL
        with pg_conn.cursor() as pg_cursor:
            if table_name == 'campers':
                # Map SQLite columns to PostgreSQL columns
                insert_sql = """
                    INSERT INTO campers (
                        timestamp, email_address, first_name, last_name, is_returning,
                        age, grade, game_behavior, rating_restrictions, bringing_switch,
                        consent_social_media, has_sensory_issues, sensory_description,
                        has_allergies, allergy_description, favorite_games, top_5_games, console_games
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                for row in rows:
                    pg_cursor.execute(insert_sql, (
                        row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                        row[7], row[8], row[9], row[10], row[11], row[12],
                        row[13], row[14], row[15], row[16], row[17]
                    ))
                    
            elif table_name == 'registrations':
                # Get column names dynamically
                columns = [description[0] for description in cursor.description]
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                insert_sql = f"INSERT INTO registrations ({columns_str}) VALUES ({placeholders})"
                
                for row in rows:
                    pg_cursor.execute(insert_sql, tuple(row))
            
            pg_conn.commit()
            print(f"✅ Migrated {len(rows)} records from {table_name}")
            
    finally:
        sqlite_conn.close()

def main():
    """Main migration function"""
    
    # Get database URLs from environment
    sqlite_main_db = os.environ.get('DATABASE_URL', 'sqlite:///camp_power_up.db').replace('sqlite:///', '')
    sqlite_reg_db = os.environ.get('REGISTRATION_DATABASE_URL', 'sqlite:///registration_form/registration_submissions.db').replace('sqlite:///', '')
    pg_url = os.environ.get('PRODUCTION_DATABASE_URL')
    
    if not pg_url:
        print("❌ PRODUCTION_DATABASE_URL environment variable is required")
        print("Example: postgresql://username:password@hostname:5432/database_name")
        sys.exit(1)
    
    print("🚀 Starting database migration...")
    print(f"Source SQLite DBs: {sqlite_main_db}, {sqlite_reg_db}")
    print(f"Target PostgreSQL: {pg_url.split('@')[0]}@***")
    
    try:
        # Parse PostgreSQL URL
        pg_params = parse_database_url(pg_url)
        
        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(**pg_params)
        print("✅ Connected to PostgreSQL")
        
        # Create tables
        create_postgresql_tables(pg_conn)
        
        # Migrate main campers data (historical)
        if os.path.exists(sqlite_main_db):
            migrate_sqlite_to_postgresql(sqlite_main_db, pg_conn, 'registrations', 'campers')
        
        # Migrate registration submissions
        if os.path.exists(sqlite_reg_db):
            migrate_sqlite_to_postgresql(sqlite_reg_db, pg_conn, 'registrations', 'registrations')
        
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)
    
    finally:
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == '__main__':
    main()