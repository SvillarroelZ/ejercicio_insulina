#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
This script reads a cleaned preproinsulin sequence (110 amino acids)
and splits it into four biologically known segments:

1. LS (Leader Sequence)    → amino acids 1-24
2. B-chain                  → amino acids 25-54
3. C-peptide                → amino acids 55-89
4. A-chain                  → amino acids 90-110

The output is written into four separate files, maintaining consistent
file names for downstream scripts such as string-insulin.py.
"""

CLEAN_FILE = "preproinsulin_seq_clean.txt"


def split_insulin(clean_file: str = CLEAN_FILE, write_files: bool = True):
    """
    Read a cleaned sequence and split it into LS, B, C and A segments.

    Parameters:
      - clean_file: path to the cleaned preproinsulin sequence (plain letters).
      - write_files: if True (default) write the four segment files to disk.

    Returns:
      - A tuple (ls_seq, b_seq, c_seq, a_seq) when the input length is 110.
      - An empty tuple when the input length is not 110 (error case).

    The function preserves the original CLI behavior (writing files and printing)
    when `write_files` is True. Setting `write_files=False` makes the function
    test-friendly (no filesystem side effects) while still returning the
    computed segments for assertions.
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

    # Optionally write each segment to its corresponding file
    if write_files:
        with open("lsinsulin_seq_clean.txt", "w") as f:
            f.write(ls_seq)

        with open("binsulin_seq_clean.txt", "w") as f:
            f.write(b_seq)

        with open("cinsulin_seq_clean.txt", "w") as f:
            f.write(c_seq)

        with open("ainsulin_seq_clean.txt", "w") as f:
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
