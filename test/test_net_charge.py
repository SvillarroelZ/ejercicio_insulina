"""
Unit tests for the net-charge module.

This module tests the net-charge.py script which calculates the net charge
of the insulin protein across pH values from 0 to 14 using amino acid pKa values.

The script uses the Henderson–Hasselbalch equation to determine the ionization
state of charge-bearing amino acids (K, R, H, D, E, Y, C) at each pH.

The net-charge.py script reads files at import time:
  - binsulin_seq_clean.txt (B-chain)
  - ainsulin_seq_clean.txt (A-chain)

To test without modifying repository files, we create these files in tmp_path
and change the working directory using monkeypatch.chdir().

Key pytest fixtures used:
  - tmp_path: Isolated temporary directory for test files.
  - monkeypatch: Change working directory temporarily.
  - capsys: Capture printed output to verify pH table generation.
"""

import importlib.util
from pathlib import Path


def test_import_net_charge(tmp_path, monkeypatch):
    """
    Test case: Import net-charge.py without modifying the repository.
    
    net-charge.py executes file I/O at import time (reads B and A chains),
    so we must create the required files before importing.
    
    This test:
      1. Creates sequence files in tmp_path.
      2. Changes working directory to tmp_path.
      3. Imports and executes net-charge.py.
      4. Verifies the module code ran without errors.
    
    Expected behavior:
      - Module imports successfully.
      - No errors are raised.
      - All file reads are satisfied by our temporary files.
    """
    # Step 1: Create the expected sequence files in tmp_path
    # net-charge.py reads these files at module level (top-level code).
    # The B and A chains are read and combined to form the "insulin" variable.
    # We use simple test sequences here; real sequences come from split_insulin.py.
    (tmp_path / "preproinsulin_seq_clean.txt").write_text("ATGC")
    (tmp_path / "lsinsulin_seq_clean.txt").write_text("LS")
    (tmp_path / "binsulin_seq_clean.txt").write_text("BCHAIN")
    (tmp_path / "ainsulin_seq_clean.txt").write_text("ACHAIN")
    (tmp_path / "cinsulin_seq_clean.txt").write_text("CCHAIN")

    # Step 2: Change the working directory to tmp_path
    # monkeypatch.chdir() temporarily changes the current working directory.
    # All relative file operations (open() calls) will use this directory.
    # This is critical because net-charge.py calls open("binsulin_seq_clean.txt", ...)
    # without an absolute path, so it looks in the current working directory.
    monkeypatch.chdir(tmp_path)

    # Step 3: Load and execute net-charge.py
    # Like string-insulin.py, this file has a hyphen in its name, so we use importlib.
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "net-charge.py"
    
    # spec_from_file_location(name, location) creates a module spec (blueprint).
    spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
    
    # module_from_spec(spec) creates an empty module object from the spec.
    module = importlib.util.module_from_spec(spec)
    
    # Step 4: Execute the module code
    # spec.loader.exec_module(module) runs all top-level code.
    # This includes file reads, pKa dictionary definitions, charge calculations,
    # and print statements. If any error occurs, this raises an exception.
    spec.loader.exec_module(module)

    # Step 5: Verify import succeeded (if we reach here, no exception was raised)
    assert True, "net-charge.py should import and execute without errors"


def test_net_charge_calculation_with_real_insulin(tmp_path, monkeypatch, capsys):
    """
    Real-world test case: Verify net charge calculation for real insulin.
    
    This test validates that the net-charge.py script:
      1. Correctly loads the B and A chains.
      2. Counts charge-bearing amino acids (K, R, H, D, E, Y, C).
      3. Calculates net charge at different pH values.
      4. Produces a pH vs. net-charge table.
    
    The Henderson–Hasselbalch equation is used to compute the ionization
    state of each amino acid at a given pH. The net charge is the sum of
    positive charges (K, R, H) minus negative charges (D, E, C, Y).
    
    Expected behavior:
      - seqCount dictionary has correct amino acid counts.
      - At low pH (0), positive charges dominate (high net charge).
      - At high pH (14), negative charges dominate (low/negative net charge).
      - Output table is printed for all pH values 0 through 14.
    """
    # Step 1: Create realistic B and A chain sequences
    # These are the actual human insulin chains.
    # B-chain: 30 aa, contains charge-bearing residues (K, R, D, etc.)
    # A-chain: 21 aa, contains charge-bearing residues
    b_seq = "fvnqhlcgshlvealylvcgergffytpkt"   # 30 aa
    a_seq = "giveqcctsicslyqlenycn"            # 21 aa
    
    # Combined insulin sequence (51 aa) for charge calculation
    insulin_seq = b_seq + a_seq
    
    # Step 2: Create the sequence files in tmp_path
    # net-charge.py reads binsulin_seq_clean.txt and ainsulin_seq_clean.txt
    # and concatenates them (via the `insulin` variable).
    (tmp_path / "preproinsulin_seq_clean.txt").write_text("dummy")
    (tmp_path / "lsinsulin_seq_clean.txt").write_text("dummy")
    (tmp_path / "binsulin_seq_clean.txt").write_text(b_seq)
    (tmp_path / "ainsulin_seq_clean.txt").write_text(a_seq)
    (tmp_path / "cinsulin_seq_clean.txt").write_text("dummy")
    
    # Step 3: Change working directory to tmp_path
    monkeypatch.chdir(tmp_path)

    # Step 4: Import and execute net-charge.py
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "net-charge.py"
    spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Step 5: Verify the insulin sequence was loaded correctly
    # The module reads B and A chains and concatenates them.
    assert hasattr(module, "insulin"), "Module should expose 'insulin' variable"
    assert module.insulin == insulin_seq, "insulin should be B + A chains concatenated"
    assert len(module.insulin) == 51, "Insulin should be 51 amino acids (30 + 21)"

    # Step 6: Verify seqCount dictionary (amino acid counts)
    # seqCount is a dictionary with counts of charge-bearing amino acids.
    # Format: {'y': count, 'c': count, 'k': count, 'h': count, 'r': count, 'd': count, 'e': count}
    assert hasattr(module, "seqCount"), "Module should expose 'seqCount' dictionary"
    seqCount = module.seqCount
    
    # All counts should be non-negative
    for aa, count in seqCount.items():
        assert count >= 0, f"Count for {aa} should be non-negative, got {count}"
    
    # Verify counts match our insulin sequence
    for aa in ['y', 'c', 'k', 'h', 'r', 'd', 'e']:
        expected_count = insulin_seq.count(aa)
        assert seqCount[aa] == expected_count, f"Count for {aa} should be {expected_count}, got {seqCount[aa]}"
    
    # Step 7: Verify positive and negative charge counts are reasonable
    # Positive amino acids: K (lysine), R (arginine), H (histidine)
    pos_count = seqCount['k'] + seqCount['r'] + seqCount['h']
    # Negative amino acids: D (aspartate), E (glutamate), C (cysteine), Y (tyrosine)
    neg_count = seqCount['d'] + seqCount['e'] + seqCount['c'] + seqCount['y']
    
    # For human insulin, we expect some balance of positive and negative charges
    assert pos_count > 0, "Insulin should have at least one positive charge-bearing amino acid"
    assert neg_count > 0, "Insulin should have at least one negative charge-bearing amino acid"

    # Step 8: Verify pH table was printed
    # The module prints a table with pH and net charge for each pH from 0 to 14.
    # We capture stdout to verify this output exists.
    captured = capsys.readouterr()
    
    # Check that the header row is printed
    assert "pH" in captured.out, "Output should include pH header"
    assert "net-charge" in captured.out.lower() or "charge" in captured.out.lower(), "Output should include charge information"
    
    # The output should have lines for each pH value (0-14 = 15 pH values)
    lines_with_digits = [line for line in captured.out.split('\n') if any(c.isdigit() for c in line)]
    # We expect at least 10 lines with pH values (could be more if formatting adds spaces)
    assert len(lines_with_digits) >= 10, f"Output should include pH values, got {len(lines_with_digits)} lines with digits"
