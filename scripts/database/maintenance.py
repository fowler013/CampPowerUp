#!/usr/bin/env python3
"""
Database Maintenance Script
Applies APCV 360 principles: Performance Optimization, Data Integrity

Performs routine maintenance tasks:
- VACUUM to reclaim space and optimize database
- ANALYZE to update query planner statistics
- Integrity check
- Index optimization
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.database import DatabaseManager
from src.config import get_config


def run_maintenance(db_path: str = None, verbose: bool = True):
    """
    Run database maintenance tasks.
    
    Args:
        db_path: Path to database (default: current database)
        verbose: Print detailed output
    """
    config = get_config()
    
    if db_path is None:
        db_path = config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
    
    db_manager = DatabaseManager(db_path)
    
    print("=" * 60)
    print("DATABASE MAINTENANCE")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Integrity Check
    print("1. Running integrity check...")
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == "ok":
            print("   ✅ Integrity check passed")
        else:
            print(f"   ❌ Integrity check failed: {result[0]}")
            return False
    except Exception as e:
        print(f"   ❌ Integrity check error: {e}")
        return False
    finally:
        db_manager.close()
    
    # 2. Get database statistics (before maintenance)
    print("\n2. Database statistics (before):")
    stats_before = get_db_stats(db_path)
    if verbose:
        print_stats(stats_before)
    
    # 3. VACUUM
    print("\n3. Running VACUUM...")
    try:
        db_manager.vacuum()
        print("   ✅ VACUUM completed")
    except Exception as e:
        print(f"   ❌ VACUUM error: {e}")
        return False
    
    # 4. ANALYZE
    print("\n4. Running ANALYZE...")
    try:
        db_manager.analyze()
        print("   ✅ ANALYZE completed")
    except Exception as e:
        print(f"   ❌ ANALYZE error: {e}")
        return False
    
    # 5. Optimize indexes
    print("\n5. Optimizing indexes...")
    try:
        optimize_indexes(db_path)
        print("   ✅ Index optimization completed")
    except Exception as e:
        print(f"   ❌ Index optimization error: {e}")
        return False
    
    # 6. Get database statistics (after maintenance)
    print("\n6. Database statistics (after):")
    stats_after = get_db_stats(db_path)
    if verbose:
        print_stats(stats_after)
    
    # 7. Show improvement
    print("\n7. Maintenance results:")
    size_before = stats_before['file_size']
    size_after = stats_after['file_size']
    size_saved = size_before - size_after
    
    print(f"   File size: {size_before / 1024:.2f} KB → {size_after / 1024:.2f} KB")
    if size_saved > 0:
        print(f"   Space saved: {size_saved / 1024:.2f} KB ({size_saved / size_before * 100:.1f}%)")
    
    print(f"\n✅ Maintenance completed successfully!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return True


def get_db_stats(db_path: str) -> dict:
    """Get database statistics."""
    db_path = Path(db_path)
    
    stats = {
        'file_size': db_path.stat().st_size if db_path.exists() else 0,
        'tables': 0,
        'indexes': 0,
        'total_rows': 0
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count tables
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        stats['tables'] = cursor.fetchone()[0]
        
        # Count indexes
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        stats['indexes'] = cursor.fetchone()[0]
        
        # Count total rows
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if not table_name.startswith('sqlite_'):
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                stats['total_rows'] += cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    return stats


def print_stats(stats: dict):
    """Print database statistics."""
    print(f"   File size: {stats['file_size'] / 1024:.2f} KB")
    print(f"   Tables: {stats['tables']}")
    print(f"   Indexes: {stats['indexes']}")
    print(f"   Total rows: {stats['total_rows']}")


def optimize_indexes(db_path: str):
    """Optimize database indexes."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    indexes = cursor.fetchall()
    
    # Reindex each index
    for index in indexes:
        index_name = index[0]
        cursor.execute(f"REINDEX {index_name}")
    
    conn.commit()
    conn.close()


def check_missing_indexes(db_path: str):
    """Check for tables without indexes on foreign keys."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n8. Checking for missing indexes...")
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    suggestions = []
    
    for table in tables:
        table_name = table[0]
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Check for foreign key columns without indexes
        for col in columns:
            col_name = col[1]
            if col_name.endswith('_id') or 'foreign' in col_name.lower():
                # Check if index exists
                cursor.execute(
                    f"SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql LIKE ?",
                    (table_name, f'%{col_name}%')
                )
                
                if cursor.fetchone()[0] == 0:
                    suggestions.append(f"CREATE INDEX idx_{table_name}_{col_name} ON {table_name}({col_name});")
    
    if suggestions:
        print("   ⚠️  Missing indexes detected:")
        for suggestion in suggestions:
            print(f"      {suggestion}")
    else:
        print("   ✅ All foreign keys are properly indexed")
    
    conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database maintenance script")
    parser.add_argument(
        '--db',
        help='Database path (default: current database)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output'
    )
    parser.add_argument(
        '--check-indexes',
        action='store_true',
        help='Check for missing indexes'
    )
    
    args = parser.parse_args()
    
    success = run_maintenance(args.db, verbose=not args.quiet)
    
    if args.check_indexes:
        check_missing_indexes(args.db or get_config().SQLALCHEMY_DATABASE_URI.replace("sqlite:///", ""))
    
    sys.exit(0 if success else 1)
