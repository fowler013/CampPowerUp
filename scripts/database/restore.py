#!/usr/bin/env python3
"""
Database Restore Script
Applies APCV 360 principles: Backup & Recovery, Data Integrity

Restores database from a backup file with safety checks.
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_config


def list_backups(backup_dir: str = None) -> list:
    """
    List available backup files.
    
    Args:
        backup_dir: Directory containing backups
    
    Returns:
        List of backup file paths sorted by date (newest first)
    """
    if backup_dir is None:
        backup_dir = Path(__file__).parent.parent.parent / "data" / "backups"
    else:
        backup_dir = Path(backup_dir)
    
    if not backup_dir.exists():
        print("No backup directory found.")
        return []
    
    backups = sorted(
        backup_dir.glob("*_backup_*.db*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    return [str(b) for b in backups]


def restore_backup(backup_path: str, target_db: str = None, force: bool = False):
    """
    Restore database from backup.
    
    Args:
        backup_path: Path to the backup file
        target_db: Target database path (default: current database)
        force: Skip confirmation prompt
    """
    config = get_config()
    backup_path = Path(backup_path)
    
    # Get target database path
    if target_db is None:
        target_db = config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
    
    target_db = Path(target_db)
    
    # Verify backup exists
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        sys.exit(1)
    
    # Verify backup is valid
    print("Verifying backup...")
    if not verify_backup(backup_path):
        print("❌ Backup verification failed. Cannot restore.")
        sys.exit(1)
    
    # Confirmation
    if not force:
        print(f"\n⚠️  WARNING: This will replace the current database!")
        print(f"   Target: {target_db}")
        print(f"   Backup: {backup_path}")
        print(f"   Backup date: {datetime.fromtimestamp(backup_path.stat().st_mtime)}")
        
        response = input("\nContinue? (yes/no): ")
        if response.lower() != "yes":
            print("Restore cancelled.")
            sys.exit(0)
    
    # Create backup of current database before restoring
    if target_db.exists():
        current_backup = target_db.with_suffix('.db.before_restore')
        print(f"Creating safety backup of current database: {current_backup}")
        shutil.copy2(target_db, current_backup)
    
    try:
        # Handle compressed backups
        if backup_path.suffix == '.gz':
            import gzip
            
            print("Decompressing backup...")
            with gzip.open(backup_path, 'rb') as f_in:
                with open(target_db, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            print("Restoring database...")
            shutil.copy2(backup_path, target_db)
        
        # Verify restored database
        print("Verifying restored database...")
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"✅ Database restored successfully!")
        print(f"   Tables restored: {len(tables)}")
        print(f"   Location: {target_db}")
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        
        # Restore the safety backup
        if target_db.exists() and (target_db.with_suffix('.db.before_restore')).exists():
            print("Restoring from safety backup...")
            shutil.copy2(target_db.with_suffix('.db.before_restore'), target_db)
            print("✅ Safety backup restored.")
        
        sys.exit(1)


def verify_backup(backup_path: str) -> bool:
    """
    Verify that a backup file is valid.
    
    Args:
        backup_path: Path to the backup file
    
    Returns:
        True if backup is valid
    """
    backup_path = Path(backup_path)
    
    if not backup_path.exists():
        return False
    
    # Handle compressed backups
    if backup_path.suffix == '.gz':
        import gzip
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            with gzip.open(backup_path, 'rb') as f_in:
                shutil.copyfileobj(f_in, tmp)
            tmp_path = tmp.name
        
        try:
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            return len(tables) > 0
        except:
            return False
        finally:
            os.unlink(tmp_path)
    else:
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            return len(tables) > 0
        except:
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database restore script")
    parser.add_argument(
        'backup_path',
        nargs='?',
        help='Path to backup file to restore (or use --list to see available backups)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available backups'
    )
    parser.add_argument(
        '--backup-dir',
        help='Directory containing backups (default: data/backups)'
    )
    parser.add_argument(
        '--target',
        help='Target database path (default: current database)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )
    parser.add_argument(
        '--latest',
        action='store_true',
        help='Restore from the latest backup'
    )
    
    args = parser.parse_args()
    
    if args.list or args.latest:
        backups = list_backups(args.backup_dir)
        
        if not backups:
            print("No backups found.")
            sys.exit(0)
        
        print("Available backups:")
        for i, backup in enumerate(backups, 1):
            backup_path = Path(backup)
            size = backup_path.stat().st_size / 1024
            date = datetime.fromtimestamp(backup_path.stat().st_mtime)
            print(f"  {i}. {backup_path.name}")
            print(f"     Date: {date}")
            print(f"     Size: {size:.2f} KB")
            print()
        
        if args.latest:
            print(f"Restoring from latest backup: {backups[0]}")
            restore_backup(backups[0], args.target, args.force)
    
    elif args.backup_path:
        restore_backup(args.backup_path, args.target, args.force)
    
    else:
        parser.print_help()
