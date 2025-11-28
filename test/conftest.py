"""
pytest configuration file for the insulin project tests.

This conftest.py file is automatically loaded by pytest before running tests.
It provides two main features:

1. PATH CONFIGURATION:
   Adjusts Python import path to ensure that modules in the project root
   (cleaner.py, split_insulin.py, etc.) can be imported by test files.
   
   The issue: When pytest runs, sys.path may not include the project root,
   causing "ModuleNotFoundError" when tests try to import project modules.
   
   The solution: We add the project root to sys.path automatically.

2. INTERACTIVE CLEANUP AFTER TESTS:
   After all tests complete, prompts the user whether to delete generated
   sequence files (*_seq_clean.txt) from the project root directory.
   
   This gives users control over keeping or removing pipeline output files.

WORKFLOW OPTIONS:

A) Run tests normally (with cleanup prompt):
   $ pytest -v
   → Tests run, then prompts: "Do you want to delete these files? (y/n)"

B) Run tests and keep generated files (skip cleanup prompt):
   $ pytest -v --keep-generated
   → Tests run, files remain, no prompt

C) Manual pipeline testing workflow:
   Step 1: Clean existing files first
   $ python -c "from pathlib import Path; [f.unlink() for f in Path('.').glob('*_seq_clean.txt')]"
   
   Step 2: Run pipeline scripts manually
   $ python cleaner.py
   $ python split_insulin.py
   $ python string-insulin.py
   $ python net-charge.py
   
   Step 3: Test with pre-generated files
   $ pytest -v --keep-generated
   → Tests validate the manually generated files, no cleanup prompt

IMPORTANT DISTINCTIONS:
- cleaner.py: Cleans raw ORIGIN format sequences (input processing)
- conftest.py: Manages test environment and post-test cleanup (this file)
- .gitignore: Prevents *_seq_clean.txt files from being committed to git
"""

import sys
from pathlib import Path

# Get the absolute path to the project root (parent of the test directory)
# Path(__file__).resolve() = absolute path of conftest.py
# .parent = test directory
# .parent = project root
project_root = Path(__file__).resolve().parent.parent

# Add project root to sys.path if not already there
# This allows tests to import modules from the project root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import pytest


def pytest_addoption(parser):
    """
    Add custom command-line options to pytest.
    
    Options:
        --keep-generated: Skip the interactive cleanup prompt after tests.
                         Useful when you want to inspect generated files.
    """
    parser.addoption(
        "--keep-generated",
        action="store_true",
        default=False,
        help="Skip cleanup prompt and keep generated *_seq_clean.txt files after tests"
    )


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook that runs after all tests complete.
    
    This hook prompts the user to decide whether to delete generated sequence
    files (*_seq_clean.txt) from the project root directory.
    
    Can be skipped with: pytest --keep-generated
    
    Args:
        session: The pytest session object
        exitstatus: The exit status code (0 = success, non-zero = failures)
    
    Note: This only runs in interactive mode (not in CI/CD or with --no-header)
    """
    # Check if user wants to skip cleanup prompt
    keep_generated = session.config.getoption("--keep-generated")
    
    if keep_generated:
        # User explicitly wants to keep files, skip prompt entirely
        return
    
    # Find all generated sequence files in the project root
    generated_files = list(project_root.glob("*_seq_clean.txt"))
    
    # Only prompt if there are files to delete
    # Note: We removed sys.stdin.isatty() check to allow prompts even when
    # run from scripts (like run_pipeline_and_test.py)
    if generated_files:
        print("\n" + "="*70)
        print("GENERATED FILES DETECTED")
        print("="*70)
        print(f"\nThe following {len(generated_files)} file(s) were generated during the workflow:")
        for file_path in generated_files:
            print(f"  - {file_path.name}")
        
        print("\nThese files are outputs from cleaner.py and split_insulin.py.")
        print("They are automatically ignored by .gitignore (*_seq_clean.txt pattern).")
        print("\nTip: Use 'pytest --keep-generated' to skip this prompt.")
        
        # Prompt user for decision
        try:
            response = input("\nDo you want to delete these files? (y/n): ").strip().lower()
            
            if response in ['y', 'yes']:
                deleted_count = 0
                for file_path in generated_files:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"  Warning: Could not delete {file_path.name}: {e}")
                
                print(f"\nSuccessfully deleted {deleted_count} file(s).")
            else:
                print("\nFiles kept. You can manually delete them later or run the pipeline again.")
        
        except (KeyboardInterrupt, EOFError):
            print("\n\nCleanup skipped. Files remain in the project root.")
        
        print("="*70 + "\n")

