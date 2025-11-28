#!/usr/bin/env python3
"""
Reset workspace utility for insulin project.

This script removes all generated files and artifacts from the workspace:
  Generated sequence files (*_seq_clean.txt) from pipeline execution
  Test cache directories (.pytest_cache, __pycache__)
  Coverage reports (.coverage, htmlcov/)

Use this to reset the workspace to a clean state before running the pipeline.

Note: This is different from cleaner.py which cleans ORIGIN format sequences.
      This script resets the entire workspace by removing generated artifacts.

Usage:
    python reset_workspace.py           # Interactive: shows files and asks confirmation
    python reset_workspace.py --force   # Non-interactive: deletes without asking
    python reset_workspace.py --list    # Just list files without deleting
"""

import sys
from pathlib import Path
import shutil


def find_generated_files(project_root):
    """Find all generated files that should be cleaned."""
    files_to_clean = []
    
    # 1. Generated sequence files in project root (*_seq_clean.txt)
    sequence_files = list(project_root.glob("*_seq_clean.txt"))
    files_to_clean.extend(sequence_files)
    
    # 2. Test cache directories
    cache_dirs = [
        project_root / ".pytest_cache",
        project_root / "__pycache__",
        project_root / "test" / "__pycache__",
    ]
    
    # 3. Coverage files
    coverage_files = [
        project_root / ".coverage",
        project_root / "htmlcov",
    ]
    
    return {
        'sequence_files': sequence_files,
        'cache_dirs': [d for d in cache_dirs if d.exists()],
        'coverage_files': [f for f in coverage_files if f.exists()],
    }


def display_files(files_dict):
    """Display all files that will be cleaned."""
    total = 0
    
    if files_dict['sequence_files']:
        print("\nGenerated sequence files (*_seq_clean.txt):")
        for f in files_dict['sequence_files']:
            size = f.stat().st_size if f.is_file() else 0
            print(f"  {f.name} ({size} bytes)")
            total += 1
    
    if files_dict['cache_dirs']:
        print("\nCache directories:")
        for d in files_dict['cache_dirs']:
            print(f"  {d.name}/")
            total += 1
    
    if files_dict['coverage_files']:
        print("\nCoverage files:")
        for f in files_dict['coverage_files']:
            name = f.name if f.is_file() else f"{f.name}/"
            print(f"  {name}")
            total += 1
    
    return total


def clean_files(files_dict):
    """Delete all files and directories."""
    deleted = 0
    errors = []
    
    # Delete sequence files
    for f in files_dict['sequence_files']:
        try:
            f.unlink()
            deleted += 1
        except Exception as e:
            errors.append(f"Failed to delete {f.name}: {e}")
    
    # Delete cache directories
    for d in files_dict['cache_dirs']:
        try:
            shutil.rmtree(d)
            deleted += 1
        except Exception as e:
            errors.append(f"Failed to delete {d.name}/: {e}")
    
    # Delete coverage files
    for f in files_dict['coverage_files']:
        try:
            if f.is_file():
                f.unlink()
            else:
                shutil.rmtree(f)
            deleted += 1
        except Exception as e:
            errors.append(f"Failed to delete {f.name}: {e}")
    
    return deleted, errors


def main():
    """Main reset workspace function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reset workspace by removing generated files and artifacts"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Delete files without confirmation"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List files without deleting"
    )
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).resolve().parent
    
    # Find all generated files
    files_dict = find_generated_files(project_root)
    
    # Display files
    total = display_files(files_dict)
    
    if total == 0:
        print("\nWorkspace is already clean. No generated files found.")
        return 0
    
    print(f"\nTotal items: {total}")
    
    # If --list flag, just list and exit
    if args.list:
        print("\n(use --force to delete without confirmation)")
        return 0
    
    # Determine if we need confirmation
    should_delete = args.force
    
    if not should_delete:
        try:
            response = input("\nDelete these files? (y/n): ").strip().lower()
            should_delete = response in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            print("\n\nCancelled by user.")
            return 1
    
    # Delete files if confirmed
    if should_delete:
        deleted, errors = clean_files(files_dict)
        
        if errors:
            print("\nErrors occurred:")
            for error in errors:
                print(f"  {error}")
        
        print(f"\nSuccessfully deleted {deleted} item(s).")
        return 0
    else:
        print("\nNo changes made. Workspace unchanged.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
