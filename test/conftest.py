"""
pytest configuration file for the insulin project tests.

This conftest.py file is automatically loaded by pytest before running tests.
It adjusts the Python import path to ensure that modules in the project root
(cleaner.py, split_insulin.py, etc.) can be imported by the test files.

Additionally, this file provides a fixture that cleans up any generated files
in the project root after each test completes. This ensures tests don't pollute
the repository with generated artifacts.

The issue: When pytest runs, it uses sys.path which may not include the
project root directory. This causes "ModuleNotFoundError" when tests try to
import project modules like 'from cleaner import clean_sequence'.

The solution: We add the project root to sys.path in this conftest.py file,
which pytest loads automatically. This ensures all project modules are
discoverable no matter how pytest is invoked.
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


@pytest.fixture(autouse=True)
def cleanup_generated_files():
    """
    Automatically clean up generated sequence files after each test.
    
    This fixture uses autouse=True, which means it runs after every test
    without needing to be explicitly requested in the test function.
    
    Generated files that should be cleaned up:
      - preproinsulin_seq_clean.txt
      - lsinsulin_seq_clean.txt
      - binsulin_seq_clean.txt
      - cinsulin_seq_clean.txt
      - ainsulin_seq_clean.txt
    
    We preserve preproinsulin_seq.txt (the original input file) since it's
    part of the project data.
    """
    # Yield control to the test (allow it to run)
    yield
    
    # After the test completes, clean up generated files
    generated_files = [
        project_root / "preproinsulin_seq_clean.txt",
        project_root / "lsinsulin_seq_clean.txt",
        project_root / "binsulin_seq_clean.txt",
        project_root / "cinsulin_seq_clean.txt",
        project_root / "ainsulin_seq_clean.txt",
    ]
    
    for file_path in generated_files:
        # Use try/except to silently ignore files that don't exist
        # (tests might not have generated all files)
        try:
            if file_path.exists():
                file_path.unlink()  # Delete the file
        except Exception:
            pass  # Silently ignore any errors during cleanup

