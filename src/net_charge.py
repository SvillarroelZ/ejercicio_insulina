#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculate insulin net charge across pH 0-14 using amino acid pKa values.

Demonstrates loops, dictionaries, string counting, and Henderson–Hasselbalch logic
for computing the net charge of a protein sequence at different pH values.
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


# pKa dictionary: only amino acids contributing to charge
pk_values = {
    'y': 10.07,
    'c': 8.18,
    'k': 10.53,
    'h': 6.00,
    'r': 12.48,
    'd': 3.65,
    'e': 4.25
}
 
def compute_seqcount(insulin: str) -> dict[str, float]:
    """
    Count charge-contributing amino acids in a protein sequence.
    
    Counts the occurrence of amino acids that contribute to protein charge:
    y (Tyr), c (Cys), k (Lys), h (His), r (Arg), d (Asp), e (Glu).
    
    Args:
        insulin: Protein sequence string (lowercase amino acid codes).
    
    Returns:
        Dictionary mapping amino acid codes to their float counts.
    
    Example:
        >>> counts = compute_seqcount("krhde")
        >>> counts['k']  # Count of lysine
        1.0
    """
    return {x: float(insulin.count(x)) for x in ['y','c','k','h','r','d','e']}

def print_net_charge_table(seq_count: dict[str, float]) -> None:
    """
    Print a table of pH values (0-14) and corresponding net charge.
    
    Uses the Henderson-Hasselbalch equation to calculate the net charge
    of a protein at each pH value based on amino acid composition.
    
    Args:
        seq_count: Dictionary of amino acid counts from compute_seqcount().
    
    Example:
        >>> counts = compute_seqcount("krhde")
        >>> print_net_charge_table(counts)
        pH     | net-charge
        ...
    """
    print(f"{'pH':<6} | {'net-charge':>12}")
    print("-" * 22)
    pH = 0
    while pH <= 14:
        positive = sum({
            x: ((seq_count[x] * (10 ** pk_values[x])) / ((10 ** pH) + (10 ** pk_values[x])))
            for x in ['k', 'h', 'r']
        }.values())

        negative = sum({
            x: ((seq_count[x] * (10 ** pH)) / ((10 ** pH) + (10 ** pk_values[x])))
            for x in ['y', 'c', 'd', 'e']
        }.values())

        netCharge = positive - negative
        print(f"{pH:<6.2f} | {netCharge:>12.4f}")
        pH += 1


# Global variables set during main() for test assertions
insulin = None
seq_count = None

def main(argv: list[str] | None = None) -> None:
    """
    Main entry point for net charge calculation.
    
    Loads insulin sequences, calculates amino acid composition, and prints
    a table of net charge values across pH 0-14.
    
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
    global insulin, seq_count
    _prepro, _ls, b, a, _c = _load_sequences(data_dir)
    insulin = b + a
    seq_count = compute_seqcount(insulin)
    print_net_charge_table(seq_count)

if __name__ == "__main__":
    main()