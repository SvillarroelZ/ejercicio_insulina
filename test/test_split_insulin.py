# Tests for split_insulin: segment boundaries, lengths, and optional file outputs.
# For testing, files are created in tmp_path and monkeypatch.chdir is used to
# run in the temporary directory instead of the repository root.
# Fixtures used: tmp_path (isolated temp dir), monkeypatch (override behavior),
# capsys (capture stdout/stderr).

import importlib.util
from pathlib import Path

import pytest
import split_insulin


def test_import_split_insulin():
	# Test case: Verify split_insulin module can be imported without errors.
	# This is a smoke test that validates the module file has correct Python syntax and can be loaded by the Python interpreter.
	# Expected behavior: The module imports successfully and exposes at least one public callable (function).
	# Step 1: Get the repository root (parent directory of the test directory)
	# Path(__file__).resolve() gets the absolute path of this test file.
	# .parents[1] gets the parent's parent (repo root).
	repo_root = Path(__file__).resolve().parents[1]
	
	# Step 2: Create a module spec from the split_insulin.py file
	# importlib.util.spec_from_file_location(name, location) creates a module spec.
	# name: arbitrary name for the module (doesn't have to match filename).
	# location: absolute path to the .py file.
	mod_path = repo_root / "src" / "split_insulin.py"
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
	# Real-world test case: Split the 110 amino acid preproinsulin into four segments.
	# Validates the core functionality: given a 110 aa sequence, split_insulin() correctly divides it into the four expected segments with correct lengths: LS: 24 aa, B: 30 aa, C: 35 aa, A: 21 aa.
	# To prevent touching repository files: 1. Create a test sequence in tmp_path. 2. Change working directory to tmp_path using monkeypatch.chdir(). 3. Call split_insulin.split_insulin() which will read/write files in the temp dir. 4. Verify the output files and their contents.
	# Expected behavior: Four output files are created with expected names and content. Each file contains the correct segment length. The segments are contiguous (no gaps, no overlaps). All files remain in tmp_path (not in repo root).
	# Step 1: Create a 110 amino acid test sequence
	# Using the actual human preproinsulin sequence.
	seq_110 = (
		"malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
		"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
	)
	assert len(seq_110) == 110, "Test sequence must be exactly 110 aa"
	
	# Step 2: Create the input file and call the function without writing files
	input_file = tmp_path / "preproinsulin_seq_clean.txt"
	input_file.write_text(seq_110)
	ls, b, c, a = split_insulin.split_insulin(clean_file=str(input_file), write_files=False)

	# Step 3: Verify segment lengths and boundaries
	assert len(ls) == 24, f"LS should be 24 aa, got {len(ls)}"
	assert len(b) == 30, f"B should be 30 aa, got {len(b)}"
	assert len(c) == 35, f"C should be 35 aa, got {len(c)}"
	assert len(a) == 21, f"A should be 21 aa, got {len(a)}"
	assert ls + b + c + a == seq_110, "Segments should reconstruct original sequence"
	
def test_split_insulin_main_block_executes_core(tmp_path, monkeypatch):
	# Execute split_insulin.py via its __main__ block to cover CLI path.
	# Script reads from and writes to data/ directory.
	# Output files will be cleaned by conftest.py after tests.
	repo_root = Path(__file__).resolve().parents[1]
	data_dir = repo_root / "data"
	
	# Prepare cleaned input file in data/ directory
	seq_110 = (
		"malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
		"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
	)
	input_file = data_dir / "preproinsulin_seq_clean.txt"
	input_file.write_text(seq_110)

	import runpy
	runpy.run_path(str(repo_root / "src" / "split_insulin.py"), run_name="__main__")

	# Verify outputs were created in data/ directory
	assert (data_dir / "lsinsulin_seq_clean.txt").exists(), "LS file should be in data/"
	assert (data_dir / "binsulin_seq_clean.txt").exists(), "B file should be in data/"
	assert (data_dir / "binsulin_seq_clean.txt").exists(), "B file should be in data/"
	assert (data_dir / "cinsulin_seq_clean.txt").exists(), "C file should be in data/"
	assert (data_dir / "ainsulin_seq_clean.txt").exists(), "A file should be in data/"


def test_split_insulin_error_for_non_110_sequence(tmp_path, monkeypatch, capsys):
	# Test case: Error handling when input sequence is not 110 amino acids.
	# split_insulin() is designed specifically for the 110 aa preproinsulin. If the input is the wrong length, the function should: 1. Detect the error. 2. Print an error message. 3. Return without creating output files.
	# This tests the function's defensive programming. The capsys fixture captures stdout and stderr so we can verify that error messages are printed correctly.
	# Expected behavior: No output files are created. An error message is printed to stdout.
	# Step 1: Create a sequence that is NOT 110 amino acids
	# Too short: 100 aa
	seq_wrong = "a" * 100
	
	# Step 2: Create input file with wrong length
	input_file = tmp_path / "preproinsulin_seq_clean.txt"
	input_file.write_text(seq_wrong)
	
	# Step 3: Change to temp directory
	monkeypatch.chdir(tmp_path)
	
	# Step 4: Call split_insulin with explicit file path
	# It should detect the wrong length and return without creating files.
	split_insulin.split_insulin(clean_file=str(input_file))
	
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


def test_split_insulin_segments_are_non_overlapping(tmp_path, monkeypatch):
	# Verify segments don't overlap and cover entire sequence.
	seq_110 = (
		"malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
		"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
	)
	inp = tmp_path / "preproinsulin_seq_clean.txt"
	inp.write_text(seq_110)
	monkeypatch.chdir(tmp_path)
	
	ls, b, c, a = split_insulin.split_insulin(clean_file=str(inp), write_files=False)
	
	# Verify segments are contiguous
	assert ls + b + c + a == seq_110, "Segments should reconstruct original without gaps"
	
	# Verify no overlap by checking cumulative lengths
	cumulative_length = len(ls) + len(b) + len(c) + len(a)
	assert cumulative_length == 110, f"Total segment length {cumulative_length} should equal 110"


def test_split_insulin_returns_empty_tuple_for_wrong_length(tmp_path, monkeypatch):
	# Verify split_insulin returns empty tuple for non-110 sequences.
	# Create a sequence that's not 110 amino acids
	short_seq = "ATGC" * 10  # 40 amino acids
	inp = tmp_path / "preproinsulin_seq_clean.txt"
	inp.write_text(short_seq)
	monkeypatch.chdir(tmp_path)
	
	result = split_insulin.split_insulin(clean_file=str(inp), write_files=False)
	
	assert result == tuple(), "Should return empty tuple for invalid length"
	assert not (tmp_path / "lsinsulin_seq_clean.txt").exists(), "Should not create files for invalid input"


def test_split_insulin_with_whitespace_in_sequence(tmp_path, monkeypatch):
	# Test that split_insulin handles sequences with trailing whitespace
	seq_110 = (
		"malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
		"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
	)
	# Add whitespace that should be stripped
	seq_with_whitespace = seq_110 + "\n  \t"
	
	inp = tmp_path / "preproinsulin_seq_clean.txt"
	inp.write_text(seq_with_whitespace)
	monkeypatch.chdir(tmp_path)
	
	ls, b, c, a = split_insulin.split_insulin(clean_file=str(inp), write_files=False)
	
	# Should still work after stripping
	assert len(ls) == 24
	assert len(b) == 30
	assert len(c) == 35
	assert len(a) == 21


def test_split_insulin_write_files_true(tmp_path, monkeypatch):
	# Test that write_files=True actually creates files
	seq_110 = (
		"malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
		"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
	)
	
	# Create data directory structure in tmp_path
	data_dir = tmp_path / "data"
	data_dir.mkdir()
	
	inp = data_dir / "preproinsulin_seq_clean.txt"
	inp.write_text(seq_110)
	
	# Import module and override _DATA_DIR
	repo_root = Path(__file__).resolve().parents[1]
	mod_path = repo_root / "src" / "split_insulin.py"
	spec = importlib.util.spec_from_file_location("split_insulin_test", str(mod_path))
	module = importlib.util.module_from_spec(spec)
	
	# Monkeypatch the _DATA_DIR before executing
	original_data_dir = Path(__file__).resolve().parent.parent / "data"
	monkeypatch.setattr(module, "_DATA_DIR", data_dir, raising=False)
	spec.loader.exec_module(module)
	monkeypatch.setattr(module, "_DATA_DIR", data_dir)
	
	ls, b, c, a = module.split_insulin(clean_file=str(inp), write_files=True)
	
	# Verify files were created
	assert (data_dir / "lsinsulin_seq_clean.txt").exists()
	assert (data_dir / "binsulin_seq_clean.txt").exists()
	assert (data_dir / "cinsulin_seq_clean.txt").exists()
	assert (data_dir / "ainsulin_seq_clean.txt").exists()
	
	# Verify file contents
	assert (data_dir / "lsinsulin_seq_clean.txt").read_text() == ls
	assert (data_dir / "binsulin_seq_clean.txt").read_text() == b
	assert (data_dir / "cinsulin_seq_clean.txt").read_text() == c
	assert (data_dir / "ainsulin_seq_clean.txt").read_text() == a


def test_split_insulin_boundary_positions(tmp_path, monkeypatch):
	# Test exact boundary positions of each segment
	seq_110 = (
		"malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
		"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
	)
	
	inp = tmp_path / "preproinsulin_seq_clean.txt"
	inp.write_text(seq_110)
	
	ls, b, c, a = split_insulin.split_insulin(clean_file=str(inp), write_files=False)
	
	# Verify exact boundaries
	assert ls == seq_110[0:24]    # positions 1-24
	assert b == seq_110[24:54]    # positions 25-54
	assert c == seq_110[54:89]    # positions 55-89
	assert a == seq_110[89:110]   # positions 90-110