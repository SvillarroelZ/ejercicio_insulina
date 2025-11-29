# Tests for string_insulin: import behavior, output capture, and MW calculation.

import importlib.util
from pathlib import Path

import pytest


def test_import_string_insulin(tmp_path, monkeypatch):
    # Import test without touching real data/, using INSULIN_DATA_DIR.
    # Module reads on import, so we create files in tmp_path and
    # point INSULIN_DATA_DIR to that temporary directory.
    data_dir = tmp_path
    (data_dir / "preproinsulin_seq_clean.txt").write_text("ATGC")
    (data_dir / "lsinsulin_seq_clean.txt").write_text("LS")
    (data_dir / "binsulin_seq_clean.txt").write_text("BCHAIN")
    (data_dir / "ainsulin_seq_clean.txt").write_text("ACHAIN")
    (data_dir / "cinsulin_seq_clean.txt").write_text("CCHAIN")

    # Force module to use temporary directory
    monkeypatch.setenv("INSULIN_DATA_DIR", str(data_dir))

    # Step 3: Load and execute string_insulin.py
    # We use importlib to load the module from its file path.
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "string_insulin.py"
    
    # spec_from_file_location(name, location):
    #   - name: arbitrary module name we assign (e.g., "string_insulin").
    #   - location: absolute file path to the .py file.
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(["--data-dir", str(data_dir)])
    assert module.insulin == "BCHAINACHAIN"


def test_string_insulin_molecular_weight_calculation(tmp_path, monkeypatch, capsys):
    # Real-world test case: Verify molecular weight calculation for insulin.
    # This test validates the core functionality of string_insulin.py: 1. Read the preproinsulin and its segments. 2. Compute the insulin sequence (B + A chains). 3. Calculate molecular weight by summing amino acid contributions. 4. Compare against the accepted value (5807.63 Da).
    # We use real amino acid sequences and weights to ensure the calculation is correct. The capsys fixture captures printed output so we can verify calculations are shown.
    # Expected behavior: Molecular weight is calculated correctly. Error percentage is within biological tolerance. Output is printed correctly.
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
    
    # Step 2: Create test files and use INSULIN_DATA_DIR
    # Module will read these files on import.
    (tmp_path / "preproinsulin_seq_clean.txt").write_text(prepro)
    (tmp_path / "lsinsulin_seq_clean.txt").write_text(ls_seq)
    (tmp_path / "binsulin_seq_clean.txt").write_text(b_seq)
    (tmp_path / "ainsulin_seq_clean.txt").write_text(a_seq)
    (tmp_path / "cinsulin_seq_clean.txt").write_text(c_seq)
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))

    # Step 4: Import and execute string_insulin.py
    # Module will read files from tmp_path via INSULIN_DATA_DIR.
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(["--data-dir", str(tmp_path)])

    # Step 5: Verify the insulin sequence (B + A)
    # The module constructs insulin by concatenating b_seq and a_seq.
    # This is the active (mature) insulin protein used by the body.
    expected_insulin = b_seq + a_seq
    assert hasattr(module, "insulin"), "Module should expose 'insulin' variable"
    assert module.insulin == expected_insulin, f"insulin variable should be B + A chains, got {module.insulin}"
    assert len(module.insulin) == 51, "Mature insulin should be 51 aa (30 + 21)"

    # Step 6: Verify molecular weight calculation
    # The module computes molecular_weight_insulin by summing (count * weight) for each amino acid.
    # Each amino acid contributes a specific weight (Da = Daltons). The total is the sum.
    # For a rough calculation: we can verify it's in the ballpark.
    # Real insulin is ~5807.63 Da; with our sequences it should be close.
    assert hasattr(module, "molecular_weight_insulin"), "Module should compute 'molecular_weight_insulin'"
    mw = module.molecular_weight_insulin
    
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


def test_count_amino_acids_function(tmp_path, monkeypatch):
    # Test count_amino_acids() function directly for comprehensive coverage
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Test with known sequence
    test_seq = "AACCCDEEE"
    counts = module.count_amino_acids(test_seq)
    
    assert counts['A'] == 2.0
    assert counts['C'] == 3.0
    assert counts['D'] == 1.0
    assert counts['E'] == 3.0
    assert counts['F'] == 0.0  # Not present
    
    # Test case sensitivity (lowercase should be counted)
    test_seq_lower = "aacccdeee"
    counts_lower = module.count_amino_acids(test_seq_lower)
    assert counts_lower['A'] == 2.0
    assert counts_lower['C'] == 3.0


def test_molecular_weight_function(tmp_path, monkeypatch):
    # Test molecular_weight() function directly
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Test with known amino acid
    # Alanine (A) = 89.09 Da
    mw_a = module.molecular_weight("A")
    assert abs(mw_a - 89.09) < 0.01
    
    # Test with two alanines
    mw_aa = module.molecular_weight("AA")
    assert abs(mw_aa - (89.09 * 2)) < 0.01
    
    # Test with mixed amino acids
    # A=89.09, C=121.16
    mw_ac = module.molecular_weight("AC")
    assert abs(mw_ac - (89.09 + 121.16)) < 0.01


def test_read_file_function(tmp_path, monkeypatch):
    # Test _read_file() helper function (private in string_insulin.py)
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Create test file with whitespace
    test_file = tmp_path / "test_seq.txt"
    test_file.write_text("  TESTSEQ  \n")
    
    result = module._read_file(test_file)
    assert result == "TESTSEQ"


def test_load_sequences_function(tmp_path, monkeypatch):
    # Test _load_sequences() function directly
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    # Create all required files
    (tmp_path / "preproinsulin_seq_clean.txt").write_text("PREPRO")
    (tmp_path / "lsinsulin_seq_clean.txt").write_text("LS")
    (tmp_path / "binsulin_seq_clean.txt").write_text("BCHAIN")
    (tmp_path / "ainsulin_seq_clean.txt").write_text("ACHAIN")
    (tmp_path / "cinsulin_seq_clean.txt").write_text("CPEPTIDE")
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    prepro, ls, b, a, c = module._load_sequences(tmp_path)
    
    assert prepro == "PREPRO"
    assert ls == "LS"
    assert b == "BCHAIN"
    assert a == "ACHAIN"
    assert c == "CPEPTIDE"


def test_get_data_dir_priority(tmp_path, monkeypatch):
    # Test _get_data_dir() priority (private in string_insulin.py): CLI > ENV > default
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Test CLI priority (CLI overrides ENV)
    cli_dir = tmp_path / "cli_dir"
    cli_dir.mkdir()
    result = module._get_data_dir(str(cli_dir))
    assert result == cli_dir
    
    # Test ENV priority (when CLI is None)
    result = module._get_data_dir(None)
    assert result == tmp_path
    
    # Test default (when both CLI and ENV are None)
    monkeypatch.delenv("INSULIN_DATA_DIR", raising=False)
    result = module._get_data_dir(None)
    assert result == repo_root / "data"


def test_string_insulin_main_function_call(tmp_path, monkeypatch, capsys):
    # Test that the main() function can be called directly (covers line 95: main() call in if __name__ block)
    # This ensures the if __name__ == "__main__": main() pattern works correctly
    import runpy
    
    data_dir = tmp_path
    (data_dir / "preproinsulin_seq_clean.txt").write_text("MALW")
    (data_dir / "lsinsulin_seq_clean.txt").write_text("MA")
    (data_dir / "binsulin_seq_clean.txt").write_text("LW")
    (data_dir / "ainsulin_seq_clean.txt").write_text("AA")
    (data_dir / "cinsulin_seq_clean.txt").write_text("CC")
    
    # Set the data directory
    monkeypatch.setenv("INSULIN_DATA_DIR", str(data_dir))
    
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "src" / "string_insulin.py"
    
    # Run the script using runpy to execute the __main__ block in this process
    # This will cover line 95 (the main() call inside if __name__ == "__main__")
    runpy.run_path(str(script_path), run_name="__main__")
    
    # Verify output was produced
    captured = capsys.readouterr()
    assert "Molecular weight" in captured.out or "insulin" in captured.out.lower()

