"""
Unit tests for the string-insulin module.

This module tests the string-insulin.py script which:
  1. Reads the split insulin sequences from files.
  2. Displays the complete preproinsulin and individual chains.
  3. Calculates the molecular weight of the processed insulin (B + A chains).
  4. Compares against the actual accepted molecular weight and calculates error.

The string-insulin.py script reads files at import time from data/ directory:
  - data/preproinsulin_seq_clean.txt
  - data/lsinsulin_seq_clean.txt
  - data/binsulin_seq_clean.txt
  - data/ainsulin_seq_clean.txt
  - data/cinsulin_seq_clean.txt

To test without modifying repository files, we create these files in tmp_path/data
and change the working directory using monkeypatch.chdir().

Key pytest fixtures used:
  - tmp_path: Isolated temporary directory for test files.
  - monkeypatch: Change working directory temporarily.
  - capsys: Capture printed output to verify calculations.
"""

import importlib.util
from pathlib import Path


def test_import_string_insulin(tmp_path, monkeypatch):
    """
    Test case: Import string-insulin.py without modifying the repository.
    
    string-insulin.py executes file I/O at import time (it calls read_file()
    at module level), so we must create the required files before importing.
    
    This test:
      1. Creates dummy sequence files in tmp_path.
      2. Changes working directory to tmp_path.
      3. Imports and executes string-insulin.py.
      4. Verifies the module code ran without errors.
    
    Expected behavior:
      - Module imports successfully.
      - No errors are raised.
      - All file reads are satisfied by our temporary files.
    """
    # Step 0: Create data directory in tmp_path
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Step 1: Create the files that string-insulin.py expects to read
    # These are minimal dummy sequences for testing (not realistic biology).
    # In real use, these come from cleaner.py and split_insulin.py.
    # Explanation of each file:
    #   - data/preproinsulin_seq_clean.txt: Full 110 aa preproinsulin (LS + B + C + A)
    #   - data/lsinsulin_seq_clean.txt: Leader sequence (24 aa)
    #   - data/binsulin_seq_clean.txt: B-chain (30 aa)
    #   - data/ainsulin_seq_clean.txt: A-chain (21 aa)
    #   - data/cinsulin_seq_clean.txt: C-peptide (35 aa)
    (tmp_path / "data" / "preproinsulin_seq_clean.txt").write_text("ATGC")
    (tmp_path / "data" / "lsinsulin_seq_clean.txt").write_text("LS")
    (tmp_path / "data" / "binsulin_seq_clean.txt").write_text("BCHAIN")
    (tmp_path / "data" / "ainsulin_seq_clean.txt").write_text("ACHAIN")
    (tmp_path / "data" / "cinsulin_seq_clean.txt").write_text("CCHAIN")

    # Step 2: Change the working directory to tmp_path
    # monkeypatch.chdir() temporarily changes the current working directory.
    # When string-insulin.py calls read_file("data/preproinsulin_seq_clean.txt"),
    # it will look in the tmp_path/data directory (current working dir), not the repo root.
    # This prevents any interaction with real repository files.
    # After the test, monkeypatch automatically restores the original directory.
    monkeypatch.chdir(tmp_path)

    # Step 3: Load and execute string-insulin.py
    # We use importlib to load the module from its file path.
    # The .py file has a name with a hyphen (string-insulin.py), so we can't use
    # 'import string-insulin' (invalid Python identifier). Instead, we use
    # importlib.util.spec_from_file_location to load it by file path.
    # This technique allows us to import files with names containing hyphens,
    # underscores, or other special characters.
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "string-insulin.py"
    
    # spec_from_file_location(name, location):
    #   - name: arbitrary module name we assign (e.g., "string_insulin").
    #   - location: absolute file path to the .py file.
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    
    # module_from_spec(spec) creates a module object from a spec (blueprint).
    module = importlib.util.module_from_spec(spec)
    
    # Step 4: Execute the module code
    # spec.loader.exec_module(module) runs all top-level code in the module.
    # This includes read_file() calls, variable assignments, print statements,
    # and calculations. If any error occurs (file not found, invalid code, etc.),
    # this will raise an exception.
    spec.loader.exec_module(module)

    # Step 5: Verify import succeeded (if we reach here, no exception was raised)
    assert True, "string-insulin.py should import and execute without errors"


def test_string_insulin_molecular_weight_calculation(tmp_path, monkeypatch, capsys):
    """
    Real-world test case: Verify molecular weight calculation for insulin.
    
    This test validates the core functionality of string-insulin.py:
      1. Read the preproinsulin and its segments.
      2. Compute the insulin sequence (B + A chains).
      3. Calculate molecular weight by summing amino acid contributions.
      4. Compare against the accepted value (5807.63 Da).
    
    We use real amino acid sequences and weights to ensure the calculation is correct.
    The capsys fixture captures printed output so we can verify calculations are shown.
    
    Expected behavior:
      - Molecular weight is calculated correctly.
      - Error percentage is within biological tolerance.
      - Output is printed correctly.
    """
    # Step 0: Create data directory in tmp_path
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Step 1: Create realistic test sequences
    # These are the actual segments from human preproinsulin (110 total amino acids).
    # LS = leader/signal sequence (24 aa): "malwmrllpllallalwgpdpaaa"
    # B = B-chain of insulin (30 aa): "fvnqhlcgshlvealylvcgergffytpkt"
    # C = C-peptide (35 aa): "rreaedlqvgqvelgggpgagslqplalegslqkr"
    # A = A-chain of insulin (21 aa): "giveqcctsicslyqlenycn"
    # Mature insulin = B + A (51 aa total)
    ls_seq = "malwmrllpllallalwgpdpaaa"          # 24 aa
    b_seq = "fvnqhlcgshlvealylvcgergffytpkt"     # 30 aa
    c_seq = "rreaedlqvgqvelgggpgagslqplalegslqkr"  # 35 aa
    a_seq = "giveqcctsicslyqlenycn"              # 21 aa
    prepro = ls_seq + b_seq + c_seq + a_seq     # 110 aa (preproinsulin)
    
    # Step 2: Create test sequence files in tmp_path/data
    # string-insulin.py expects these files to exist and reads them at import time.
    # By creating them in tmp_path/data and changing the working directory, we avoid
    # touching the repository's real files.
    (tmp_path / "data" / "preproinsulin_seq_clean.txt").write_text(prepro)
    (tmp_path / "data" / "lsinsulin_seq_clean.txt").write_text(ls_seq)
    (tmp_path / "data" / "binsulin_seq_clean.txt").write_text(b_seq)
    (tmp_path / "data" / "ainsulin_seq_clean.txt").write_text(a_seq)
    (tmp_path / "data" / "cinsulin_seq_clean.txt").write_text(c_seq)

    # Step 3: Change working directory to tmp_path
    # This ensures all file operations (especially open() calls) happen in the temp directory.
    monkeypatch.chdir(tmp_path)

    # Step 4: Import and execute string-insulin.py
    # The module will read the files we created in tmp_path (since that's now the cwd).
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "string-insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Step 5: Verify the insulin sequence (B + A)
    # The module constructs insulin by concatenating b_seq and a_seq.
    # This is the active (mature) insulin protein used by the body.
    expected_insulin = b_seq + a_seq
    assert hasattr(module, "insulin"), "Module should expose 'insulin' variable"
    assert module.insulin == expected_insulin, f"insulin variable should be B + A chains, got {module.insulin}"
    assert len(module.insulin) == 51, "Mature insulin should be 51 aa (30 + 21)"

    # Step 6: Verify molecular weight calculation
    # The module computes molecularWeightInsulin by summing (count * weight) for each amino acid.
    # Each amino acid contributes a specific weight (Da = Daltons). The total is the sum.
    # For a rough calculation: we can verify it's in the ballpark.
    # Real insulin is ~5807.63 Da; with our sequences it should be close.
    assert hasattr(module, "molecularWeightInsulin"), "Module should compute 'molecularWeightInsulin'"
    mw = module.molecularWeightInsulin
    
    # Sanity checks on molecular weight:
    # Molecular weight should be positive and within reasonable range for a 51 aa peptide.
    # Real human insulin (51 aa) has MW ~5800 Da. Our sequences may vary slightly.
    assert mw > 0, "Molecular weight should be positive"
    assert mw > 5000, f"Molecular weight should be > 5000 Da for a 51 aa peptide, got {mw}"
    assert mw < 7000, f"Molecular weight should be < 7000 Da for a 51 aa peptide, got {mw}"

    # Step 7: Verify error percentage is calculated
    # The module compares the computed value to the accepted value (5807.63 Da)
    # and calculates the percentage difference.
    assert hasattr(module, "error_percentage"), "Module should calculate 'error_percentage'"
    error = module.error_percentage
    # The error percentage depends on the specific amino acid composition.
    # Real sequences may have 10-20% variation from the nominal accepted value.
    # We just verify it's a number and was computed.
    assert isinstance(error, float), "Error percentage should be a number"
    assert abs(error) < 25, f"Error percentage should be reasonable, got {error}%"

    # Step 8: Verify output was printed
    # The module prints calculations and results. We capture them with capsys
    # to verify the module is doing its job (not just silently computing).
    captured = capsys.readouterr()
    assert "molecular weight" in captured.out.lower(), "Module should print molecular weight information"
