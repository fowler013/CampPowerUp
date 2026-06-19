#!/usr/bin/env python3
"""
ROM Organization Script for CampPowerUp Gaming Server

This script helps organize ROM files into the correct directories based on
file extension. It can also validate files and generate reports.

Usage:
    python organize_roms.py /path/to/unsorted/roms
    python organize_roms.py --validate
    python organize_roms.py --report
"""

import os
import shutil
import argparse
from pathlib import Path
from collections import defaultdict

# ROM extensions mapped to target directories
ROM_MAPPINGS = {
    # NES
    '.nes': 'nes',
    '.unf': 'nes',
    '.unif': 'nes',
    
    # SNES
    '.sfc': 'snes',
    '.smc': 'snes',
    
    # Sega Genesis / Mega Drive
    '.md': 'genesis',
    '.gen': 'genesis',
    '.bin': 'genesis',  # Note: .bin is ambiguous, may need manual sorting
    '.smd': 'genesis',
    
    # Game Boy / Game Boy Color
    '.gb': 'gb',
    '.gbc': 'gb',
    
    # Game Boy Advance
    '.gba': 'gba',
    
    # Nintendo 64
    '.n64': 'n64',
    '.z64': 'n64',
    '.v64': 'n64',
    
    # PlayStation
    '.cue': 'psx',
    '.chd': 'psx',
    '.iso': 'psx',
    '.pbp': 'psx',
    
    # Arcade (MAME)
    '.zip': 'arcade',  # Note: .zip is ambiguous for arcade
}

# BIOS files that should go to bios directory
BIOS_FILES = {
    'scph1001.bin': 'psx',
    'scph5500.bin': 'psx',
    'scph5501.bin': 'psx',
    'scph5502.bin': 'psx',
    'gba_bios.bin': 'gba',
    'gb_bios.bin': 'gb',
    'gbc_bios.bin': 'gb',
}

# Get the gaming-server directory (parent of scripts/)
SCRIPT_DIR = Path(__file__).parent
GAMING_SERVER_DIR = SCRIPT_DIR.parent
ROMS_DIR = GAMING_SERVER_DIR / 'roms'
BIOS_DIR = GAMING_SERVER_DIR / 'bios'


def get_target_directory(filename: str) -> tuple[str, str]:
    """
    Determine the target directory for a ROM file.
    
    Returns:
        tuple: (directory_type, directory_name) where type is 'roms' or 'bios'
    """
    filename_lower = filename.lower()
    
    # Check if it's a BIOS file
    for bios_name, system in BIOS_FILES.items():
        if bios_name in filename_lower:
            return ('bios', system)
    
    # Check by extension
    ext = Path(filename).suffix.lower()
    if ext in ROM_MAPPINGS:
        return ('roms', ROM_MAPPINGS[ext])
    
    return (None, None)


def organize_roms(source_dir: str, dry_run: bool = False, copy: bool = False):
    """
    Organize ROM files from source directory into appropriate subdirectories.
    
    Args:
        source_dir: Path to directory containing unsorted ROMs
        dry_run: If True, only print what would be done
        copy: If True, copy files instead of moving them
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"Error: Source directory '{source_dir}' does not exist")
        return
    
    stats = defaultdict(int)
    unrecognized = []
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Organizing ROMs from: {source_path}")
    print(f"Target ROMs directory: {ROMS_DIR}")
    print(f"Target BIOS directory: {BIOS_DIR}")
    print("-" * 60)
    
    # Walk through all files in source directory
    for root, dirs, files in os.walk(source_path):
        for filename in files:
            if filename.startswith('.'):
                continue
                
            source_file = Path(root) / filename
            dir_type, system = get_target_directory(filename)
            
            if dir_type is None:
                unrecognized.append(str(source_file))
                stats['unrecognized'] += 1
                continue
            
            # Determine target path
            if dir_type == 'bios':
                target_dir = BIOS_DIR / system
            else:
                target_dir = ROMS_DIR / system
            
            target_file = target_dir / filename
            
            # Create target directory if needed
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
            
            # Skip if file already exists
            if target_file.exists():
                print(f"  SKIP (exists): {filename}")
                stats['skipped'] += 1
                continue
            
            # Move or copy the file
            action = "COPY" if copy else "MOVE"
            print(f"  {action}: {filename} -> {dir_type}/{system}/")
            
            if not dry_run:
                if copy:
                    shutil.copy2(source_file, target_file)
                else:
                    shutil.move(source_file, target_file)
            
            stats[system] += 1
            stats['total'] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for system in ['nes', 'snes', 'genesis', 'gb', 'gba', 'n64', 'psx', 'arcade']:
        if stats[system] > 0:
            print(f"  {system.upper():12} {stats[system]:4} files")
    
    print(f"\n  Total organized: {stats['total']}")
    print(f"  Skipped (exists): {stats['skipped']}")
    print(f"  Unrecognized: {stats['unrecognized']}")
    
    if unrecognized:
        print("\nUnrecognized files (need manual sorting):")
        for f in unrecognized[:10]:
            print(f"  - {f}")
        if len(unrecognized) > 10:
            print(f"  ... and {len(unrecognized) - 10} more")


def validate_library():
    """Validate the ROM library structure and report any issues."""
    print("\nValidating ROM Library")
    print("=" * 60)
    
    issues = []
    
    # Check ROM directories exist
    for system in ['nes', 'snes', 'genesis', 'gb', 'gba', 'n64', 'psx', 'arcade']:
        system_dir = ROMS_DIR / system
        if not system_dir.exists():
            issues.append(f"Missing directory: roms/{system}/")
        elif not any(system_dir.iterdir()):
            # Only .gitkeep exists
            files = list(system_dir.glob('*'))
            if len(files) == 1 and files[0].name == '.gitkeep':
                issues.append(f"Empty directory: roms/{system}/ (only .gitkeep)")
    
    # Check for required BIOS files
    psx_bios = BIOS_DIR / 'psx'
    if psx_bios.exists():
        has_psx_bios = any(f.suffix == '.bin' for f in psx_bios.glob('*'))
        if not has_psx_bios:
            issues.append("Missing PlayStation BIOS (required for PSX games)")
    
    gba_bios = BIOS_DIR / 'gba'
    if gba_bios.exists():
        has_gba_bios = any('bios' in f.name.lower() for f in gba_bios.glob('*'))
        if not has_gba_bios:
            issues.append("Missing GBA BIOS (recommended for GBA games)")
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print("\n✅ All checks passed!")
    
    return len(issues) == 0


def generate_report():
    """Generate a report of the current ROM library."""
    print("\n" + "=" * 60)
    print("ROM LIBRARY REPORT")
    print("=" * 60)
    
    total_files = 0
    total_size = 0
    
    systems = {
        'nes': 'Nintendo Entertainment System',
        'snes': 'Super Nintendo',
        'genesis': 'Sega Genesis / Mega Drive',
        'gb': 'Game Boy / Game Boy Color',
        'gba': 'Game Boy Advance',
        'n64': 'Nintendo 64',
        'psx': 'PlayStation',
        'arcade': 'Arcade (MAME)',
    }
    
    for system, name in systems.items():
        system_dir = ROMS_DIR / system
        if system_dir.exists():
            files = [f for f in system_dir.glob('*') if f.name != '.gitkeep']
            count = len(files)
            size = sum(f.stat().st_size for f in files if f.is_file())
            
            if count > 0:
                print(f"\n{name} ({system.upper()})")
                print(f"  Games: {count}")
                print(f"  Size: {format_size(size)}")
                
                # List first 5 games
                print("  Sample titles:")
                for f in sorted(files)[:5]:
                    print(f"    - {f.stem}")
                if count > 5:
                    print(f"    ... and {count - 5} more")
                
                total_files += count
                total_size += size
    
    print("\n" + "-" * 60)
    print(f"TOTAL: {total_files} games, {format_size(total_size)}")
    
    # Check BIOS status
    print("\nBIOS Status:")
    for system in ['psx', 'gba', 'gb']:
        bios_dir = BIOS_DIR / system
        if bios_dir.exists():
            bios_files = [f for f in bios_dir.glob('*') if f.name != '.gitkeep']
            if bios_files:
                print(f"  ✅ {system.upper()}: {len(bios_files)} file(s)")
            else:
                print(f"  ❌ {system.upper()}: Missing")
        else:
            print(f"  ❌ {system.upper()}: Directory not found")


def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='Organize ROM files for CampPowerUp Gaming Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Organize ROMs from a directory (moves files)
  python organize_roms.py /path/to/unsorted/roms
  
  # Preview what would happen (dry run)
  python organize_roms.py /path/to/unsorted/roms --dry-run
  
  # Copy instead of move
  python organize_roms.py /path/to/unsorted/roms --copy
  
  # Validate library structure
  python organize_roms.py --validate
  
  # Generate library report
  python organize_roms.py --report
        """
    )
    
    parser.add_argument('source', nargs='?', help='Source directory containing unsorted ROMs')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--copy', '-c', action='store_true', help='Copy files instead of moving them')
    parser.add_argument('--validate', '-v', action='store_true', help='Validate the ROM library structure')
    parser.add_argument('--report', '-r', action='store_true', help='Generate a report of the ROM library')
    
    args = parser.parse_args()
    
    if args.validate:
        validate_library()
    elif args.report:
        generate_report()
    elif args.source:
        organize_roms(args.source, dry_run=args.dry_run, copy=args.copy)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
