# Python3.6  
# Coding: utf-8  

# -------------------------------------------------------------
# This script calculates the net charge of the insulin protein 
# across pH values from 0 to 14 using amino acid pKa values.
# It demonstrates loops, dictionaries, string counting, 
# and the Henderson–Hasselbalch equation logic.
# -------------------------------------------------------------

# # Store the human preproinsulin sequence in a variable called preproinsulin:  
# preproInsulin = "malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktrreaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"  

# # Store the remaining sequence elements of human insulin in variables:  
# lsInsulin = "malwmrllpllallalwgpdpaaa"  
# bInsulin = "fvnqhlcgshlvealylvcgergffytpkt"  
# aInsulin = "giveqcctsicslyqlenycn"  
# cInsulin = "rreaedlqvgqvelgggpgagslqplalegslqkr"  
# insulin = bInsulin + aInsulin  # Combine B-chain + A-chain to form the insulin protein:

def read_file(path: str) -> str:
    """Read a sequence file and return the stripped string."""
    with open(path) as f:
        return f.read().strip()
    
preproInsulin = read_file("data/preproinsulin_seq_clean.txt")
lsInsulin = read_file("data/lsinsulin_seq_clean.txt")
bInsulin = read_file("data/binsulin_seq_clean.txt")
aInsulin = read_file("data/ainsulin_seq_clean.txt")
cInsulin = read_file("data/cinsulin_seq_clean.txt")

insulin = bInsulin + aInsulin

# pKa dictionary: only amino acids contributing to charge
pKR = {
    'y': 10.07,
    'c': 8.18,
    'k': 10.53,
    'h': 6.00,
    'r': 12.48,
    'd': 3.65,
    'e': 4.25
}
 
# Count how many of each charge-contributing amino acid are present
float(insulin.count("Y"))

seqCount = ({x: float(insulin.count(x)) for x in ['y','c','k','h','r','d','e']})
 
# Calculate net charge for pH values from 0 to 14 using a loop
pH = 0
 
# # while (pH <= 14):
# #     netCharge = (
# #     +(sum({x: ((seqCount[x]*(10**pKR[x]))/((10**pH)+(10**pKR[x]))) \
# #     for x in ['k','h','r']}.values()))
# #     -(sum({x: ((seqCount[x]*(10**pH))/((10**pH)+(10**pKR[x]))) \
# #     for x in ['y','c','d','e']}.values())))

# #     print('{0:.2f}'.format(pH), netCharge)
# #     pH +=1


# Print formatted pH and charge
print(f"{'pH':<6} | {'net-charge':>12}")
print("-" * 22)

while (pH <= 14):

    # Positive charge contributors: K, H, R
    positive = sum({
        x: ((seqCount[x] * (10 ** pKR[x])) / ((10 ** pH) + (10 ** pKR[x])))
        for x in ['k', 'h', 'r']
    }.values())

    # Negative charge contributors: Y, C, D, E
    negative = sum({
        x: ((seqCount[x] * (10 ** pH)) / ((10 ** pH) + (10 ** pKR[x])))
        for x in ['y', 'c', 'd', 'e']
    }.values())

    # Net charge = positive - negative
    netCharge = positive - negative

    
    #print('{0:.2f}'.format(pH), netCharge)
    print(f"{pH:<6.2f} | {netCharge:>12.4f}")

    # Increase pH by 1
    pH += 1