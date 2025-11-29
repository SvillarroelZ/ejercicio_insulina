"""
Unit tests for the split_insulin module.

This module tests the split_insulin() function which takes a cleaned 110 amino acid
preproinsulin sequence and splits it into four biologically meaningful segments:
  1. LS (Leader Sequence): amino acids 1-24
  2. B-chain: amino acids 25-54
  3. C-peptide: amino acids 55-89
  4. A-chain: amino acids 90-110

The split_insulin() function reads from a file called "preproinsulin_seq_clean.txt"
and writes four output files. For testing, we create these files in a temporary
directory (tmp_path) and change the working directory (monkeypatch.chdir) so the
function operates there instead of in the repository root.

Key pytest fixtures used:
  - tmp_path: Isolated temporary directory, auto-cleaned after test.
  - monkeypatch: Temporarily modify module behavior or change working directory.
  - capsys: Capture printed output (stdout/stderr).
"""

import importlib.util
from pathlib import Path

import split_insulin


def test_import_split_insulin():
	"""
	Test case: Verify split_insulin module can be imported without errors.
	
	This is a smoke test that validates the module file has correct Python syntax
	and can be loaded by the Python interpreter.
	
	Expected behavior:
	  - The module imports successfully.
	  - The module exposes at least one public callable (function).
	"""
	# Step 1: Get the repository root (parent directory of the test directory)
	# Path(__file__).resolve() gets the absolute path of this test file.
	# .parents[1] gets the parent's parent (repo root).
	repo_root = Path(__file__).resolve().parents[1]
	
	# Step 2: Create a module spec from the split_insulin.py file
	# importlib.util.spec_from_file_location(name, location) creates a module spec.
	# name: arbitrary name for the module (doesn't have to match filename).
	# location: absolute path to the .py file.
	mod_path = repo_root / "split_insulin.py"
	spec = importlib.util.spec_from_file_location("split_insulin", str(mod_path))
	
	# Step 3: Create a module object from the spec
	# A spec is a blueprint; we need to create the actual module object.
	module = importlib.util.module_from_spec(spec)
	
	# Step 4: Execute the module code
	# spec.loader.exec_module(module) runs the module's top-level code.
	# If there's a syntax error or import error, this will raise an exception.
	spec.loader.exec_module(module)

	# Step 5: Verify the module has at least one public callable
	# We iterate over module.__dict__ (the module's namespace).
	# We filter for items that:
	#   - Don't start with "_" (exclude private/magic variables like __name__)
	#   - Are callable (functions, classes, etc.)
	public_callables = [v for k, v in module.__dict__.items() if not k.startswith("_") and callable(v)]
	assert len(public_callables) >= 1, "split_insulin module should expose at least one public function"


def test_split_insulin_splits_110_amino_acids_correctly(tmp_path, monkeypatch):
	"""
	Real-world test case: Split the 110 amino acid preproinsulin into four segments.
	
	This validates the core functionality: given a 110 aa sequence, split_insulin()
	correctly divides it into the four expected segments with correct lengths:
	  - LS: 24 aa
	  - B: 30 aa
	  - C: 35 aa
	  - A: 21 aa
	
	To prevent touching repository files, we:
	  1. Create a test sequence in tmp_path.
	  2. Change working directory to tmp_path using monkeypatch.chdir().
	  3. Call split_insulin.split_insulin() which will read/write files in the temp dir.
	  4. Verify the output files and their contents.
	
	Expected behavior:
	  - Four output files are created with expected names and content.
	  - Each file contains the correct segment length.
	  - The segments are contiguous (no gaps, no overlaps).
	  - All files remain in tmp_path (not in repo root).
	"""
	# Step 1: Create a 110 amino acid test sequence
	# Using the actual human preproinsulin sequence.
	seq_110 = (
		"malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
		"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
	)
	assert len(seq_110) == 110, "Test sequence must be exactly 110 aa"
	
	# Step 2: Create the input file that split_insulin expects
	# split_insulin.py reads from "preproinsulin_seq_clean.txt" by default.
	input_file = tmp_path / "preproinsulin_seq_clean.txt"
	input_file.write_text(seq_110)
	
	# Step 3: Change the working directory to tmp_path
	# monkeypatch.chdir(path) temporarily changes the current working directory.
	# All relative file operations (like split_insulin's open("filename.txt"))
	# will happen in tmp_path, not in the repo root.
	# After the test, monkeypatch restores the original working directory.
	monkeypatch.chdir(tmp_path)
	
	# Step 4: Call split_insulin.split_insulin()
	# This function reads the input file and creates four output files.
	split_insulin.split_insulin()
	
	# Step 5: Verify the output files were created with correct content
	# Expected segment boundaries (0-indexed slicing in Python):
	# LS: seq[0:24] (24 characters)
	# B:  seq[24:54] (30 characters)
	# C:  seq[54:89] (35 characters)
	# A:  seq[89:110] (21 characters)
	
	# Read and verify LS (Leader Sequence)
	ls_file = tmp_path / "lsinsulin_seq_clean.txt"
	assert ls_file.exists(), "lsinsulin_seq_clean.txt should be created"
	ls_content = ls_file.read_text()
	assert len(ls_content) == 24, f"LS should be 24 aa, got {len(ls_content)}"
	assert ls_content == seq_110[0:24], "LS content does not match expected segment"
	
	# Read and verify B-chain
	b_file = tmp_path / "binsulin_seq_clean.txt"
	assert b_file.exists(), "binsulin_seq_clean.txt should be created"
	b_content = b_file.read_text()
	assert len(b_content) == 30, f"B-chain should be 30 aa, got {len(b_content)}"
	assert b_content == seq_110[24:54], "B-chain content does not match expected segment"
	
	# Read and verify C-peptide
	c_file = tmp_path / "cinsulin_seq_clean.txt"
	assert c_file.exists(), "cinsulin_seq_clean.txt should be created"
	c_content = c_file.read_text()
	assert len(c_content) == 35, f"C-peptide should be 35 aa, got {len(c_content)}"
	assert c_content == seq_110[54:89], "C-peptide content does not match expected segment"
	
	# Read and verify A-chain
	a_file = tmp_path / "ainsulin_seq_clean.txt"
	assert a_file.exists(), "ainsulin_seq_clean.txt should be created"
	a_content = a_file.read_text()
	assert len(a_content) == 21, f"A-chain should be 21 aa, got {len(a_content)}"
	assert a_content == seq_110[89:110], "A-chain content does not match expected segment"
	
	# Step 6: Verify segments are contiguous (no gaps or overlaps)
	reconstructed = ls_content + b_content + c_content + a_content
	assert reconstructed == seq_110, "Segments should reconstruct the original sequence"
	assert len(reconstructed) == 110, f"Total length should be 110, got {len(reconstructed)}"


def test_split_insulin_error_for_non_110_sequence(tmp_path, monkeypatch, capsys):
	"""
	Test case: Error handling when input sequence is not 110 amino acids.
	
	split_insulin() is designed specifically for the 110 aa preproinsulin.
	If the input is the wrong length, the function should:
	  1. Detect the error.
	  2. Print an error message.
	  3. Return without creating output files.
	
	This tests the function's defensive programming.
	
	The capsys fixture captures stdout and stderr so we can verify
	that error messages are printed correctly.
	
	Expected behavior:
	  - No output files are created.
	  - An error message is printed to stdout.
	"""
	# Step 1: Create a sequence that is NOT 110 amino acids
	# Too short: 100 aa
	seq_wrong = "a" * 100
	
	# Step 2: Create input file with wrong length
	input_file = tmp_path / "preproinsulin_seq_clean.txt"
	input_file.write_text(seq_wrong)
	
	# Step 3: Change to temp directory
	monkeypatch.chdir(tmp_path)
	
	# Step 4: Call split_insulin
	# It should detect the wrong length and return without creating files.
	split_insulin.split_insulin()
	
	# Step 5: Verify that NO output files were created
	# This is the expected defensive behavior.
	assert not (tmp_path / "lsinsulin_seq_clean.txt").exists(), "LS file should not be created for wrong length"
	assert not (tmp_path / "binsulin_seq_clean.txt").exists(), "B file should not be created for wrong length"
	assert not (tmp_path / "cinsulin_seq_clean.txt").exists(), "C file should not be created for wrong length"
	assert not (tmp_path / "ainsulin_seq_clean.txt").exists(), "A file should not be created for wrong length"
	
	# Step 6: Verify error message was printed
	# capsys.readouterr() captures and returns the captured stdout and stderr.
	captured = capsys.readouterr()
	assert "ERROR" in captured.out, "Error message should be printed for wrong length"