"""
Tests for __main__ execution blocks in the insulin processing scripts.

These tests ensure that when modules are executed as scripts (e.g., `python cleaner.py`),
they execute correctly. This covers the `if __name__ == "__main__":` blocks which are
typically not executed during normal imports.

We use runpy.run_path() to execute the scripts, which allows coverage to track execution.
"""

import runpy
import sys
from pathlib import Path

import pytest


def test_cleaner_main_block_executes(tmp_path, monkeypatch):
    """
    Test that cleaner.py can be executed as a script via its __main__ block.
    
    This verifies the `if __name__ == "__main__":` block in cleaner.py works.
    We create a temporary input file and run cleaner.py as a script using runpy.
    """
    repo_root = Path(__file__).resolve().parents[1]
    
    # Create a temporary input file with ORIGIN format
    input_content = "ORIGIN\n1 malwmrllpl lallalwgpd paaa\n//\n"
    input_file = tmp_path / "preproinsulin_seq.txt"
    output_file = tmp_path / "preproinsulin_seq_clean.txt"
    input_file.write_text(input_content)
    
    # Change to tmp_path so the script finds the input file
    monkeypatch.chdir(tmp_path)
    
    # Run cleaner.py as a script using runpy (this executes __main__ block)
    # runpy.run_path executes the file and coverage tracks it
    runpy.run_path(str(repo_root / "cleaner.py"), run_name="__main__")
    
    # Verify output file was created
    assert output_file.exists(), "Output file should be created by __main__ block"
    
    # Verify content is cleaned correctly
    cleaned = output_file.read_text().strip()
    assert cleaned == "malwmrllpllallalwgpdpaaa", f"Expected cleaned sequence, got {cleaned}"


def test_split_insulin_main_block_executes(tmp_path, monkeypatch):
    """
    Test that split_insulin.py can be executed as a script via its __main__ block.
    
    This verifies the `if __name__ == "__main__":` block in split_insulin.py works.
    We create a 110 aa input file and run split_insulin.py as a script.
    """
    repo_root = Path(__file__).resolve().parents[1]
    
    # Create a 110 amino acid input file
    seq_110 = (
        "malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
        "reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
    )
    input_file = tmp_path / "preproinsulin_seq_clean.txt"
    input_file.write_text(seq_110)
    
    # Change to tmp_path so the script finds the input file
    monkeypatch.chdir(tmp_path)
    
    # Run split_insulin.py as a script using runpy
    runpy.run_path(str(repo_root / "split_insulin.py"), run_name="__main__")
    
    # Verify the four output files were created
    assert (tmp_path / "lsinsulin_seq_clean.txt").exists(), "LS file should be created"
    assert (tmp_path / "binsulin_seq_clean.txt").exists(), "B file should be created"
    assert (tmp_path / "cinsulin_seq_clean.txt").exists(), "C file should be created"
    assert (tmp_path / "ainsulin_seq_clean.txt").exists(), "A file should be created"
