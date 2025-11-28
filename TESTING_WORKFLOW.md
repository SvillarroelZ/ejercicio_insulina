# Insulin Processing Pipeline Testing Workflow

## Overview

This document describes the complete workflow for testing the insulin processing pipeline.

## Pipeline Components

1. cleaner.py: Cleans raw ORIGIN format sequences (removes numbers and formatting)
2. split_insulin.py: Splits 110 aa preproinsulin into 4 segments (LS, B, C, A chains)
3. string-insulin.py: Calculates molecular weight of insulin (B + A chains)
4. net-charge.py: Calculates net charge table across pH 0-14

## File Naming Clarification

To avoid confusion between similar sounding scripts:

  cleaner.py: Cleans ORIGIN format sequences (input processing)
  reset_workspace.py: Resets workspace by removing all generated files and artifacts

## Complete Testing Workflow

### Step 1: Clean Workspace (Before Starting)

Remove any previously generated files to ensure a clean state:

```bash
python reset_workspace.py
```

This removes:
  Generated sequence files (*_seq_clean.txt)
  Test cache directories (.pytest_cache, __pycache__)
  Coverage reports (.coverage, htmlcov/)

Options:
  --list : Just show what would be deleted
  --force : Delete without confirmation

### Step 2: Run Tests BEFORE Pipeline

Verify that all test infrastructure works correctly:

```bash
pytest -v
```

Expected result: All 21 tests should pass. Tests create their own temporary files and clean up automatically.

Note: If generated files exist from a previous run, pytest will prompt you to delete them at the end.

### Step 3: Execute Pipeline Manually

Run each script in order to generate the workflow outputs:

```bash
python cleaner.py
python split_insulin.py
python string-insulin.py
python net-charge.py
```

Generated files:
  preproinsulin_seq_clean.txt (110 amino acids, cleaned)
  lsinsulin_seq_clean.txt (24 amino acids, leader sequence)
  binsulin_seq_clean.txt (30 amino acids, B chain)
  cinsulin_seq_clean.txt (35 amino acids, C peptide)
  ainsulin_seq_clean.txt (21 amino acids, A chain)

### Step 4: Run Tests AFTER Pipeline

Test the generated files and validate the pipeline output:

```bash
pytest -v
```

What happens:
1. All 21 tests run and validate pipeline outputs
2. After tests complete, you will see a prompt:

```
======================================================================
GENERATED FILES DETECTED
======================================================================

The following 5 file(s) were generated during the workflow:
  preproinsulin_seq_clean.txt
  lsinsulin_seq_clean.txt
  binsulin_seq_clean.txt
  cinsulin_seq_clean.txt
  ainsulin_seq_clean.txt

These files are outputs from cleaner.py and split_insulin.py.
They are automatically ignored by .gitignore (*_seq_clean.txt pattern).

Tip: Use 'pytest --keep-generated' to skip this prompt.

Do you want to delete these files? (y/n):
```

3. Choose:
  y or yes: Delete generated files (clean workspace)
  n or no: Keep files for inspection

---

## Alternative Commands

### Run tests without cleanup prompt

If you want to keep generated files without being prompted:

```bash
pytest -v --keep-generated
```

### Run tests with coverage report

```bash
pytest --cov=. --cov-report=term-missing
```

### Generate HTML coverage report

```bash
pytest --cov=. --cov-report=html
```
Then open htmlcov/index.html in browser

## File Management

### What gets committed to git

Tracked files:
  Source code: cleaner.py, split_insulin.py, string-insulin.py, net-charge.py
  Utilities: reset_workspace.py (workspace cleanup utility)
  Original data: preproinsulin_seq.txt (NEVER deleted)
  Test files: test/*.py
  Configuration: .gitignore, test/conftest.py

Ignored files (in .gitignore):
  Generated sequences: *_seq_clean.txt
  Test cache: .pytest_cache/, __pycache__/
  Coverage: .coverage, htmlcov/
  Virtual environment: .venv/

## Quick Reference

```bash
# Full workflow
python reset_workspace.py
pytest -v
python cleaner.py
python split_insulin.py
python string-insulin.py
python net-charge.py
pytest -v

# One liner for Steps 3 and 4
python cleaner.py && python split_insulin.py && python string-insulin.py && python net-charge.py && pytest -v
```

## Important Notes

1. Original data is protected: preproinsulin_seq.txt is NEVER deleted by any script
2. Tests are isolated: Tests use temporary directories (tmp_path) and do not interfere with manual pipeline execution
3. Interactive cleanup: The prompt at the end gives you control over generated files
4. File naming: cleaner.py cleans sequences, reset_workspace.py resets the workspace
5. Coverage: Currently at 99% overall, 100% on all main modules

## Troubleshooting

Q: Tests fail with "FileNotFoundError"
A: Make sure you are in the project root directory when running pytest.

Q: Cleanup prompt does not appear
A: Use pytest -v (not pytest from a script). Or the prompt only appears if *_seq_clean.txt files exist.

Q: Want to skip prompt entirely
A: Use pytest -v --keep-generated

Q: How to see test coverage
A: Run pytest --cov=. --cov-report=term-missing
