import re
import os

INPUT_FILE = "preproinsulin_seq.txt"
OUTPUT_FILE = "data/preproinsulin_seq_clean.txt"

def clean_sequence(input_file: str, output_file: str, expected_length: int | None = None) -> str:
    """
    Clean a protein sequence file in NCBI ORIGIN format.
    - Removes 'ORIGIN', '//', digits, whitespace and non-letter chars.
    - Returns the cleaned sequence as a string (lowercase).
    """
    with open(input_file, "r") as f:
        data = f.read()

    # Remove ORIGIN and end marker
    data = data.replace("ORIGIN", "").replace("//", "")

    # Remove numbers and whitespace (spaces, tabs, newlines)
    data = re.sub(r"[0-9\s]", "", data)

    # Keep only letters, convert to lowercase
    clean_seq = re.sub(r"[^a-zA-Z]", "", data).lower()

    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
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


def clean_preproinsulin():
    """Wrapper for the insulin lab so names stay consistent."""
    return clean_sequence(INPUT_FILE, OUTPUT_FILE, expected_length=110)


if __name__ == "__main__":
    clean_preproinsulin()