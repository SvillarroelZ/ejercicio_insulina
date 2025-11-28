"""
Additional tests for the insulin exercises.

This file contains two pytest tests:

1) test_string_insulin_missing_files_raises:
   - create only preproinsulin and lsinsulin files (omit binsulin or ainsulin)
   - change cwd to tmp_path using monkeypatch
   - attempt to import `string-insulin.py` via importlib
   - assert that FileNotFoundError is raised

2) test_net_charge_seqcount_and_output:
   - create all required cleaned sequence files in tmp_path with a designed
     B-chain + A-chain sequence so counts of 'y','c','k','h','r','d','e' are known
   - change cwd to tmp_path using monkeypatch
   - import `net-charge.py` via importlib
   - assert that the imported module's `seqCount` matches expected floats
   - assert that stdout captured during import includes the 'pH' header and at least one pH numeric line
"""

from pathlib import Path
import importlib.util
import pytest
import re


def _load_module_from_repo(script_name: str, module_name: str):
    """
    Helper to load a module from the repository root by filename.
    Returns the loaded module object.
    """
    repo_root = Path(__file__).resolve().parents[1]  # project root (..)
    script_path = repo_root / script_name
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    module = importlib.util.module_from_spec(spec)
    # Execute the module (this runs its top-level code)
    spec.loader.exec_module(module)
    return module


def test_string_insulin_missing_files_raises(tmp_path, monkeypatch):
    """
    If some cleaned sequence files are missing, importing the
    `string-insulin.py` script should fail with FileNotFoundError.
    """
    # Create only two of the required files (omit binsulin and ainsulin)
    (tmp_path / "preproinsulin_seq_clean.txt").write_text("prepro_dummy_sequence")
    (tmp_path / "lsinsulin_seq_clean.txt").write_text("ls_dummy_sequence")
    monkeypatch.chdir(tmp_path)

    # Importing should raise a FileNotFoundError because additional files are missing
    with pytest.raises(FileNotFoundError):
        _load_module_from_repo("string-insulin.py", "string_insulin_missing_test")


def test_net_charge_seqcount_and_output(tmp_path, monkeypatch, capsys):
    """
    Create all required cleaned sequence files with a deterministic B-chain + A-chain
    such that the counts for the following amino acids are known:
    'y', 'c', 'k', 'h', 'r', 'd', 'e'.

    Chosen sequences:
      binsulin_seq_clean.txt = "yckk"
      ainsulin_seq_clean.txt = "hrede"
    Combined insulin = "yckkhrede" with counts:
      y:1, c:1, k:2, h:1, r:1, d:1, e:1
    """
    (tmp_path / "preproinsulin_seq_clean.txt").write_text("prepro_dummy")
    (tmp_path / "lsinsulin_seq_clean.txt").write_text("ls_dummy")
    (tmp_path / "binsulin_seq_clean.txt").write_text("yckk")
    (tmp_path / "ainsulin_seq_clean.txt").write_text("hrede")
    (tmp_path / "cinsulin_seq_clean.txt").write_text("cpeptide_dummy")

    monkeypatch.chdir(tmp_path)

    # Load net-charge.py (it prints to stdout during import)
    net_mod = _load_module_from_repo("net-charge.py", "net_charge_test_mod")

    # note: 'e' appears twice in the chosen A-chain 'hrede'
    expected = {'y': 1.0, 'c': 1.0, 'k': 2.0, 'h': 1.0, 'r': 1.0, 'd': 1.0, 'e': 2.0}

    assert hasattr(net_mod, "seqCount"), "Imported module must define seqCount"
    assert net_mod.seqCount == expected

    captured = capsys.readouterr()
    out = captured.out

    assert "pH" in out, "Output must include header 'pH'"

    numeric_pH_line_found = any(
        re.match(r'^\s*0(?:\.00)?\s*\|', line) or re.match(r'^\s*\d+\.\d{2}\s*\|', line)
        for line in out.splitlines()
    )
    assert numeric_pH_line_found, "Output must include at least one pH value line (e.g., '0.00 | ...')"
