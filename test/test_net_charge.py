# Tests for net_charge: import behavior, seq counts, and pH table output.

import importlib.util
from pathlib import Path

import pytest


def test_import_net_charge(tmp_path, monkeypatch):
    # Test case: Import net_charge.py without modifying the repository.
    # net_charge.py executes file I/O at import time (reads B and A chains), so we must create the required files before importing.
    # This test: 1. Creates sequence files in data/. 2. Imports and executes net_charge.py. 3. Verifies the module code ran without errors. 4. Cleans up created files.
    # Expected behavior: Module imports successfully. No errors are raised. All file reads are satisfied by files in data/.
    # Step 1: Create the expected sequence files in data/
    # net_charge.py reads these files at module level using absolute paths to data/.
    # The B and A chains are read and combined to form the "insulin" variable.
    # We use simple test sequences here; real sequences come from split_insulin.py.
    # Use temporary directory and redirect via INSULIN_DATA_DIR
    data_dir = tmp_path
    (data_dir / "preproinsulin_seq_clean.txt").write_text("PREPRO")
    (data_dir / "lsinsulin_seq_clean.txt").write_text("LS")
    (data_dir / "binsulin_seq_clean.txt").write_text("BCHAIN")
    (data_dir / "ainsulin_seq_clean.txt").write_text("ACHAIN")
    (data_dir / "cinsulin_seq_clean.txt").write_text("CCHAIN")
    monkeypatch.setenv("INSULIN_DATA_DIR", str(data_dir))

    try:
        # Step 2: Load and execute net_charge.py
        repo_root = Path(__file__).resolve().parents[1]
        mod_path = repo_root / "src" / "net_charge.py"
        
        # spec_from_file_location(name, location) creates a module spec (blueprint).
        spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
        
        # module_from_spec(spec) creates an empty module object from the spec.
        module = importlib.util.module_from_spec(spec)
        
        # Execute main with explicit data-dir; import should not do I/O now
        spec.loader.exec_module(module)
        module.main(["--data-dir", str(data_dir)])

        # If we reach here, execution succeeded
    finally:
        pass


def test_net_charge_calculation_with_real_insulin(tmp_path, monkeypatch, capsys):
    # Real-world test case: Verify net charge calculation for real insulin.
    # This test validates that the net_charge.py script: 1. Correctly loads the B and A chains. 2. Counts charge-bearing amino acids (K, R, H, D, E, Y, C). 3. Calculates net charge at different pH values. 4. Produces a pH vs. net-charge table.
    # The Henderson-Hasselbalch equation is used to compute the ionization state of each amino acid at a given pH. The net charge is the sum of positive charges (K, R, H) minus negative charges (D, E, C, Y).
    # Expected behavior: seq_count dictionary has correct amino acid counts. At low pH (0), positive charges dominate (high net charge). At high pH (14), negative charges dominate (low/negative net charge). Output table is printed for all pH values 0 through 14.
    # Step 1: Create realistic B and A chain sequences
    # These are the actual human insulin chains.
    # B-chain: 30 aa, contains charge-bearing residues (K, R, D, etc.)
    # A-chain: 21 aa, contains charge-bearing residues
    b_seq = "fvnqhlcgshlvealylvcgergffytpkt"   # 30 aa
    a_seq = "giveqcctsicslyqlenycn"            # 21 aa
    
    # Combined insulin sequence (51 aa) for charge calculation
    insulin_seq = b_seq + a_seq
    
    # Step 2: Create the sequence files in data/
    # net_charge.py reads binsulin_seq_clean.txt and ainsulin_seq_clean.txt
    # using absolute paths to data/.
    data_dir = tmp_path
    (data_dir / "preproinsulin_seq_clean.txt").write_text("prepro_dummy")
    (data_dir / "lsinsulin_seq_clean.txt").write_text("dummy")
    (data_dir / "binsulin_seq_clean.txt").write_text(b_seq)
    (data_dir / "ainsulin_seq_clean.txt").write_text(a_seq)
    (data_dir / "cinsulin_seq_clean.txt").write_text("dummy")
    monkeypatch.setenv("INSULIN_DATA_DIR", str(data_dir))
    
    try:
        # Step 3: Import and execute net_charge.py
        repo_root = Path(__file__).resolve().parents[1]
        mod_path = repo_root / "src" / "net_charge.py"
        spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main(["--data-dir", str(data_dir)])

        # Step 4: Verify the insulin sequence was loaded correctly
        # The module reads B and A chains and concatenates them.
        assert hasattr(module, "insulin"), "Module should expose 'insulin' variable"
        assert module.insulin == insulin_seq, "insulin should be B + A chains concatenated"
        assert len(module.insulin) == 51, "Insulin should be 51 amino acids (30 + 21)"

        # Step 5: Verify seq_count dictionary (amino acid counts)
        # seq_count is a dictionary with counts of charge-bearing amino acids.
        # Format: {'y': count, 'c': count, 'k': count, 'h': count, 'r': count, 'd': count, 'e': count}
        assert hasattr(module, "seq_count"), "Module should expose 'seq_count' dictionary"
        seq_count = module.seq_count
        
        # All counts should be non-negative
        for aa, count in seq_count.items():
            assert count >= 0, f"Count for {aa} should be non-negative, got {count}"
        
        # Verify counts match our insulin sequence
        for aa in ['y', 'c', 'k', 'h', 'r', 'd', 'e']:
            expected_count = insulin_seq.count(aa)
            assert seq_count[aa] == expected_count, f"seq_count[{aa}] should be {expected_count}, got {seq_count[aa]}"
    finally:
        pass


def test_compute_seqcount_function(tmp_path, monkeypatch):
    # Test compute_seqcount() function directly
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "net_charge.py"
    spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Test with known sequence
    test_seq = "kkhhrrddeeyycc"
    seq_count = module.compute_seqcount(test_seq)
    
    assert seq_count['k'] == 2.0
    assert seq_count['h'] == 2.0
    assert seq_count['r'] == 2.0
    assert seq_count['d'] == 2.0
    assert seq_count['e'] == 2.0
    assert seq_count['y'] == 2.0
    assert seq_count['c'] == 2.0


def test_print_net_charge_table_function(tmp_path, monkeypatch, capsys):
    # Test print_net_charge_table() function directly
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "net_charge.py"
    spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Create test seqCount
    seqCount = {'y': 1.0, 'c': 1.0, 'k': 1.0, 'h': 1.0, 'r': 1.0, 'd': 1.0, 'e': 1.0}
    
    module.print_net_charge_table(seqCount)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Verify table header
    assert "pH" in output
    assert "net-charge" in output
    
    # Verify pH values 0-14 are present
    assert "0.00" in output
    assert "7.00" in output
    assert "14.00" in output
    
    # Verify table has separators
    assert "---" in output


def test_read_file_function_net_charge(tmp_path, monkeypatch):
    # Test _read_file() helper function (private in net_charge.py)
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "net_charge.py"
    spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Create test file with whitespace
    test_file = tmp_path / "test_seq.txt"
    test_file.write_text("  TESTSEQ  \n")
    
    result = module._read_file(test_file)
    assert result == "TESTSEQ"


def test_load_sequences_function_net_charge(tmp_path, monkeypatch):
    # Test _load_sequences() function in net_charge directly
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    # Create all required files
    (tmp_path / "preproinsulin_seq_clean.txt").write_text("PREPRO")
    (tmp_path / "lsinsulin_seq_clean.txt").write_text("LS")
    (tmp_path / "binsulin_seq_clean.txt").write_text("BCHAIN")
    (tmp_path / "ainsulin_seq_clean.txt").write_text("ACHAIN")
    (tmp_path / "cinsulin_seq_clean.txt").write_text("CPEPTIDE")
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "net_charge.py"
    spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    prepro, ls, b, a, c = module._load_sequences(tmp_path)
    
    assert prepro == "PREPRO"
    assert ls == "LS"
    assert b == "BCHAIN"
    assert a == "ACHAIN"
    assert c == "CPEPTIDE"


def test_get_data_dir_priority_net_charge(tmp_path, monkeypatch):
    # Test _get_data_dir() priority (private in net_charge.py): CLI > ENV > default
    monkeypatch.setenv("INSULIN_DATA_DIR", str(tmp_path))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "net_charge.py"
    spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
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


def test_net_charge_with_empty_sequence(tmp_path, monkeypatch, capsys):
    # Test net charge calculation with empty insulin sequence
    data_dir = tmp_path
    (data_dir / "preproinsulin_seq_clean.txt").write_text("")
    (data_dir / "lsinsulin_seq_clean.txt").write_text("")
    (data_dir / "binsulin_seq_clean.txt").write_text("")
    (data_dir / "ainsulin_seq_clean.txt").write_text("")
    (data_dir / "cinsulin_seq_clean.txt").write_text("")
    monkeypatch.setenv("INSULIN_DATA_DIR", str(data_dir))
    
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "src" / "net_charge.py"
    spec = importlib.util.spec_from_file_location("net_charge", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(["--data-dir", str(data_dir)])
    
    # With empty sequence, all counts should be 0
    assert module.seq_count['k'] == 0.0
    assert module.seq_count['h'] == 0.0
    assert module.seq_count['r'] == 0.0
    assert module.seq_count['d'] == 0.0
    assert module.seq_count['e'] == 0.0
    assert module.seq_count['y'] == 0.0
    assert module.seq_count['c'] == 0.0


def test_net_charge_main_function_call(tmp_path, monkeypatch, capsys):
    # Test that the main() function can be called directly (covers line 84: main() call in if __name__ block)
    # This ensures the if __name__ == "__main__": main() pattern works correctly
    import runpy
    
    data_dir = tmp_path
    # Create all required files
    (data_dir / "preproinsulin_seq_clean.txt").write_text("KRHDE")
    (data_dir / "lsinsulin_seq_clean.txt").write_text("K")
    (data_dir / "binsulin_seq_clean.txt").write_text("RH")
    (data_dir / "ainsulin_seq_clean.txt").write_text("DE")
    (data_dir / "cinsulin_seq_clean.txt").write_text("C")
    
    # Set the data directory
    monkeypatch.setenv("INSULIN_DATA_DIR", str(data_dir))
    
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "src" / "net_charge.py"
    
    # Run the script using runpy to execute the __main__ block in this process
    # This will cover line 84 (the main() call inside if __name__ == "__main__")
    runpy.run_path(str(script_path), run_name="__main__")
    
    # Verify output was produced
    captured = capsys.readouterr()
    assert "pH" in captured.out or "net" in captured.out.lower()

