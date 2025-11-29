"""
Tests for __main__ blocks to achieve 100% coverage.

These tests execute the scripts as if run from command line (python script.py)
using runpy.run_path(), which covers the `if __name__ == "__main__":` blocks.
"""

import runpy
from pathlib import Path


def test_cleaner_main_block(tmp_path, monkeypatch):
    """
    Test that cleaner.py can be executed as __main__ (python cleaner.py).
    
    This covers the `if __name__ == "__main__":` block in cleaner.py (line 49).
    """
    # Step 1: Create test input file
    repo_root = Path(__file__).resolve().parents[1]
    input_content = "ORIGIN\n1 malwmrllpl\n//\n"
    input_file = tmp_path / "preproinsulin_seq.txt"
    input_file.write_text(input_content)
    
    # Step 2: Create data directory for output
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Step 3: Change to tmp_path so script reads/writes there
    monkeypatch.chdir(tmp_path)
    
    # Step 4: Execute cleaner.py as __main__
    # runpy.run_path() executes the script as if you ran `python cleaner.py`
    # This triggers the `if __name__ == "__main__":` block
    script_path = str(repo_root / "cleaner.py")
    runpy.run_path(script_path, run_name="__main__")
    
    # Step 5: Verify output was created
    output_file = data_dir / "preproinsulin_seq_clean.txt"
    assert output_file.exists(), "cleaner.py should create output file"
    
    # Step 6: Verify content
    content = output_file.read_text().strip()
    assert len(content) > 0, "Output should not be empty"
    assert content.isalpha(), "Output should contain only letters"
    assert content.islower(), "Output should be lowercase"


def test_split_insulin_main_block(tmp_path, monkeypatch):
    """
    Test that split_insulin.py can be executed as __main__.
    
    This covers the `if __name__ == "__main__":` block in split_insulin.py (line 69).
    """
    # Step 1: Create test input (110 aa sequence)
    seq_110 = (
        "malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
        "reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
    )
    
    # Step 2: Create data directory with input file
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    input_file = data_dir / "preproinsulin_seq_clean.txt"
    input_file.write_text(seq_110)
    
    # Step 3: Change to tmp_path
    monkeypatch.chdir(tmp_path)
    
    # Step 4: Execute split_insulin.py as __main__
    repo_root = Path(__file__).resolve().parents[1]
    script_path = str(repo_root / "split_insulin.py")
    runpy.run_path(script_path, run_name="__main__")
    
    # Step 5: Verify all 4 output files were created
    ls_file = data_dir / "lsinsulin_seq_clean.txt"
    b_file = data_dir / "binsulin_seq_clean.txt"
    c_file = data_dir / "cinsulin_seq_clean.txt"
    a_file = data_dir / "ainsulin_seq_clean.txt"
    
    assert ls_file.exists(), "split_insulin.py should create LS file"
    assert b_file.exists(), "split_insulin.py should create B file"
    assert c_file.exists(), "split_insulin.py should create C file"
    assert a_file.exists(), "split_insulin.py should create A file"
    
    # Step 6: Verify content lengths
    assert len(ls_file.read_text()) == 24, "LS should be 24 aa"
    assert len(b_file.read_text()) == 30, "B should be 30 aa"
    assert len(c_file.read_text()) == 35, "C should be 35 aa"
    assert len(a_file.read_text()) == 21, "A should be 21 aa"
