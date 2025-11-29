#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Split cleaned preproinsulin sequence (110 aa) into four biological segments.

Segments:
- LS (signal peptide): positions 1-24 (24 aa)
- B (B-chain): positions 25-54 (30 aa)  
- C (C-peptide): positions 55-89 (35 aa)
- A (A-chain): positions 90-110 (21 aa)

Output: Writes four files in data/ directory for downstream processing.
"""

from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DATA_DIR = _SCRIPT_DIR.parent / "data"

CLEAN_FILE = str(_DATA_DIR / "preproinsulin_seq_clean.txt")


def split_insulin(clean_file: str = CLEAN_FILE, write_files: bool = True) -> tuple[str, ...] | tuple[()]:
    """
    Read a cleaned preproinsulin sequence and split it into four biological segments.
    
    The function validates that the input sequence is exactly 110 amino acids,
    then splits it according to the biological structure of human preproinsulin:
    - LS (signal peptide): 24 aa
    - B-chain: 30 aa
    - C-peptide: 35 aa
    - A-chain: 21 aa
    
    Args:
        clean_file: Path to cleaned preproinsulin sequence (plain letters).
        write_files: If True (default), write the four segment files to disk.
    
    Returns:
        tuple: (ls_seq, b_seq, c_seq, a_seq) when input length is 110.
        tuple: Empty tuple () when input length is not 110 (error case).
    
    Example:
        >>> ls, b, c, a = split_insulin()  # Uses default file, writes output
        Input length received: 110 amino acids
        Generated files:
        lsinsulin_seq_clean.txt → 24 characters (expected: 24)
        ...
        
        >>> segments = split_insulin(write_files=False)  # Test mode, no files
    
    Note:
        The function preserves CLI behavior (writing files and printing)
        when write_files=True. Setting write_files=False makes it test-friendly
        (no filesystem side effects) while still returning computed segments.
    """

    # Read the cleaned sequence from file
    with open(clean_file, "r") as f:
        seq = f.read().strip()

    print(f"Input length received: {len(seq)} amino acids")

    # Validate expected length for human preproinsulin
    if len(seq) != 110:
        print("ERROR: Sequence length is NOT 110. Check your cleaned file.")
        return tuple()

    # ---------------------------------------------------------
    # Segment boundaries according to the lab specification
    # ---------------------------------------------------------
    ls_seq = seq[0:24]     # aa 1-24  → 24 aa
    b_seq  = seq[24:54]    # aa 25-54 → 30 aa
    c_seq  = seq[54:89]    # aa 55-89 → 35 aa
    a_seq  = seq[89:110]   # aa 90-110 → 21 aa

    # Optionally write each segment to its corresponding file in data/
    if write_files:
        with open(str(_DATA_DIR / "lsinsulin_seq_clean.txt"), "w") as f:
            f.write(ls_seq)

        with open(str(_DATA_DIR / "binsulin_seq_clean.txt"), "w") as f:
            f.write(b_seq)

        with open(str(_DATA_DIR / "cinsulin_seq_clean.txt"), "w") as f:
            f.write(c_seq)

        with open(str(_DATA_DIR / "ainsulin_seq_clean.txt"), "w") as f:
            f.write(a_seq)

        # Verification summary (kept for CLI compatibility)
        print("\nGenerated files:")
        print(f"lsinsulin_seq_clean.txt → {len(ls_seq)} characters (expected: 24)")
        print(f"binsulin_seq_clean.txt  → {len(b_seq)} characters (expected: 30)")
        print(f"cinsulin_seq_clean.txt  → {len(c_seq)} characters (expected: 35)")
        print(f"ainsulin_seq_clean.txt  → {len(a_seq)} characters (expected: 21)")

    return (ls_seq, b_seq, c_seq, a_seq)


# Auto-run when executed directly
if __name__ == "__main__":
    split_insulin()
