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
 
# Store the human preproinsulin sequence in a variable called preproinsulin:
preproInsulin = "malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr" \
"reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
 
# Store the remaining sequence elements of human insulin in variables:
lsInsulin = "malwmrllpllallalwgpdpaaa"      # lsInsulin stores the signal peptide (leader sequence) of preproinsulin
bInsulin = "fvnqhlcgshlvealylvcgergffytpkt"     # bInsulin stores the B-chain of human insulin
aInsulin = "giveqcctsicslyqlenycn"                  # aInsulin stores the A-chain of human insulin
cInsulin = "rreaedlqvgqvelgggpgagslqplalegslqkr"    # cInsulin stores the connecting peptide (C-peptide) sequence
insulin = bInsulin + aInsulin       # Combine B-chain and A-chain to form the processed insulin molecule:
 
# Printing "the sequence of human insulin" to console using successive print() commands:
print("The sequence of human preproinsulin:")
print(lsInsulin + bInsulin + aInsulin + cInsulin + insulin)
 
# Printing to console using concatenated strings inside the print function (one-liner):
print("nThe sequence of human insulin, chain a: " + aInsulin)
 
# Calculating the molecular weight of insulin  
# Dictionary storing molecular weights of amino acids:
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

# Multiply the count by the weights  
# Multiply count * molecular weight for each amino acid and sum it:

molecularWeightInsulin = sum(
    {
        x: (aaCountInsulin[x] * aaWeights[x])
        for x in ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
                'M', 'N', 'P', 'Q', 'R','S', 'T', 'V', 'W', 'Y']
    }.values()
)  

print("The rough molecular weight of insulin: " + str(molecularWeightInsulin))
 
molecularWeightInsulinActual = 5807.63 #6696.42

error_percentage = ((molecularWeightInsulin - molecularWeightInsulinActual)
                    / molecularWeightInsulinActual) * 100

print("Error percentage: " + str(error_percentage))