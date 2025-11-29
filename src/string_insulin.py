#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compute insulin molecular weight with configurable data directory.

Calculates the molecular weight of insulin and its components using amino acid
weights and compares the result with the known experimental value.
"""

import argparse
import os
from pathlib import Path


# Private helper functions for file I/O and data directory management
def _get_data_dir(cli_dir: str | None = None) -> Path:
    """Get data directory with priority: CLI arg > env var > default."""
    # Priority 1: CLI argument (--data-dir flag)
    if cli_dir:
        return Path(cli_dir)
    # Priority 2: Environment variable (INSULIN_DATA_DIR)
    env_dir = os.getenv("INSULIN_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    # Priority 3: Default (project_root/data/)
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent / "data"


def _read_file(path: Path) -> str:
    """Read text file and return stripped content."""
    with open(path) as f:
        return f.read().strip()


def _load_sequences(data_dir: Path) -> tuple[str, str, str, str, str]:
    """Load all five insulin sequence files from data directory."""
    # Read preproinsulin (110 aa) and segmented chains
    prepro = _read_file(data_dir / "preproinsulin_seq_clean.txt")
    ls = _read_file(data_dir / "lsinsulin_seq_clean.txt")
    b = _read_file(data_dir / "binsulin_seq_clean.txt")
    a = _read_file(data_dir / "ainsulin_seq_clean.txt")
    c = _read_file(data_dir / "cinsulin_seq_clean.txt")
    return prepro, ls, b, a, c


# Amino acid weights (Da)
aa_weights = {
    'A': 89.09, 'C': 121.16, 'D': 133.10, 'E': 147.13, 'F': 165.19,
    'G': 75.07, 'H': 155.16, 'I': 131.17, 'K': 146.19, 'L': 131.17,
    'M': 149.21,'N': 132.12, 'P': 115.13, 'Q': 146.15, 'R': 174.20,
    'S': 105.09, 'T': 119.12, 'V': 117.15, 'W': 204.23, 'Y': 181.19
}

def count_amino_acids(seq: str) -> dict[str, float]:
    """
    Count uppercase amino acids in a sequence for molecular weight calculation.
    
    Args:
        seq: Protein sequence string (will be converted to uppercase).
    
    Returns:
        Dictionary mapping amino acid codes to their float counts.
    
    Example:
        >>> counts = count_amino_acids("malw")
        >>> counts['M']  # Count of methionine
        1.0
    """
    return {
        x: float(seq.upper().count(x))
        for x in ['A', 'C','D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
                   'M', 'N', 'P', 'Q', 'R', 'S', 'T','V', 'W', 'Y']
    }

def molecular_weight(seq: str) -> float:
    """
    Calculate the rough molecular weight of a protein sequence.
    
    Sums the molecular weights of individual amino acids.
    Note: This is a simplified calculation that doesn't account for
    peptide bonds, post-translational modifications, or disulfide bridges.
    
    Args:
        seq: Protein sequence string.
    
    Returns:
        Molecular weight in Daltons (Da).
    
    Example:
        >>> mw = molecular_weight("MALW")
        >>> print(f"{mw:.2f} Da")
    """
    counts = count_amino_acids(seq)
    return sum({x: (counts[x] * aa_weights[x])
                for x in ['A','C','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','V','W','Y']}.values())

# Global variables set during main() for test assertions
prepro_insulin = None
ls_insulin = None
b_insulin = None
a_insulin = None
c_insulin = None
insulin = None
molecular_weight_insulin = None
error_percentage = None

def main(argv: list[str] | None = None) -> None:
    """
    Main entry point for molecular weight calculation.
    
    Loads insulin sequences, calculates molecular weight, and compares
    with the known experimental value (5807.63 Da).
    
    Args:
        argv: Optional command-line arguments. If None, uses sys.argv.
    
    Example:
        >>> main()  # Uses default data directory
        >>> main(["--data-dir", "/custom/path"])  # Custom directory
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data-dir", dest="data_dir", default=None)
    args, _ = parser.parse_known_args(argv)

    data_dir = _get_data_dir(args.data_dir)
    global prepro_insulin, ls_insulin, b_insulin, a_insulin, c_insulin, insulin, molecular_weight_insulin, error_percentage
    prepro_insulin, ls_insulin, b_insulin, a_insulin, c_insulin = _load_sequences(data_dir)

    insulin = b_insulin + a_insulin

    print("\nThe sequence of human preproinsulin:")
    print("------------------------------------")
    print(ls_insulin + b_insulin + c_insulin + a_insulin)

    print("\nThe sequence of human insulin, chain A is: ")
    print("---------------------------------------")
    print(a_insulin)

    molecular_weight_insulin = molecular_weight(insulin)
    print("\nThe rough molecular weight of insulin:")
    print("--------------------------------------")
    print(molecular_weight_insulin)

    molecular_weight_insulin_actual = 5807.63
    error_percentage = ((molecular_weight_insulin - molecular_weight_insulin_actual) / molecular_weight_insulin_actual) * 100
    print("\nError percentage:")
    print("-----------------")
    print(f"{error_percentage:.2f}%")

if __name__ == "__main__":
    main()