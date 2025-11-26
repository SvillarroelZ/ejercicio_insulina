#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
#
# Python Version: Python 3.10 (GitHub Codespaces)
# Executable Path: /usr/bin/python3.10

# -------------------------------------------------------------
# This script stores the human insulin sequence in variables,
# prints them to the console, and calculates the approximate 
# molecular weight using basic Python operations.
# It demonstrates variables, strings, concatenation, printing,
# dictionary usage, and simple calculations.
# -------------------------------------------------------------

# # Store the human preproinsulin sequence in a variable called preproinsulin: 
# # preproInsulin = "malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr" \ 
# # "reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn" 
#
# # Store the remaining sequence elements of human insulin in variables: 
# # lsInsulin = "malwmrllpllallalwgpdpaaa" # lsInsulin stores the signal peptide (leader sequence) of preproinsulin 
# # bInsulin = "fvnqhlcgshlvealylvcgergffytpkt" 
# # bInsulin stores the B-chain of human insulin 
# # aInsulin = "giveqcctsicslyqlenycn" # aInsulin stores the A-chain of human insulin 
# # cInsulin = "rreaedlqvgqvelgggpgagslqplalegslqkr" # cInsulin stores the connecting peptide (C-peptide) sequence 
# # insulin = bInsulin + aInsulin # Combine B-chain and A-chain to form the processed insulin molecule:

def read_file(path: str) -> str:
    """Read a sequence file and return the stripped string."""
    with open(path) as f:
        return f.read().strip()

# Load sequences from cleaned text files   
preproInsulin = read_file("preproinsulin_seq_clean.txt")
lsInsulin = read_file("lsinsulin_seq_clean.txt")
bInsulin = read_file("binsulin_seq_clean.txt")
aInsulin = read_file("ainsulin_seq_clean.txt")
cInsulin = read_file("cinsulin_seq_clean.txt")

# Combine B-chain and A-chain to form the processed insulin molecule
insulin = bInsulin + aInsulin

# -------------------------------------------------------------
# Printing sequences
# -------------------------------------------------------------
print("\nThe sequence of human preproinsulin:")
print("------------------------------------")
# Usamos las partes limpiadas; esto equivale a la preproinsulina
print(lsInsulin + bInsulin + cInsulin + aInsulin)

# One-liner using concatenated strings inside the print function (as lab asks)
print("\nThe sequence of human insulin, chain A is: ")
print("---------------------------------------")
print(aInsulin)

# -------------------------------------------------------------
# Calculating the molecular weight of insulin  
# -------------------------------------------------------------
aaWeights = {
    'A': 89.09, 'C': 121.16, 'D': 133.10, 'E': 147.13, 'F': 165.19,
    'G': 75.07, 'H': 155.16, 'I': 131.17, 'K': 146.19, 'L': 131.17,
    'M': 149.21,'N': 132.12, 'P': 115.13, 'Q': 146.15, 'R': 174.20,
    'S': 105.09, 'T': 119.12, 'V': 117.15, 'W': 204.23, 'Y': 181.19
}

# Count how many times each amino acid appears in the insulin sequence:
aaCountInsulin = {
    x: float(insulin.upper().count(x))
    for x in ['A', 'C','D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
               'M', 'N', 'P', 'Q', 'R', 'S', 'T','V', 'W', 'Y']
} 

# Multiply count * molecular weight for each amino acid and sum it
molecularWeightInsulin = sum(
    {
        x: (aaCountInsulin[x] * aaWeights[x])
        for x in ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
                  'M', 'N', 'P', 'Q', 'R','S', 'T', 'V', 'W', 'Y']
    }.values()
)  

print("\nThe rough molecular weight of insulin:")
print("--------------------------------------")
print(molecularWeightInsulin)

molecularWeightInsulinActual = 5807.63  # accepted value

error_percentage = ((molecularWeightInsulin - molecularWeightInsulinActual)
                    / molecularWeightInsulinActual) * 100

print("\nError percentage:")
print("-----------------")
print(f"{error_percentage:.2f}%")