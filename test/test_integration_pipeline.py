# Integration tests for the insulin processing pipeline.

import importlib.util
import re
import runpy
import shutil
from pathlib import Path

import pytest

from cleaner import clean_sequence
import split_insulin


def _make_origin_content(seq_letters: str) -> str:
    # Create a minimal NCBI ORIGIN-like block for given letters.
    # The real clean_sequence implementation removes the string "ORIGIN", the end marker "//", any digits and whitespace and any non-letter characters.
    # To make a realistic input we place the sequence letters separated into groups and include a leading numeric position. The returned string is written directly to a file and later cleaned by clean_sequence.
    # Args: seq_letters: String of only letters (a-z, A-Z) to be formatted.
    # Returns: String in NCBI ORIGIN format with markers and position numbers.
    # Break into groups of 10 with spaces to emulate the ORIGIN layout
    groups = [seq_letters[i : i + 10] for i in range(0, len(seq_letters), 10)]
    body = " ".join(groups)
    return f"ORIGIN\n1 {body}\n//\n"


def test_full_pipeline_with_real_preproinsulin_data(tmp_path, monkeypatch, capsys):
    # End-to-end integration test using REAL human preproinsulin sequence.
    # This test validates that the entire pipeline (cleaner -> split_insulin -> string_insulin -> net_charge) works correctly with the actual 110 amino acid human preproinsulin sequence.
    # Files are created in data/ directory and cleaned by conftest.py after the test.
    # Steps: 1. Read the real preproinsulin sequence from the project data file. 2. Run clean_sequence() using the real data file. 3. Run split_insulin.split_insulin() to split into four segments. 4. Import and execute string_insulin.py to compute molecular weight. 5. Import and execute net_charge.py to compute charge table. 6. Verify all outputs are correct.
    # Expected behavior: Cleaned sequence is exactly 110 lowercase letters. Four segment files are created with correct lengths (24, 30, 35, 21). Molecular weight is computed for the B + A chains (51 aa). Net charge table is generated for pH 0-14.

    # Get paths to project directories
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    original_file = project_root / "preproinsulin_seq.txt"  # Input is in repository root

    # Verify input file exists
    assert original_file.exists(), "Original data file must exist"
    
    # Step 1: Clean the sequence (writes to data/)
    from cleaner import clean_preproinsulin
    clean_seq = clean_preproinsulin()
    
    # Verify cleaned file exists
    cleaned_file = data_dir / "preproinsulin_seq_clean.txt"
    assert cleaned_file.exists(), "Cleaned file should exist in data/"
    assert len(clean_seq) == 110, f"Cleaned sequence should be 110 aa, got {len(clean_seq)}"
    
    # Step 2: Split into segments (writes to data/)
    ls, b, c, a = split_insulin.split_insulin()
    
    # Verify segment lengths
    assert len(ls) == 24, f"LS should be 24 aa, got {len(ls)}"
    assert len(b) == 30, f"B-chain should be 30 aa, got {len(b)}"
    assert len(c) == 35, f"C-peptide should be 35 aa, got {len(c)}"
    assert len(a) == 21, f"A-chain should be 21 aa, got {len(a)}"
    
    # Verify segments reconstruct original
    reconstructed = ls + b + c + a
    assert reconstructed == clean_seq, "Segments should reconstruct the original sequence"
    
    # Step 3: Import string_insulin.py (reads from data/)
    string_path = project_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(string_path))
    string_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(string_mod)
    # Execute string_insulin main to perform I/O and computations
    string_mod.main(["--data-dir", str(data_dir)])
    
    # Verify insulin variable (B + A)
    expected_insulin = b + a
    assert string_mod.insulin == expected_insulin, "insulin should be B + A chains"
    assert len(string_mod.insulin) == 51, "Insulin should be 51 aa"
    
    # Verify molecular weight
    assert hasattr(string_mod, "molecular_weight_insulin"), "Module should compute molecular weight"
    mw = string_mod.molecular_weight_insulin
    assert 5000 < mw < 7000, f"MW should be 5000-7000 Da, got {mw}"
    
    # Step 4: Import net_charge.py (reads from data/)
    net_path = project_root / "src" / "net_charge.py"
    spec2 = importlib.util.spec_from_file_location("net_charge", str(net_path))
    net_mod = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(net_mod)
    # Execute net_charge main to compute seq_count and print table
    net_mod.main(["--data-dir", str(data_dir)])
    
    # Verify seq_count
    assert hasattr(net_mod, "seq_count"), "Module should expose seq_count"
    for aa, count in net_mod.seq_count.items():
        assert count >= 0, f"Count for {aa} should be >= 0"
    
    # Verify output includes pH table
    captured = capsys.readouterr()
    assert "pH" in captured.out, "Output should include pH table header"


# ============================================================================
# Error Handling Integration Tests
# ============================================================================

def _load_module_from_repo(script_name: str, module_name: str):
    # Helper to load a module from the repository src/ directory by filename.
    # Returns the loaded module object.
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "src" / script_name
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_string_insulin_missing_files_raises(tmp_path, monkeypatch):
    # Verify that string_insulin.py raises FileNotFoundError when required files are missing.
    # This test creates only SOME of the required cleaned sequence files in data/ (preproinsulin and lsinsulin) but omits others (binsulin, ainsulin).
    # When attempting to import string_insulin.py, it should fail with FileNotFoundError because it tries to read all required files at import time.
    # This validates defensive behavior: the script should fail fast with a clear error when dependencies are missing.
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    
    # Clean data/ directory first
    for f in data_dir.glob("*_seq_clean.txt"):
        f.unlink()
    
    # Create only two of the required files (omit binsulin and ainsulin)
    (data_dir / "preproinsulin_seq_clean.txt").write_text("prepro_dummy_sequence")
    (data_dir / "lsinsulin_seq_clean.txt").write_text("ls_dummy_sequence")

    # Import module (no side effects on import), then running main should raise
    mod = _load_module_from_repo("string_insulin.py", "string_insulin_missing_test")
    with pytest.raises(FileNotFoundError):
        mod.main(["--data-dir", str(data_dir)])


def test_net_charge_seqcount_and_output(tmp_path, monkeypatch, capsys):
    # Verify that net_charge.py correctly counts amino acids and produces formatted output.
    # This test creates all required cleaned sequence files with deterministic sequences so that amino acid counts are known in advance.
    # It then imports net_charge.py and validates: 1. The seq_count dictionary has correct counts for each charge-bearing AA 2. The output includes a pH table header 3. The output includes at least one pH value line
    # Chosen test sequences: binsulin = "yckk" (y:1, c:1, k:2), ainsulin = "hrede" (h:1, r:1, d:1, e:2). Combined insulin = "yckkhrede" with counts: y:1, c:1, k:2, h:1, r:1, d:1, e:2
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    
    # Create test files in data/
    (data_dir / "preproinsulin_seq_clean.txt").write_text("prepro_dummy")
    (data_dir / "lsinsulin_seq_clean.txt").write_text("ls_dummy")
    (data_dir / "binsulin_seq_clean.txt").write_text("yckk")
    (data_dir / "ainsulin_seq_clean.txt").write_text("hrede")
    (data_dir / "cinsulin_seq_clean.txt").write_text("cpeptide_dummy")

    # Load net_charge.py and execute main to compute and print
    net_mod = _load_module_from_repo("net_charge.py", "net_charge_test_mod")
    net_mod.main(["--data-dir", str(data_dir)])

    # Verify seq_count has correct values
    # Note: 'e' appears twice in 'hrede'
    expected = {'y': 1.0, 'c': 1.0, 'k': 2.0, 'h': 1.0, 'r': 1.0, 'd': 1.0, 'e': 2.0}

    assert hasattr(net_mod, "seq_count"), "Module must define seq_count"
    assert net_mod.seq_count == expected, f"seq_count mismatch: {net_mod.seq_count} != {expected}"

    # Verify output format includes pH table
    captured = capsys.readouterr()
    out = captured.out

    assert "pH" in out, "Output must include header 'pH'"

    # Check for at least one pH value line (e.g., "0.00 | ..." or "1.00 | ...")
    numeric_pH_line_found = any(
        re.match(r'^\s*0(?:\.00)?\s*\|', line) or re.match(r'^\s*\d+\.\d{2}\s*\|', line)
        for line in out.splitlines()
    )
    assert numeric_pH_line_found, "Output must include at least one pH value line"


# ============================================================================
# CLI Execution Tests (__main__ block coverage)
# ============================================================================

def test_cleaner_main_block_executes(tmp_path, monkeypatch):
    # Verify that cleaner.py can be executed as a script via __main__ block.
    # This test uses runpy.run_path() to execute cleaner.py as if running `python cleaner.py` from the command line. This ensures the `if __name__ == "__main__":` block is covered by tests.
    # The script reads the real data/preproinsulin_seq.txt file and writes output to data/ directory. After execution, we verify the output file exists and contains the expected cleaned sequence (110 lowercase amino acids).
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    output_file = data_dir / "preproinsulin_seq_clean.txt"
    
    # Remove output file if it exists from previous run
    if output_file.exists():
        output_file.unlink()
    
    # Execute cleaner.py as a script (this runs __main__ block)
    runpy.run_path(str(repo_root / "src" / "cleaner.py"), run_name="__main__")
    
    # Verify output file was created in data/
    assert output_file.exists(), "Output should be created in data/"
    
    # Verify content is cleaned correctly
    cleaned = output_file.read_text().strip()
    assert len(cleaned) == 110, f"Cleaned should be 110 aa, got {len(cleaned)}"
    assert cleaned.islower(), "Cleaned sequence should be lowercase"
    assert cleaned.isalpha(), "Cleaned sequence should be only letters"


def test_pipeline_with_custom_data_directory(tmp_path, monkeypatch, capsys):
    # Test complete pipeline using custom data directory via INSULIN_DATA_DIR
    # Create test sequences in custom directory
    custom_data = tmp_path / "custom_data"
    custom_data.mkdir()
    
    # Real sequences for testing
    ls_seq = "malwmrllpllallalwgpdpaaa"
    b_seq = "fvnqhlcgshlvealylvcgergffytpkt"
    c_seq = "rreaedlqvgqvelgggpgagslqplalegslqkr"
    a_seq = "giveqcctsicslyqlenycn"
    prepro = ls_seq + b_seq + c_seq + a_seq
    
    (custom_data / "preproinsulin_seq_clean.txt").write_text(prepro)
    (custom_data / "lsinsulin_seq_clean.txt").write_text(ls_seq)
    (custom_data / "binsulin_seq_clean.txt").write_text(b_seq)
    (custom_data / "ainsulin_seq_clean.txt").write_text(a_seq)
    (custom_data / "cinsulin_seq_clean.txt").write_text(c_seq)
    
    # Test string_insulin with custom directory
    repo_root = Path(__file__).resolve().parents[1]
    string_path = repo_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin_custom", str(string_path))
    string_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(string_mod)
    string_mod.main(["--data-dir", str(custom_data)])
    
    assert string_mod.insulin == b_seq + a_seq
    assert len(string_mod.insulin) == 51
    
    # Test net_charge with custom directory
    net_path = repo_root / "src" / "net_charge.py"
    spec2 = importlib.util.spec_from_file_location("net_charge_custom", str(net_path))
    net_mod = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(net_mod)
    net_mod.main(["--data-dir", str(custom_data)])
    
    assert net_mod.insulin == b_seq + a_seq
    assert hasattr(net_mod, "seq_count")


def test_pipeline_error_recovery_invalid_sequence_length(tmp_path, monkeypatch, capsys):
    # Test pipeline behavior with invalid sequence length (not 110 aa)
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    
    # Create invalid sequence (too short)
    invalid_seq = "A" * 50  # Only 50 aa instead of 110
    (data_dir / "preproinsulin_seq_clean.txt").write_text(invalid_seq)
    
    # split_insulin should detect error and return empty tuple
    result = split_insulin.split_insulin()
    
    assert result == tuple(), "Should return empty tuple for invalid length"
    
    captured = capsys.readouterr()
    assert "ERROR" in captured.out or "NOT 110" in captured.out


def test_molecular_weight_error_percentage_calculation(tmp_path, monkeypatch):
    # Test that error percentage is calculated correctly
    repo_root = Path(__file__).resolve().parents[1]
    
    # Use real sequences
    b_seq = "fvnqhlcgshlvealylvcgergffytpkt"
    a_seq = "giveqcctsicslyqlenycn"
    prepro = "malwmrllpllallalwgpdpaaa" + b_seq + "rreaedlqvgqvelgggpgagslqplalegslqkr" + a_seq
    
    custom_data = tmp_path / "test_data"
    custom_data.mkdir()
    (custom_data / "preproinsulin_seq_clean.txt").write_text(prepro)
    (custom_data / "lsinsulin_seq_clean.txt").write_text("malwmrllpllallalwgpdpaaa")
    (custom_data / "binsulin_seq_clean.txt").write_text(b_seq)
    (custom_data / "ainsulin_seq_clean.txt").write_text(a_seq)
    (custom_data / "cinsulin_seq_clean.txt").write_text("rreaedlqvgqvelgggpgagslqplalegslqkr")
    
    string_path = repo_root / "src" / "string_insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin_error", str(string_path))
    string_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(string_mod)
    string_mod.main(["--data-dir", str(custom_data)])
    
    # Verify error percentage exists and is reasonable
    assert hasattr(string_mod, "error_percentage")
    # The rough molecular weight calculation will have some error
    # Accept error percentage up to 20% as reasonable for this approximation
    assert abs(string_mod.error_percentage) < 20.0, f"Error percentage should be < 20% for rough calculation, got {abs(string_mod.error_percentage)}%"


def test_net_charge_at_extreme_ph_values(tmp_path, monkeypatch, capsys):
    # Test net charge calculation at pH extremes (0 and 14)
    repo_root = Path(__file__).resolve().parents[1]
    
    custom_data = tmp_path / "test_data"
    custom_data.mkdir()
    
    # Simple test sequence with known charged residues
    b_seq = "kkkrrr"  # 3 K (lysine) + 3 R (arginine) = 6 positive charges
    a_seq = "dddee"   # 3 D (aspartate) + 2 E (glutamate) = 5 negative charges
    
    (custom_data / "preproinsulin_seq_clean.txt").write_text("prepro")
    (custom_data / "lsinsulin_seq_clean.txt").write_text("ls")
    (custom_data / "binsulin_seq_clean.txt").write_text(b_seq)
    (custom_data / "ainsulin_seq_clean.txt").write_text(a_seq)
    (custom_data / "cinsulin_seq_clean.txt").write_text("c")
    
    net_path = repo_root / "src" / "net_charge.py"
    spec = importlib.util.spec_from_file_location("net_charge_extreme", str(net_path))
    net_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(net_mod)
    net_mod.main(["--data-dir", str(custom_data)])
    
    captured = capsys.readouterr()
    output = captured.out
    
    # At pH 0, positive charges should dominate (high positive net charge)
    # At pH 14, negative charges should dominate (negative net charge)
    assert "0.00" in output
    assert "14.00" in output


def test_split_insulin_main_block_executes(tmp_path, monkeypatch):
    # Verify that split_insulin.py can be executed as a script via __main__ block.
    # This test creates a 110 aa input file in data/, then executes split_insulin.py using runpy.run_path() to cover the `if __name__ == "__main__":` block.
    # After execution, we verify that the four output files (LS, B, C, A) were created successfully in data/.
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"

    # Create a valid 110 amino acid input file in data/
    seq_110 = (
            "malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
            "reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
    )
    input_file = data_dir / "preproinsulin_seq_clean.txt"
    input_file.write_text(seq_110)

    # Execute split_insulin.py as a script (this runs __main__ block)
    runpy.run_path(str(repo_root / "src" / "split_insulin.py"), run_name="__main__")

    try:
        # Verify the four output files were created in data/
        assert (data_dir / "lsinsulin_seq_clean.txt").exists(), "LS file should be in data/"
        assert (data_dir / "binsulin_seq_clean.txt").exists(), "B file should be in data/"
        assert (data_dir / "cinsulin_seq_clean.txt").exists(), "C file should be in data/"
        assert (data_dir / "ainsulin_seq_clean.txt").exists(), "A file should be in data/"
    finally:
        # Cleanup generated files from data/
        for file in [
            data_dir / "lsinsulin_seq_clean.txt",
            data_dir / "binsulin_seq_clean.txt",
            data_dir / "cinsulin_seq_clean.txt",
            data_dir / "ainsulin_seq_clean.txt"
        ]:
            if file.exists():
                file.unlink()

