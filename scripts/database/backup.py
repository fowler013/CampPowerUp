#!/usr/bin/env python3
"""
Database Backup Script
Applies APCV 360 principles: Backup & Recovery, Data Integrity

Creates timestamped backups of the database with optional compression.
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.shared.database import DatabaseManager
from src.config import get_config


def create_backup(backup_dir: str = None, compress: bool = True) -> str:
    """
    Create a database backup.
    
    Args:
        backup_dir: Directory to store backups (default: data/backups)
        compress: Whether to compress the backup
    
    Returns:
        Path to the backup file
    """
    config = get_config()
    
    # Set default backup directory
    if backup_dir is None:
        backup_dir = Path(__file__).parent.parent.parent / "data" / "backups"
    else:
        backup_dir = Path(backup_dir)
    
    # Create backup directory if it doesn't exist
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get database path
    db_path = config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
    db_name = Path(db_path).stem
    
    # Create backup filename
    backup_filename = f"{db_name}_backup_{timestamp}.db"
    backup_path = backup_dir / backup_filename
    
    print(f"Creating backup: {backup_path}")
    
    try:
        # Use DatabaseManager's backup method
        db_manager = DatabaseManager(db_path)
        
        # SQLite backup using VACUUM INTO (preserves integrity)
        conn = sqlite3.connect(db_path)
        conn.execute(f"VACUUM INTO '{backup_path}'")
        conn.close()
        
        print(f"✅ Backup created successfully: {backup_path}")
        print(f"   Size: {backup_path.stat().st_size / 1024:.2f} KB")
        
        # Compress if requested
        if compress:
            import gzip
            compressed_path = backup_path.with_suffix('.db.gz')
            
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            backup_path.unlink()
            
            print(f"✅ Compressed backup: {compressed_path}")
            print(f"   Compressed size: {compressed_path.stat().st_size / 1024:.2f} KB")
            
            return str(compressed_path)
        
        return str(backup_path)
    
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        sys.exit(1)


def cleanup_old_backups(backup_dir: str = None, keep_count: int = 10):
    """
    Remove old backups, keeping only the most recent ones.
    
    Args:
        backup_dir: Directory containing backups
        keep_count: Number of recent backups to keep
    """
    if backup_dir is None:
        backup_dir = Path(__file__).parent.parent.parent / "data" / "backups"
    else:
        backup_dir = Path(backup_dir)
    
    if not backup_dir.exists():
        print("No backup directory found.")
        return
    
    # Get all backup files
    backup_files = sorted(
        backup_dir.glob("*_backup_*.db*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    # Remove old backups
    for backup_file in backup_files[keep_count:]:
        print(f"Removing old backup: {backup_file.name}")
        backup_file.unlink()
    
    print(f"✅ Cleanup complete. Kept {min(keep_count, len(backup_files))} most recent backups.")


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
        print(f"❌ Backup file not found: {backup_path}")
        return False
    
    # Handle compressed backups
    if backup_path.suffix == '.gz':
        import gzip
        import tempfile
        
        # Extract to temporary file
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
            
            print(f"✅ Backup verified: {len(tables)} tables found")
            return True
        except Exception as e:
            print(f"❌ Backup verification failed: {e}")
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
            
            print(f"✅ Backup verified: {len(tables)} tables found")
            return True
        except Exception as e:
            print(f"❌ Backup verification failed: {e}")
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database backup script")
    parser.add_argument(
        '--backup-dir',
        help='Directory to store backups (default: data/backups)'
    )
    parser.add_argument(
        '--no-compress',
        action='store_true',
        help='Do not compress the backup'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up old backups'
    )
    parser.add_argument(
        '--keep',
        type=int,
        default=10,
        help='Number of backups to keep when cleaning up (default: 10)'
    )
    parser.add_argument(
        '--verify',
        help='Verify a backup file'
    )
    
    args = parser.parse_args()
    
    if args.verify:
        verify_backup(args.verify)
    elif args.cleanup:
        cleanup_old_backups(args.backup_dir, args.keep)
    else:
        backup_path = create_backup(
            backup_dir=args.backup_dir,
            compress=not args.no_compress
        )
        
        # Verify the backup
        verify_backup(backup_path)
        
        # Cleanup old backups
        cleanup_old_backups(args.backup_dir, args.keep)
