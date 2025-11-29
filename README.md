# Human Insulin Sequence Analysis and Molecular Property Calculator

[![Tests](https://img.shields.io/badge/tests-16%20passing-success)]() [![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)]() [![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()

Bioinformatics pipeline for human insulin analysis through computational sequence processing and biochemical property calculations.

**What we do:** Parse NCBI ORIGIN sequences → Split into biological segments → Calculate molecular weight → Compute pH-dependent net charge

**Why it matters:** Demonstrates production-ready bioinformatics code with 100% test coverage, modern Python practices, and scientific accuracy validated against ExPASy ProtParam.

---

## Quick Start (Complete Workflow)

```bash
# Clone and setup
git clone https://github.com/SvillarroelZ/ejercicio_insulina.git
cd ejercicio_insulina
python3 -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Execute complete pipeline
python cleaner.py && python split-insulin.py && python string-insulin.py && python net-charge.py

# Run tests with coverage
pytest test/ -v

# Clean generated files
python reset_workspace.py --force
```

**Expected output:**
- `preproinsulin_seq_clean.txt` (110 aa cleaned sequence)
- `lsinsulin_seq_clean.txt`, `binsulin_seq_clean.txt`, `ainsulin_seq_clean.txt`, `cinsulin_seq_clean.txt` (4 biological segments)
- Console: Molecular weight 5807.63 Da, pH charge table (pH 0-14)
- Tests: 16 passed, 100% coverage

---

## What This Pipeline Does

### 1. Sequence Cleaning (`cleaner.py`)
**Input:** NCBI ORIGIN format with numbers, spaces, metadata  
**Output:** Clean amino acid sequence (110 aa)  
**Why:** NCBI format is not suitable for computational analysis - we extract only the sequence data

```
# Before (NCBI format):
ORIGIN
     1 malwmrllpl lallalwgpd paaafvnqhl
    61 ...
//

# After (cleaned):
MALWMRLLPLLALLALWGPDPAAAFVNQHL...
```

### 2. Biological Segmentation (`split-insulin.py`)
**Input:** 110 aa preproinsulin sequence  
**Output:** 4 biological segments based on known cleavage sites  
**Why:** Insulin undergoes post-translational processing - we simulate this biologically accurate segmentation

| Segment | Position | Length | Biological Function |
|---------|----------|--------|---------------------|
| **Signal Peptide (LS)** | 1-24 | 24 aa | Directs protein to ER, removed during processing |
| **B-chain** | 25-54 | 30 aa | Active component of mature insulin |
| **C-peptide** | 55-89 | 35 aa | Connecting peptide, cleaved out |
| **A-chain** | 90-110 | 21 aa | Active component of mature insulin |

**Mature insulin** = B-chain + A-chain (51 aa, 5807.63 Da)

### 3. Molecular Weight Calculation (`string-insulin.py`)
**Input:** B-chain + A-chain sequences  
**Output:** Molecular weight in Daltons (Da)  
**Why:** Molecular weight is critical for drug formulation, quality control, and mass spectrometry validation

**Method:**
- Count amino acid frequencies
- Sum: MW = Σ (count × amino_acid_weight)
- Compare with experimental value (5807.63 Da from ExPASy)
- Report error percentage

### 4. pH-Dependent Net Charge (`net-charge.py`)
**Input:** Mature insulin sequence (B + A chains)  
**Output:** Net charge at pH 0-14 (table format)  
**Why:** Protein charge affects solubility, stability, and biological activity - critical for formulation development

**Method:**
- Use Henderson-Hasselbalch equation
- Calculate charge contribution from ionizable residues (K, R, D, E, H, Y, C)
- Net charge = Σ(positive charges) - Σ(negative charges)
- Estimate isoelectric point (pI) where net charge ≈ 0

---

## Scientific Background

Human insulin is synthesized as **preproinsulin** (110 amino acids), which undergoes proteolytic processing:

1. **Signal peptide cleavage** (ER translocation)
2. **Proinsulin formation** (B-C-A structure)
3. **C-peptide removal** (mature insulin: B + A chains)
4. **Disulfide bond formation** (A6-A11, A7-B7, A20-B19)

This pipeline computationally replicates steps 1-3 and calculates biophysical properties of the final product.

---

## Design Decisions & Rationale

### Why Simple Architecture?
- **Decision:** Keep all code in 4 scripts (cleaner, split-insulin, string-insulin, net-charge) without separate utils module
- **Why:** For small projects (~300 lines total), extracting shared code into utils adds complexity without benefit
- **Trade-off:** Some code duplication vs maintainability and clarity
- **Outcome:** 100% test coverage maintained, easier to understand for new contributors

### Why 100% Test Coverage?
- **Decision:** Comprehensive unit + integration tests covering all code paths
- **Why:** Bioinformatics calculations must be scientifically accurate - untested code = unvalidated science
- **Challenge:** Coverage tracking in `if __name__ == "__main__":` blocks required `runpy.run_path()` instead of `subprocess.run()`
- **Outcome:** Caught edge cases (empty sequences, wrong lengths, missing files) before production

### Why Custom Pytest Fixtures?
- **Decision:** Use `tmp_path` and `monkeypatch` for test isolation
- **Why:** Tests must not modify repository files or depend on external state
- **Outcome:** Zero side effects, tests can run in any order

### Why Python 3.10+?
- **Decision:** Use modern type hints (`str | None` instead of `Optional[str]`)
- **Why:** Cleaner, more readable, aligns with Python's direction
- **Trade-off:** Requires Python 3.10+ (acceptable for 2025 project)

---

## Testing Strategy

### Test Types
- **Unit Tests:** Isolated functions with synthetic data (zero side effects)
- **Integration Tests:** Full pipeline with real preproinsulin sequence
- **Coverage Tests:** Validate all code paths execute during test runs

### Quick Test Commands

```bash
# Run all tests with verbose output
pytest test/ -v

# Run tests with coverage report
pytest test/ --cov=. --cov-report=term-missing

# Run specific test file
pytest test/test_cleaner.py -v

# Run tests for specific function
pytest test/test_string_insulin.py::test_molecular_weight_calculation -v

# Clean generated files before testing
python reset_workspace.py --force && pytest test/ -v
```

### Coverage Summary

| Module | Coverage | Tests | Lines |
|--------|----------|-------|-------|
| `cleaner.py` | 100% | 7 | ~80 |
| `split-insulin.py` | 100% | 3 | ~60 |
| `string-insulin.py` | 100% | 2 | ~90 |
| `net-charge.py` | 100% | 2 | ~70 |
| `integration` | 100% | 2 | - |
| **Total** | **100%** | **16** | **~300** |

---

## Project Structure

```
ejercicio_insulina/
├── cleaner.py                  # NCBI ORIGIN parser
├── split-insulin.py            # Biological segmentation
├── string-insulin.py           # Molecular weight calculator
├── net-charge.py               # pH-dependent charge calculator
├── test/
│   ├── conftest.py             # Pytest configuration
│   ├── test_cleaner.py         # 7 tests, 100% coverage
│   ├── test_split_insulin.py   # 3 tests, 100% coverage
│   ├── test_string_insulin.py  # 2 tests, 100% coverage
│   ├── test_net_charge.py      # 2 tests, 100% coverage
│   ├── test_integration_pipeline.py  # 1 test, end-to-end
│   └── test_real_pipeline_validation.py  # 1 test, real data
├── preproinsulin_seq.txt       # Original NCBI sequence (tracked)
├── *_seq_clean.txt             # Generated files (gitignored)
├── requirements.txt            # pytest, pytest-cov
├── reset_workspace.py          # Cleanup utility
└── README.md
```

---

## Installation & Setup

**Prerequisites:** Python 3.10+, pip, git

```bash
# 1. Clone repository
git clone https://github.com/SvillarroelZ/ejercicio_insulina.git
cd ejercicio_insulina

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat

# 4. Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- `pytest>=9.0.0` - Testing framework
- `pytest-cov>=6.0.0` - Coverage reporting

Scripts use **only Python standard library** (no runtime dependencies).

---

## Usage Examples

### Complete Workflow (From Scratch)

```bash
# Step 1: Clean workspace
python reset_workspace.py --force

# Step 2: Clean NCBI sequence
python cleaner.py
# Output: preproinsulin_seq_clean.txt (110 aa)

# Step 3: Split into biological segments
python split-insulin.py
# Output: lsinsulin_seq_clean.txt, binsulin_seq_clean.txt, ainsulin_seq_clean.txt, cinsulin_seq_clean.txt

# Step 4: Calculate molecular weight
python string-insulin.py
# Output: Console displays MW and error %

# Step 5: Calculate pH-dependent charge
python net-charge.py
# Output: Console displays pH 0-14 vs net charge table

# Step 6: Validate with tests
pytest test/ -v
# Output: 16 passed, 100% coverage
```

### One-Line Pipeline Execution

```bash
# Execute all 4 scripts sequentially
python cleaner.py && python split-insulin.py && python string-insulin.py && python net-charge.py
```

---

## Code Quality Standards

### Type Safety
- Type hints where beneficial (modern Python 3.10+ syntax)
- Clear variable names and function signatures
- Static analysis ready (mypy, pylance)

### Documentation
- Inline comments explain complex logic (Henderson-Hasselbalch, pKa calculations)
- Function docstrings describe inputs, outputs, and purpose
- README documents design decisions and rationale

### Testing
- 100% line coverage
- Unit tests with synthetic data (isolation)
- Integration tests with real NCBI data (validation)
- Edge cases: empty sequences, wrong lengths, missing files

### Simplicity
- 4 focused scripts, single responsibility each
- Direct, readable code without over-abstraction
- No premature optimization

---

## File Management

### Tracked Files (Git)
- Scripts: `*.py` (cleaner, split-insulin, string-insulin, net-charge)
- Tests: `test/*.py`
- Config: `requirements.txt`, `.gitignore`
- Data: `preproinsulin_seq.txt` (original NCBI sequence)
- Utils: `reset_workspace.py`

### Generated Files (Gitignored)
- Sequences: `*_seq_clean.txt` (cleaned and split sequences)
- Cache: `.pytest_cache/`, `__pycache__/` (recursive)
- Coverage: `.coverage`
- Venv: `venv/`, `.venv/`

---

## Development Insights

### Key Challenges Solved

**1. Coverage Tracking in `main()` Blocks**
- **Problem:** `subprocess.run()` didn't track coverage for `if __name__ == "__main__":` blocks
- **Solution:** Use `runpy.run_path()` to execute in same process
- **Impact:** Achieved 100% coverage

**2. Test Isolation vs Real Data**
- **Problem:** Unit tests need isolation, integration tests need real NCBI data
- **Solution:** `tmp_path` fixtures for units, real files for integration
- **Impact:** Zero side effects, confidence in real-world behavior

**3. Simple vs Complex Architecture**
- **Problem:** Extract shared code to utils or keep inline?
- **Solution:** Keep inline for clarity in small project
- **Impact:** Simpler to understand and maintain

### Lessons Learned
- **Domain Knowledge:** Biology + computation requires understanding both
- **TDD Discipline:** 100% coverage prevents bugs
- **Pragmatic Design:** Simplicity > premature abstraction
- **Testing Strategy:** Synthetic + real data = speed + confidence

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `No module named pytest` | Activate venv: `source venv/bin/activate` |
| `FileNotFoundError: preproinsulin_seq_clean.txt` | Run `python cleaner.py` first |
| Virtual environment won't activate | Recreate: `python3 -m venv venv` |
| Tests fail on Windows | Check line endings (use `git config core.autocrlf input`) |

---

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/your-feature`)
3. Implement with tests (maintain 100% coverage)
4. Run tests: `pytest test/ -v`
5. Commit: `git commit -m "Add feature"`)
6. Push: `git push origin feature/your-feature`
7. Submit pull request

---

## License

Educational project for AWS re/Start Cloud Computing program

---

## Acknowledgments

- **Sequence Data:** [NCBI Protein Database](https://www.ncbi.nlm.nih.gov/protein)
- **Molecular Weights:** [ExPASy ProtParam](https://web.expasy.org/protparam/)
- **pKa Values:** Nelson & Cox, *Lehninger Principles of Biochemistry*

**Author:** SvillarroelZ  
**Repository:** [github.com/SvillarroelZ/ejercicio_insulina](https://github.com/SvillarroelZ/ejercicio_insulina)  
**Program:** AWS re/Start Cloud Computing - Generation Chile
