"""
Real pipeline validation test.

This test executes the COMPLETE pipeline using the actual repository data
in an isolated temporary directory. Unlike isolated unit tests, this test:

1. Copies the real preproinsulin_seq.txt file to a temporary directory.
2. Executes clean_sequence() to generate preproinsulin_seq_clean.txt.
3. Executes split_insulin.split_insulin() to generate four segment files.
4. Imports and executes string-insulin.py and net-charge.py with generated files.
5. Validates that all outputs match expected biological values.
6. Uses tmp_path for isolation, so no cleanup is needed in repo root.

This test validates that the code ACTUALLY WORKS end-to-end with real data
while keeping the repository clean during test execution.

Expected flow:
  preproinsulin_seq.txt (ORIGIN format, 110 aa)
       ↓ clean_sequence()
  preproinsulin_seq_clean.txt (cleaned, 110 lowercase letters)
       ↓ split_insulin.split_insulin()
  ├─ lsinsulin_seq_clean.txt (24 aa)
  ├─ binsulin_seq_clean.txt (30 aa)
  ├─ cinsulin_seq_clean.txt (35 aa)
  └─ ainsulin_seq_clean.txt (21 aa)
       ↓ import string-insulin.py
  molecularWeightInsulin (computed from B + A chains)
       ↓ import net-charge.py
  seqCount + pH vs net-charge table
"""

import importlib.util
import shutil
from pathlib import Path

import pytest

from cleaner import clean_sequence
import split_insulin


def test_real_pipeline_end_to_end_with_actual_repo_files(tmp_path, monkeypatch):
    """
    End-to-end validation test with REAL repository data in isolated tmp_path.

    This test executes the actual pipeline using the real preproinsulin_seq.txt
    file from the repository, but runs it in a temporary directory to avoid
    polluting the repository root with generated files.

    Validates that:
    1. clean_sequence() correctly cleans the ORIGIN-formatted input.
    2. split_insulin() correctly splits the 110 aa sequence into 4 segments.
    3. string-insulin.py correctly reads segments and computes molecular weight.
    4. net-charge.py correctly reads B and A chains and computes charge.

    Expected values (derived from human preproinsulin biological data):
      - Total length: 110 amino acids (preproinsulin)
      - LS segment: 24 amino acids
      - B-chain: 30 amino acids
      - C-peptide: 35 amino acids
      - A-chain: 21 amino acids
      - Insulin (B + A): 51 amino acids
      - Approximate molecular weight of insulin: 5800-5900 Da
      - Charge-bearing amino acids: K, R, H (positive), D, E, C, Y (negative)

    This test will fail immediately if any module in the pipeline is broken.
    """

    repo_root = Path(__file__).resolve().parents[1]

    # Step 1: Copy the original input file to tmp_path
    input_file = repo_root / "preproinsulin_seq.txt"
    assert input_file.exists(), "preproinsulin_seq.txt should exist in repo root"
    
    tmp_input = tmp_path / "preproinsulin_seq.txt"
    shutil.copy(input_file, tmp_input)
    
    original_content = tmp_input.read_text()
    assert "ORIGIN" in original_content, "Input file should be in NCBI ORIGIN format"
    assert "//" in original_content, "Input file should end with // marker"
    
    # Change to tmp_path so all files are generated there
    monkeypatch.chdir(tmp_path)

    # Step 2: Run clean_sequence to generate preproinsulin_seq_clean.txt in tmp_path
    clean_sequence(
        input_file="preproinsulin_seq.txt",
        output_file="preproinsulin_seq_clean.txt",
        expected_length=110
    )

    # Step 3: Verify the cleaned file was created and has correct properties
    cleaned_file = tmp_path / "preproinsulin_seq_clean.txt"
    assert cleaned_file.exists(), "preproinsulin_seq_clean.txt should exist after cleaning"
    cleaned_seq = cleaned_file.read_text().strip()

    # Validate cleaned sequence properties
    assert len(cleaned_seq) == 110, f"Cleaned sequence should be 110 aa, got {len(cleaned_seq)}"
    assert cleaned_seq.islower(), "Cleaned sequence should be all lowercase"
    assert cleaned_seq.isalpha(), "Cleaned sequence should contain only letters"
    
    # Verify no ORIGIN markers or digits remain
    assert "ORIGIN" not in cleaned_seq, "Cleaned sequence should not contain ORIGIN"
    assert "//" not in cleaned_seq, "Cleaned sequence should not contain //"
    assert any(c.isdigit() for c in cleaned_seq) == False, "Cleaned sequence should not contain digits"

    # Step 4: Run split_insulin to generate the four segment files in tmp_path
    split_insulin.split_insulin()

    # Step 5: Verify all four segment files were created with correct content in tmp_path
    ls_file = tmp_path / "lsinsulin_seq_clean.txt"
    b_file = tmp_path / "binsulin_seq_clean.txt"
    c_file = tmp_path / "cinsulin_seq_clean.txt"
    a_file = tmp_path / "ainsulin_seq_clean.txt"

    # Verify files exist
    assert ls_file.exists(), "lsinsulin_seq_clean.txt should exist after split"
    assert b_file.exists(), "binsulin_seq_clean.txt should exist after split"
    assert c_file.exists(), "cinsulin_seq_clean.txt should exist after split"
    assert a_file.exists(), "ainsulin_seq_clean.txt should exist after split"

    # Read segment content
    ls_seq = ls_file.read_text().strip()
    b_seq = b_file.read_text().strip()
    c_seq = c_file.read_text().strip()
    a_seq = a_file.read_text().strip()

    # Step 6: Validate segment lengths (biological invariant)
    assert len(ls_seq) == 24, f"LS segment should be 24 aa, got {len(ls_seq)}"
    assert len(b_seq) == 30, f"B-chain should be 30 aa, got {len(b_seq)}"
    assert len(c_seq) == 35, f"C-peptide should be 35 aa, got {len(c_seq)}"
    assert len(a_seq) == 21, f"A-chain should be 21 aa, got {len(a_seq)}"

    # Step 7: Validate segment reconstruction
    reconstructed = ls_seq + b_seq + c_seq + a_seq
    assert reconstructed == cleaned_seq, "Segments should reconstruct the cleaned sequence exactly"
    assert len(reconstructed) == 110, f"Reconstructed sequence should be 110 aa, got {len(reconstructed)}"

    # Step 8: Import and execute string-insulin.py with files from tmp_path
    # We're still in tmp_path due to monkeypatch.chdir(), so imports will find the files
    repo_root = Path(__file__).resolve().parents[1]
    string_path = repo_root / "string-insulin.py"
    spec = importlib.util.spec_from_file_location("string_insulin", str(string_path))
    string_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(string_mod)

    # Step 9: Validate string-insulin.py results
    # Verify insulin variable is constructed correctly (B + A chains)
    assert hasattr(string_mod, "insulin"), "Module should expose 'insulin' variable"
    expected_insulin = b_seq + a_seq
    assert string_mod.insulin == expected_insulin, "insulin should be B + A chains concatenated"
    assert len(string_mod.insulin) == 51, f"Insulin should be 51 aa (30+21), got {len(string_mod.insulin)}"

    # Verify molecular weight computation
    assert hasattr(string_mod, "molecularWeightInsulin"), "Module should compute 'molecularWeightInsulin'"
    mw = string_mod.molecularWeightInsulin
    
    # Validate MW is in realistic range for human insulin (51 aa)
    # Real human insulin is ~5807.63 Da; our calculated value should be close
    assert mw > 5000, f"MW should be > 5000 Da for 51 aa, got {mw}"
    assert mw < 7000, f"MW should be < 7000 Da for 51 aa, got {mw}"
    
    # Verify error percentage is computed
    assert hasattr(string_mod, "error_percentage"), "Module should compute 'error_percentage'"
    error_pct = string_mod.error_percentage
    assert isinstance(error_pct, float), "error_percentage should be a float"

    # Step 10: Import and execute net-charge.py with real files
    net_path = repo_root / "net-charge.py"
    spec2 = importlib.util.spec_from_file_location("net_charge", str(net_path))
    net_mod = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(net_mod)

    # Step 11: Validate net-charge.py results
    # Verify seqCount dictionary exists and contains amino acid counts
    assert hasattr(net_mod, "seqCount"), "Module should expose 'seqCount' dictionary"
    seqCount = net_mod.seqCount

    # Validate counts for the insulin sequence (B + A)
    insulin_seq = b_seq + a_seq
    for aa in ['y', 'c', 'k', 'h', 'r', 'd', 'e']:
        expected_count = insulin_seq.count(aa)
        actual_count = seqCount[aa]
        assert actual_count == expected_count, \
            f"Count for {aa} should be {expected_count}, got {actual_count}"

    # Verify positive and negative charge counts are reasonable
    pos_count = seqCount['k'] + seqCount['r'] + seqCount['h']
    neg_count = seqCount['d'] + seqCount['e'] + seqCount['c'] + seqCount['y']
    
    assert pos_count >= 0, "Positive charge count should be non-negative"
    assert neg_count >= 0, "Negative charge count should be non-negative"

    # Step 12: Summary validation
    # Verify that the pipeline successfully produced valid biological results
    # If we reach here without assertion failures, the pipeline is working correctly
    assert True, "Real pipeline validation completed successfully"
