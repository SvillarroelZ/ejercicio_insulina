#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean protein sequence files in NCBI ORIGIN format.

Removes ORIGIN markers, position numbers, whitespace, and non-letter characters
from NCBI sequence files, producing clean amino acid sequences.
"""

import re

from pathlib import Path

# Use absolute path relative to this script's location
_SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = str(_SCRIPT_DIR.parent / "preproinsulin_seq.txt")  # Input from repository root
OUTPUT_FILE = str(_SCRIPT_DIR.parent / "data" / "preproinsulin_seq_clean.txt")  # Output to data/

def clean_sequence(input_file: str, output_file: str, expected_length: int | None = None) -> str:
    """
    Clean a protein sequence file in NCBI ORIGIN format.
    
    Removes 'ORIGIN' and '//' markers, digits, whitespace and non-letter chars.
    Converts result to lowercase and writes to output file.
    
    Args:
        input_file: Path to input file containing NCBI ORIGIN format sequence.
        output_file: Path where cleaned sequence will be written.
        expected_length: Optional expected length in amino acids. If provided,
            prints OK or WARNING message comparing actual to expected length.
    
    Returns:
        The cleaned sequence as a lowercase string.
    
    Raises:
        FileNotFoundError: If input_file does not exist.
        IOError: If files cannot be read or written.
    
    Example:
        >>> clean_seq = clean_sequence("raw.txt", "clean.txt", expected_length=110)
        Clean file created: clean.txt
        Final length: 110 characters
        Length OK: 110 amino acids.
    """
    with open(input_file, "r") as f:
        data = f.read()

    # Remove ORIGIN and end marker
    data = data.replace("ORIGIN", "").replace("//", "")

    # Remove numbers and whitespace (spaces, tabs, newlines)
    data = re.sub(r"[0-9\s]", "", data)

    # Keep only letters, convert to lowercase
    clean_seq = re.sub(r"[^a-zA-Z]", "", data).lower()

    with open(output_file, "w") as f:
        f.write(clean_seq)

    print(f"Clean file created: {output_file}")
    print(f"Final length: {len(clean_seq)} characters")

    if expected_length is not None:
        if len(clean_seq) == expected_length:
            print(f"Length OK: {expected_length} amino acids.")
        else:
            print(f"WARNING: expected {expected_length}, got {len(clean_seq)}.")

    return clean_seq


def clean_preproinsulin() -> str:
    """
    Wrapper function for cleaning the preproinsulin sequence.
    
    Cleans the default input file (preproinsulin_seq.txt) and writes
    to the default output location (data/preproinsulin_seq_clean.txt).
    Expects exactly 110 amino acids.
    
    Returns:
        The cleaned sequence as a lowercase string.
    
    Example:
        >>> clean_seq = clean_preproinsulin()
        Clean file created: data/preproinsulin_seq_clean.txt
        Final length: 110 characters
        Length OK: 110 amino acids.
    """
    return clean_sequence(INPUT_FILE, OUTPUT_FILE, expected_length=110)


if __name__ == "__main__":
    clean_preproinsulin()