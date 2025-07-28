#!/usr/bin/env python3
"""
Update the registration database to include new verification fields.
"""

import sqlite3

def update_database():
    """Add new columns for returning camper verification."""
    conn = sqlite3.connect('registration_submissions.db')
    cursor = conn.cursor()
    
    # Check if the new columns already exist
    cursor.execute("PRAGMA table_info(registrations)")
    columns = [col[1] for col in cursor.fetchall()]
    
    new_columns = [
        ('previous_year', 'TEXT'),
        ('previous_instructor', 'TEXT'), 
        ('returning_camper_details', 'TEXT')
    ]
    
    for column_name, column_type in new_columns:
        if column_name not in columns:
            try:
                cursor.execute(f'ALTER TABLE registrations ADD COLUMN {column_name} {column_type}')
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"❌ Error adding column {column_name}: {e}")
        else:
            print(f"ℹ️ Column {column_name} already exists")
    
    conn.commit()
    conn.close()
    print("Database update complete!")

if __name__ == "__main__":
    update_database()
