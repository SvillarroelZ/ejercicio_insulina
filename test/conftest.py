# pytest configuration file for the insulin project tests.
# This conftest.py file is automatically loaded by pytest before running tests.
# It provides three main features:
# 1. PATH CONFIGURATION: Adjusts Python import path to ensure that modules in the src/ directory can be imported by test files.
#    The issue: When pytest runs, sys.path may not include the src/ directory, causing "ModuleNotFoundError" when tests try to import project modules.
#    The solution: We add the src/ directory to sys.path automatically.
# 2. INTERACTIVE CLEANUP AFTER TESTS: After all tests complete, prompts the user whether to delete generated sequence files (*_seq_clean.txt) from the data/ directory.
#    This gives users control over keeping or removing pipeline output files.
# 3. CODE COVERAGE DISPLAY: Shows real code coverage percentage per source file in verbose mode (how much of each file is tested).
#    - Quiet mode (-q, -qq): Shows only dots/F/E and test count (minimal noise)
#    - Verbose mode (-v, -vv): Shows code coverage percentage per source file with color coding:
#      * Green (95-100%): Excellent coverage
#      * Yellow (80-94%): Good coverage, consider adding more tests
#      * Red (<80%): Needs more test coverage
# WORKFLOW OPTIONS:
# A) Quick tests (minimal output): $ pytest -q --keep-generated (clean output, no coverage display, no cleanup prompt)
# B) Detailed tests with coverage: $ pytest -v --keep-generated (shows code coverage per file, no cleanup prompt)
# C) Tests with cleanup prompt: $ pytest -v (shows coverage, then asks to delete generated files)
# D) Manual pipeline testing workflow:
#    Step 1: Clean existing files first $ python -c "from pathlib import Path; [f.unlink() for f in Path('data').glob('*_seq_clean.txt')]"
#    Step 2: Run pipeline scripts manually $ python src/cleaner.py; python src/split_insulin.py; python src/string_insulin.py; python src/net_charge.py
#    Step 3: Test with pre-generated files $ pytest -v --keep-generated (tests validate the manually generated files, shows coverage, no cleanup prompt)
# IMPORTANT DISTINCTIONS:
# - cleaner.py: Cleans raw ORIGIN format sequences (input processing)
# - conftest.py: Manages test environment and post-test cleanup (this file)
# - .gitignore: Prevents *_seq_clean.txt files from being committed to git
# COVERAGE EXPLANATION:
# - Coverage shows what percentage of code lines in each source file are actually executed during tests
# - Example: src/net_charge.py [98%] means 98% of lines in net_charge.py are tested, 2% are not covered
# - Use this to identify which parts of your code need more tests

import sys
from pathlib import Path
from collections import defaultdict

# Absolute path to the project root (parent of the test directory)
project_root = Path(__file__).resolve().parent.parent

# Ensure only src/ is added to sys.path for imports like `from cleaner import ...`.
# Adding project_root is unnecessary for current tests and can be omitted safely.
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


import pytest


def pytest_configure(config):
    # Configure pytest custom markers.
    # Default options (verbose, coverage, warnings) are set in pytest.ini for simplicity. Just run: pytest
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (full pipeline, CLI, error handling)"
    )


def pytest_collection_modifyitems(config, items):
    # Mark integration tests for the consolidated test_integration_pipeline.py file.
    # All tests in test_cleaner.py, test_net_charge.py, test_split_insulin.py, and test_string_insulin.py run by default.
    # Integration tests (in test_integration_pipeline.py) are marked for documentation purposes but still run by default.
    # Note: config parameter required by pytest hook signature but not used in this implementation
    integration_files = {
        "test_integration_pipeline.py"
    }
    
    for item in items:
        fname = item.fspath.basename
        if fname in integration_files:
            item.add_marker(pytest.mark.integration)


def pytest_addoption(parser):
    # Add custom command-line options to pytest.
    # Options: --keep-generated: Skip the interactive cleanup prompt after tests. Useful when you want to inspect generated files.
    parser.addoption(
        "--keep-generated",
        action="store_true",
        default=False,
        help="Skip cleanup prompt and keep generated *_seq_clean.txt files after tests"
    )


# Minimal plugin: group and display results per file
_file_seen = []  # ordered list of files (absolute paths)
_file_relmap = {}  # abs -> rel path relative to project_root
_file_counts = defaultdict(lambda: {"passed": 0, "failed": 0, "error": 0, "skipped": 0})
_file_items_count = defaultdict(int)  # number of tests per file
_total_items = 0


def pytest_collection_finish(session):
    # Register unique files and test counts per file
    global _total_items
    _total_items = len(session.items)
    seen = []
    for item in session.items:
        abs_path = str(item.fspath)
        rel_path = str(Path(abs_path).resolve().relative_to(project_root)) if Path(abs_path).resolve().is_relative_to(project_root) else abs_path
        _file_relmap[abs_path] = rel_path
        _file_items_count[abs_path] += 1
        if abs_path not in seen:
            seen.append(abs_path)
    _file_seen.extend(seen)


def pytest_runtest_logreport(report):
    # Update counts per file based on test result
    nodeid = report.nodeid
    test_file = nodeid.split("::", 1)[0]
    if report.skipped:
        _file_counts[test_file]["skipped"] += 1
    elif report.failed:
        # Failures in setup/call/teardown count as error or failed; we unify as failed
        if report.when in ("setup", "teardown"):
            _file_counts[test_file]["error"] += 1
        else:
            _file_counts[test_file]["failed"] += 1
    elif report.passed and report.when == "call":
        _file_counts[test_file]["passed"] += 1


# Do not modify state per test to avoid forcing verbose mode


def pytest_terminal_summary(terminalreporter, config):
    # Print code coverage summary per source file with detailed stats, BEFORE cleanup prompt
    # Skip summary in quiet mode (-q or -qq)
    if config.option.verbose < 0:  # -q sets verbose to -1, -qq to -2
        _handle_cleanup(config)
        return
    
    tr = terminalreporter
    tw = getattr(tr, "_tw", tr.writer if hasattr(tr, "writer") else None)
    
    # Try to get coverage data
    try:
        import coverage
        cov = coverage.Coverage()
        cov.load()
        
        # Get coverage data
        data = cov.get_data()
        
        tr.write_line("")
        
        # Get all source files from src/ directory
        src_files = sorted(project_root.glob("src/*.py"))
        
        for src_file in src_files:
            if src_file.name.startswith("__"):
                continue
            
            rel_path = f"src/{src_file.name}"
            
            # Get coverage statistics for this file
            analysis = cov.analysis2(str(src_file))
            if analysis:
                executed = len(analysis[1])  # executed lines
                missing = len(analysis[3])   # missing lines
                total = executed + missing
                pct = int(round((executed / total) * 100)) if total > 0 else 0
                
                # Format: "src/file.py [100%] (58/58 lines)"
                left = f"{rel_path.ljust(50)} "
                coverage_info = f"[{pct:>3}%] ({executed}/{total} lines)"
                
                if tw is not None:
                    tw.write(left)
                    if pct < 80:
                        tw.write(coverage_info, red=True)
                    elif pct < 95:
                        tw.write(coverage_info, yellow=True)
                    else:
                        tw.write(coverage_info, green=True)
                    tw.write("\n")
                else:
                    tr.write_line(f"{left}{coverage_info}")
    
    except (ImportError, Exception):
        # If coverage is not available or fails, show test file summary instead
        tr.write_line("")
        
        for abs_path in _file_seen:
            rel = _file_relmap.get(abs_path, abs_path)
            counts = _file_counts.get(rel, {})
            total = counts.get("passed", 0) + counts.get("failed", 0) + counts.get("error", 0) + counts.get("skipped", 0)
            passed = counts.get("passed", 0)
            
            pct = int(round((passed / total) * 100)) if total > 0 else 100
            
            left = f"{rel.ljust(75)} "
            if tw is not None:
                tw.write(left)
                if pct < 70:
                    tw.write(f"[{pct:>3}%]", red=True)
                elif pct < 100:
                    tw.write(f"[{pct:>3}%]", yellow=True)
                else:
                    tw.write(f"[{pct:>3}%]", green=True)
                tw.write("\n")
            else:
                tr.write_line(f"{left}[{pct:>3}%]")
    
    # Handle cleanup here, after the summary
    _handle_cleanup(config)


def _handle_cleanup(config):
    # Separate cleanup logic to keep code clean
    keep_generated = config.getoption("--keep-generated")
    
    if keep_generated:
        return
    
    # Find all generated sequence files in the data/ directory
    data_dir = project_root / "data"
    generated_files = list(data_dir.glob("*_seq_clean.txt")) if data_dir.exists() else []
    
    # Only prompt if there are files to delete
    if generated_files:
        # Temporarily disable output capture to allow interactive input
        capmanager = config.pluginmanager.getplugin("capturemanager")
        if capmanager:
            capmanager.suspend_global_capture(in_=True)
        
        try:
            # Concise prompt, minimal noise
            print(f"\nGenerated outputs detected: {len(generated_files)} file(s).")
            print("Use 'pytest --keep-generated' to skip this prompt.")
            
            # Prompt user for decision
            try:
                response = input("Delete generated files now? (y/N): ").strip().lower()
                
                if response in ['y', 'yes']:
                    deleted_count = 0
                    for file_path in generated_files:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception as e:
                            print(f"Warning: Could not delete {file_path.name}: {e}")
                    print(f"Deleted {deleted_count} file(s).")
                else:
                    print("Kept generated files.")
            
            except (KeyboardInterrupt, EOFError):
                print("Cleanup skipped. Files remain.")
        
        finally:
            # Re-enable output capture
            if capmanager:
                capmanager.resume_global_capture()

