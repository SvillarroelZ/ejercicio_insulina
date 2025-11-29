"""
Integration test for the full insulin processing pipeline.

This test runs the pipeline end-to-end inside a temporary directory so that
NO files are written to the repository root. All file operations happen
exclusively within tmp_path, which pytest automatically cleans up after
the test completes.

Pipeline steps covered (in order):
  1) `cleaner.clean_sequence` - cleans an ORIGIN-style input file and writes
     a cleaned sequence file.
  2) `split_insulin.split_insulin` - reads the cleaned file and splits it
     into LS, B, C and A segment files.
  3) `string-insulin.py` (import) - reads the segment files and computes a
     molecular weight value.
  4) `net-charge.py` (import) - reads the B/A chains and prints net charge
     values across pH values.

All files are created inside `tmp_path` and the test changes the current
working directory there for the duration of the test. After the test,
pytest automatically deletes tmp_path and all its contents.

Key fixture: monkeypatch.chdir(tmp_path) changes the working directory
so that all relative file operations (like open("filename.txt")) happen
inside tmp_path, not in the repository root.
"""

import importlib.util
from pathlib import Path

from cleaner import clean_sequence
import split_insulin


def _make_origin_content(seq_letters: str) -> str:
	"""
	Create a minimal NCBI ORIGIN-like block for given letters.

	The real `clean_sequence` implementation removes the string "ORIGIN",
	the end marker "//", any digits and whitespace and any non-letter
	characters. To make a realistic input we place the sequence letters
	separated into groups and include a leading numeric position. The
	returned string is written directly to a file and later cleaned by
	`clean_sequence`.
	
	Args:
	    seq_letters: String of only letters (a-z, A-Z) to be formatted.
	
	Returns:
	    String in NCBI ORIGIN format with markers and position numbers.
	"""
	# Break into groups of 10 with spaces to emulate the ORIGIN layout
	groups = [seq_letters[i : i + 10] for i in range(0, len(seq_letters), 10)]
	body = " ".join(groups)
	return f"ORIGIN\n1 {body}\n//\n"


def test_full_pipeline_with_real_preproinsulin_data(tmp_path, monkeypatch, capsys):
	"""
	End-to-end integration test using REAL human preproinsulin sequence.

	This test validates that the entire pipeline (cleaner → split_insulin →
	string-insulin → net-charge) works correctly with the actual 110 amino
	acid human preproinsulin sequence. No files are created in the repo root;
	all work happens inside tmp_path.

	Steps:
	  1. Read the real preproinsulin sequence from the project data file.
	  2. Format it as ORIGIN input (as if it came from NCBI).
	  3. Create the formatted file in tmp_path.
	  4. Change working directory to tmp_path (all file operations now happen there).
	  5. Run `clean_sequence()` to clean the input.
	  6. Run `split_insulin.split_insulin()` to split into four segments.
	  7. Import and execute string-insulin.py to compute molecular weight.
	  8. Import and execute net-charge.py to compute charge table.
	  9. Verify all outputs are correct.
	  10. After test, pytest automatically deletes tmp_path (cleanup guaranteed).

	Expected behavior:
	  - Cleaned sequence is exactly 110 lowercase letters.
	  - Four segment files are created with correct lengths (24, 30, 35, 21).
	  - Molecular weight is computed for the B + A chains (51 aa).
	  - Net charge table is generated for pH 0-14.
	  - No files remain in the repository root.
	"""

	# Step 1: Read the REAL preproinsulin sequence from the project data file
	# The project includes preproinsulin_seq.txt with the real sequence in ORIGIN format.
	# We read this to get the authentic biological data.
	project_root = Path(__file__).resolve().parents[1]
	original_file = project_root / "preproinsulin_seq.txt"
	original_content = original_file.read_text()
	
	# Step 2: Extract just the letters from the original ORIGIN-formatted file
	# The original file contains ORIGIN markers, position numbers, spaces, //, etc.
	# We extract the cleaned version (110 aa) by running it through our helper.
	import re
	data = original_content.replace("ORIGIN", "").replace("//", "")
	data = re.sub(r"[0-9\s]", "", data)
	real_seq_110 = re.sub(r"[^a-zA-Z]", "", data).lower()
	
	# Verify we got a valid 110 aa sequence
	assert len(real_seq_110) == 110, f"Real preproinsulin should be 110 aa, got {len(real_seq_110)}"
	
	# Step 3: Create a formatted ORIGIN input using the real sequence
	# This simulates what we'd receive if downloading from NCBI.
	origin_text = _make_origin_content(real_seq_110)
	
	# Step 4: Create the input file in tmp_path (NOT in repo root)
	input_file = tmp_path / "preproinsulin_seq.txt"
	input_file.write_text(origin_text)
	
	# Step 4.5: Create data directory in tmp_path for output files
	data_dir = tmp_path / "data"
	data_dir.mkdir(exist_ok=True)
	
	# Step 5: Change working directory to tmp_path
	# This is CRITICAL: all subsequent file operations (open(), read(), write())
	# that use relative paths will now happen in tmp_path, not the repo root.
	# After the test, monkeypatch automatically restores the original cwd.
	monkeypatch.chdir(tmp_path)
	
	# Step 6: Run cleaner to produce the cleaned file
	cleaned_name = "data/preproinsulin_seq_clean.txt"
	clean_sequence(str(input_file), cleaned_name)
	
	# Verify the cleaned file exists and contains the expected sequence
	cleaned_file = tmp_path / cleaned_name
	assert cleaned_file.exists(), "Cleaned file should exist in tmp_path/data"
	cleaned_content = cleaned_file.read_text().strip()
	assert len(cleaned_content) == 110, f"Cleaned sequence should be 110 aa, got {len(cleaned_content)}"
	assert cleaned_content == real_seq_110, "Cleaned sequence should match real preproinsulin"
	
	# Step 7: Run the splitter which expects the cleaned file in the cwd/data
	split_insulin.split_insulin()  # uses default CLEAN_FILE = "data/preproinsulin_seq_clean.txt"
	
	# Verify the four segment files were created in tmp_path/data with correct lengths
	ls = (tmp_path / "data" / "lsinsulin_seq_clean.txt").read_text().strip()
	b = (tmp_path / "data" / "binsulin_seq_clean.txt").read_text().strip()
	c = (tmp_path / "data" / "cinsulin_seq_clean.txt").read_text().strip()
	a = (tmp_path / "data" / "ainsulin_seq_clean.txt").read_text().strip()
	
	# Verify segment lengths
	assert len(ls) == 24, f"LS should be 24 aa, got {len(ls)}"
	assert len(b) == 30, f"B-chain should be 30 aa, got {len(b)}"
	assert len(c) == 35, f"C-peptide should be 35 aa, got {len(c)}"
	assert len(a) == 21, f"A-chain should be 21 aa, got {len(a)}"
	
	# Verify the segments reconstruct the original sequence
	reconstructed = ls + b + c + a
	assert reconstructed == real_seq_110, "Segments should reconstruct the original sequence"
	
	# Step 8: Import string-insulin.py
	# It reads the segment files at import time; all files are in tmp_path (current cwd).
	string_path = project_root / "string-insulin.py"
	spec = importlib.util.spec_from_file_location("string_insulin", str(string_path))
	string_mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(string_mod)
	
	# Verify the insulin variable (B + A)
	expected_insulin = b + a
	assert string_mod.insulin == expected_insulin, "insulin should be B + A chains"
	assert len(string_mod.insulin) == 51, "Insulin should be 51 aa"
	
	# Verify molecular weight is computed
	assert hasattr(string_mod, "molecularWeightInsulin"), "Module should compute molecular weight"
	mw = string_mod.molecularWeightInsulin
	assert mw > 5000, f"MW should be > 5000 Da, got {mw}"
	
	# Step 9: Import net-charge.py
	# It reads the segment files at import time; all files are in tmp_path (current cwd).
	net_path = project_root / "net-charge.py"
	spec2 = importlib.util.spec_from_file_location("net_charge", str(net_path))
	net_mod = importlib.util.module_from_spec(spec2)
	spec2.loader.exec_module(net_mod)
	
	# Verify the module computed seqCount (amino acid counts)
	assert hasattr(net_mod, "seqCount"), "Module should expose seqCount"
	# Verify counts are non-negative
	for aa, count in net_mod.seqCount.items():
		assert count >= 0, f"Count for {aa} should be >= 0"
	
	# Verify output was printed (capture and check)
	captured = capsys.readouterr()
	assert "pH" in captured.out, "Output should include pH table header"
	
	# Step 10: After test, monkeypatch.chdir and tmp_path are automatically cleaned
	# by pytest. No files remain in the repository root. All generated files
	# (data/preproinsulin_seq_clean.txt, data/*insulin*.txt, etc.) are deleted automatically.
