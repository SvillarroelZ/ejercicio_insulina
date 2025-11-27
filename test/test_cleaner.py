"""
Unit tests for the cleaner module.

This module tests the clean_sequence() function and the clean_preproinsulin() wrapper.
The tests validate:
  1. Normal behavior with NCBI ORIGIN-format input.
  2. Input without ORIGIN/end markers but with noise (digits, punctuation).
  3. Error handling when input file does not exist.
  4. The wrapper function that uses module-level constants.
  5. Real-world case: cleaning the actual 110 amino acid preproinsulin sequence.
  6. Edge cases: empty files, files with only non-letter characters.

All tests use tmp_path (pytest fixture) to ensure files are created only
inside a temporary directory and are cleaned up automatically after the test.
No files are left in the repository root.

Key pytest fixtures used:
  - tmp_path: Provides an isolated temporary directory per test. Pytest
    automatically deletes it after the test completes. Use it like a
    regular pathlib.Path object.
  - monkeypatch: Allows temporary modification of module attributes (like
    constants). After the test, attributes are restored to original values.
"""

import re
from pathlib import Path

import pytest

from cleaner import clean_sequence, clean_preproinsulin as cleaner_main


def _expected_clean(text: str) -> str:
	r"""
	Helper function to compute the expected cleaned sequence.
	
	This mimics exactly what clean_sequence() does:
	  1. Remove the string "ORIGIN" and "//" (NCBI format markers).
	  2. Remove all digits and whitespace (regex: [0-9\s]).
	  3. Keep only letters (A-Z, a-z) and convert to lowercase.
	
	This helper ensures our assertions match the actual function behavior.
	If clean_sequence() changes its logic, we update this helper and all
	tests automatically use the new expected behavior.
	
	Args:
	    text: Raw input text that may contain ORIGIN markers, numbers, spaces, etc.
	
	Returns:
	    Cleaned string containing only lowercase letters.
	
	Example:
	    >>> _expected_clean("ORIGIN\n1 atg 2 cta\n//")
	    'atgcta'
	"""
	# Step 1: Remove ORIGIN and end markers (// is the NCBI end-of-sequence marker)
	# str.replace() returns a new string with all occurrences of the substring replaced.
	# We chain two replace() calls: first remove "ORIGIN", then remove "//".
	data = text.replace("ORIGIN", "").replace("//", "")
	
	# Step 2: Use regex to remove all digits and whitespace (spaces, tabs, newlines)
	# re.sub(pattern, replacement, string) replaces all matches of pattern with replacement.
	# [0-9\s] is a character class matching: 0-9 (any digit) or \s (any whitespace).
	# The second argument "" means replace with nothing (delete).
	data = re.sub(r"[0-9\s]", "", data)
	
	# Step 3: Keep only alphabetic characters and convert to lowercase
	# [^a-zA-Z] is a negated character class: ^ means "NOT", so [^...] matches anything NOT in [...]
	# This matches any character that is NOT a letter; we replace it with "" (delete it).
	# .lower() converts uppercase letters to lowercase.
	return re.sub(r"[^a-zA-Z]", "", data).lower()


def test_clean_sequence_nominal_origin_format(tmp_path):
	"""
	Test case: Normal workflow with a file in NCBI ORIGIN format.
	
	This is the typical use case: a raw sequence from NCBI that includes
	the ORIGIN header, position numbers, whitespace and the // end marker.
	
	The tmp_path fixture creates an isolated temporary directory for this test.
	All files created inside tmp_path are automatically deleted by pytest after
	the test completes, ensuring no side effects in the repository.
	
	Expected behavior:
	  - The function should read the file, clean it, and write the result.
	  - Return value should be the cleaned sequence (lowercase letters only).
	  - Output file should exist and contain the exact cleaned sequence.
	"""
	# Step 1: Create input text in NCBI ORIGIN format
	# Real ORIGIN files have a header "ORIGIN", position numbers (1, 61, ...) and grouped sequences
	content = """ORIGIN
1 atg cta 4 ggg
//
"""
	
	# Step 2: Create file paths inside tmp_path (temporary directory)
	# tmp_path is a pytest fixture that provides an isolated temp directory per test.
	# Usage: treat tmp_path like pathlib.Path. Example: tmp_path / "filename.txt"
	# Using tmp_path ensures cleanup: pytest automatically deletes tmp_path after test ends.
	# This is why we don't need to manually clean up files—pytest does it.
	inp = tmp_path / "in_origin.txt"
	out = tmp_path / "out_clean.txt"
	
	# Step 3: Write the input file to the temp directory
	# .write_text() is a pathlib.Path method that writes a string to a file.
	# It creates the file if it doesn't exist; overwrites if it does.
	inp.write_text(content)

	# Step 4: Compute the expected result using our helper
	# The expected output will be "atgctaggg" (all lowercase, no numbers/spaces/special chars)
	expected = _expected_clean(content)

	# Step 5: Call the function under test
	# clean_sequence() reads the file at inp, applies the cleaning logic,
	# writes the result to the file at out, and returns the cleaned string.
	# We convert pathlib.Path to str using str() because clean_sequence expects str.
	result = clean_sequence(str(inp), str(out))

	# Step 6: Assertions to verify correct behavior
	# Assert 1: The function returns a string (not None, not bytes, not some other type)
	assert isinstance(result, str), "clean_sequence should return a string"
	
	# Assert 2: The returned value matches our expected cleaned sequence
	assert result == expected, f"Expected {expected}, got {result}"
	
	# Assert 3: The output file was actually created on disk
	# .exists() is a pathlib.Path method that returns True if the file/directory exists.
	assert out.exists(), f"Output file {out} was not created"
	
	# Assert 4: The file content matches the returned value
	# This verifies the function wrote to the file correctly (not just returned the value).
	# .read_text() reads the entire file as a string.
	assert out.read_text() == expected, "Output file content does not match expected"


def test_clean_sequence_no_origin_labels(tmp_path):
	"""
	Test case: Input without ORIGIN markers but with noise (numbers, symbols).
	
	This tests the cleaner's robustness to input that doesn't follow the
	exact NCBI format but still contains unwanted characters (punctuation,
	digits, mixed case, etc.).
	
	Expected behavior:
	  - The function should silently handle the missing markers (no error).
	  - All non-letter characters should be removed.
	  - Output should be clean lowercase letters.
	"""
	# Step 1: Create input with no ORIGIN/end markers but lots of noise
	# This simulates a user providing a messy sequence file.
	content = "abc123 xy!z-.,_ 987"
	
	# Step 2: Create temp file paths
	inp = tmp_path / "in_simple.txt"
	out = tmp_path / "out_simple.txt"
	
	# Step 3: Write noisy input to temp file
	inp.write_text(content)

	# Step 4: Calculate expected result
	# Input: "abc123 xy!z-.,_ 987"
	# Remove digits and spaces: "abcxyz"
	# Remove non-letters: "abcxyz" (no change, all are letters)
	# Lowercase: "abcxyz"
	# Note: there are no ORIGIN or // to remove, but the function handles that fine.
	expected = _expected_clean(content)

	# Step 5: Call clean_sequence
	result = clean_sequence(str(inp), str(out))

	# Step 6: Verify the function handled this format correctly
	# The function should not fail even though the input lacks ORIGIN markers.
	assert result == expected, "Failed to clean sequence without ORIGIN markers"
	
	# Assert: File content is clean
	assert out.read_text() == expected, "Output file does not match expected for non-ORIGIN input"


def test_clean_sequence_file_not_found_raises():
	"""
	Test case: Error handling when input file does not exist.
	
	Expected behavior:
	  - The function should raise FileNotFoundError.
	  - This verifies the function properly propagates OS errors
	    (it does not catch and suppress the exception).
	  
	We use pytest.raises() to verify an exception is raised.
	If the code does NOT raise the expected exception, the test fails.
	"""
	# Step 1: Use pytest.raises() context manager to expect an exception
	# Syntax: with pytest.raises(ExceptionType): <code that should raise>
	# If the code raises the specified exception, the test passes.
	# If it doesn't raise (or raises a different exception), the test fails.
	with pytest.raises(FileNotFoundError):
		# Step 2: Call clean_sequence with a file path that does not exist
		# The function will call open(input_file, "r") which will raise FileNotFoundError
		# because the file path points to a nonexistent file.
		clean_sequence("this_file_does_not_exist.xyz", "does_not_matter.txt")


def test_clean_preproinsulin_uses_constants_and_writes(tmp_path, monkeypatch):
	"""
	Test case: The wrapper function clean_preproinsulin() uses module constants.
	
	The cleaner module defines two module-level constants:
	  - INPUT_FILE = "preproinsulin_seq.txt"
	  - OUTPUT_FILE = "preproinsulin_seq_clean.txt"
	
	The wrapper clean_preproinsulin() calls clean_sequence(INPUT_FILE, OUTPUT_FILE).
	For testing, we don't want to use the actual files. Instead, we use
	monkeypatch (a pytest fixture) to temporarily replace the constants.
	
	monkeypatch.setattr(target, name, value):
	  - target: string like "module.CONSTANT_NAME"
	  - name: not needed when using string form (it's implicit in target)
	  - value: the replacement value
	
	After the test, monkeypatch automatically restores the original values.
	This is cleaner and safer than modifying the module directly.
	
	Expected behavior:
	  - The wrapper should read from INPUT_FILE and write to OUTPUT_FILE.
	  - When we monkeypatch these constants, the wrapper uses our temp files.
	  - After the test, the constants are restored to their original values.
	  - No files are left in the repo root.
	"""
	# Step 1: Create temp file paths for input and output
	# These will temporarily replace the module's INPUT_FILE and OUTPUT_FILE.
	# We create them in tmp_path so they're automatically cleaned up.
	input_path = tmp_path / "prepro_in.txt"
	output_path = tmp_path / "prepro_out.txt"

	# Step 2: Create test input in ORIGIN format
	content = "ORIGIN\n1 a t g c 2 g a\n//\n"
	
	# Step 3: Write the input file to our temp directory
	input_path.write_text(content)

	# Step 4: Use monkeypatch to temporarily override the module constants
	# monkeypatch.setattr() replaces a module attribute for the duration of the test.
	# Syntax: monkeypatch.setattr("module.CONSTANT", new_value)
	# After the test, monkeypatch automatically restores the original values.
	# raising=False tells monkeypatch to not raise an error if the attribute doesn't exist.
	# This is useful for defensive coding if the module structure changes.
	monkeypatch.setattr("cleaner.INPUT_FILE", str(input_path), raising=False)
	monkeypatch.setattr("cleaner.OUTPUT_FILE", str(output_path), raising=False)

	# Step 5: Call the wrapper function
	# Since we monkeypatched the constants, the wrapper will use our temp files,
	# not the real "preproinsulin_seq.txt" and "preproinsulin_seq_clean.txt".
	cleaner_main()

	# Step 6: Verify the wrapper worked correctly
	# Assert 1: The output file was created where we expected it
	assert output_path.exists(), "Wrapper did not create output file"
	
	# Assert 2: The output file contains the expected cleaned sequence
	# We calculate the expected value and compare.
	assert output_path.read_text() == _expected_clean(content), "Output content is incorrect"


def test_clean_sequence_with_real_preproinsulin_data(tmp_path):
	"""
	Real-world test case: Clean the actual human preproinsulin sequence.
	
	This test uses a realistic 110 amino acid preproinsulin sequence
	(human insulin protein) in a format similar to what you would download
	from a biological database (like NCBI). This validates that the cleaner
	correctly handles real, biologically relevant data.
	
	The preproinsulin is a precursor to insulin. After processing, it yields:
	  - LS (leader sequence, 24 aa)
	  - B-chain (30 aa)
	  - C-peptide (35 aa)
	  - A-chain (21 aa)
	
	Expected behavior:
	  - Input is 110 aa with ORIGIN markers, position numbers, and grouped layout.
	  - After cleaning, result should be exactly 110 lowercase letters.
	  - The sequence should match the known human preproinsulin.
	  - This output is critical downstream: split_insulin.py expects exactly 110 aa.
	"""
	# Step 1: Real human preproinsulin sequence (110 amino acids)
	# This is the actual sequence from standard biological databases.
	# Format: single-letter amino acid codes (m=methionine, a=alanine, etc.)
	real_seq = (
		"malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
		"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
	)
	
	# Step 2: Format the real sequence as if it came from NCBI
	# NCBI ORIGIN format: groups of 60 characters per line, position numbers
	# We'll simulate this format to test real-world input.
	formatted_lines = []
	for i, char in enumerate(real_seq, 1):
		# Every 60 characters, add a new line with position number
		if (i - 1) % 60 == 0:
			formatted_lines.append(f"{i:>5} ")
		formatted_lines.append(char)
		if i % 60 == 0:
			formatted_lines.append("\n")
	
	# Create the complete ORIGIN-formatted string
	origin_formatted = "ORIGIN\n" + "".join(formatted_lines) + "\n//\n"
	
	# Step 3: Create temp file
	inp = tmp_path / "real_prepro.txt"
	out = tmp_path / "real_prepro_clean.txt"
	inp.write_text(origin_formatted)
	
	# Step 4: Clean the real sequence
	result = clean_sequence(str(inp), str(out))
	
	# Step 5: Verify the results
	# The cleaned sequence should be exactly the real sequence in lowercase
	# This ensures the cleaner handles multiline ORIGIN format correctly.
	assert result == real_seq.lower(), "Real preproinsulin sequence not cleaned correctly"
	
	# The length must be 110 amino acids (this is critical for downstream processing).
	# split_insulin.py will fail if this is not exactly 110.
	assert len(result) == 110, f"Cleaned sequence has {len(result)} aa, expected 110"
	
	# The output file should match
	assert out.read_text() == real_seq.lower(), "Output file does not match expected real sequence"


def test_clean_sequence_empty_file(tmp_path):
	"""
	Edge case test: Empty or whitespace-only input file.
	
	Validates robustness: the cleaner should handle edge cases gracefully
	without crashes or unexpected behavior.
	
	Expected behavior:
	  - An empty file should result in an empty cleaned sequence.
	  - No errors should be raised.
	  - The output file should exist but be empty.
	"""
	# Step 1: Create an empty file
	inp = tmp_path / "empty.txt"
	out = tmp_path / "empty_clean.txt"
	inp.write_text("")
	
	# Step 2: Call clean_sequence on empty input
	result = clean_sequence(str(inp), str(out))
	
	# Step 3: Verify behavior
	# Empty input should produce empty output (no error, no crash)
	assert result == "", "Empty file should produce empty result"
	
	# The output file should exist and be empty
	assert out.exists(), "Output file should be created even for empty input"
	assert out.read_text() == "", "Output file should be empty for empty input"


def test_clean_sequence_only_numbers_and_symbols(tmp_path):
	"""
	Edge case test: Input containing only numbers and symbols (no letters).
	
	Validates robustness: what happens when the input has no valid characters?
	
	Expected behavior:
	  - All characters should be removed during cleaning.
	  - Result should be an empty string.
	  - No error should be raised.
	  - The output file should exist but be empty.
	"""
	# Step 1: Create input with no letters, only noise
	content = "123 456 !@# $%^ &*( )"
	inp = tmp_path / "no_letters.txt"
	out = tmp_path / "no_letters_clean.txt"
	inp.write_text(content)
	
	# Step 2: Clean the input
	result = clean_sequence(str(inp), str(out))
	
	# Step 3: Verify behavior
	# After removing all non-letters, the result should be empty
	assert result == "", "Input with no letters should produce empty result"
	
	# The output file should be empty
	assert out.read_text() == "", "Output file should be empty for input with no letters"
