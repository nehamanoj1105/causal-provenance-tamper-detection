# Reproducibility Verification Report

**Evaluator**: USENIX Security Artifact Evaluation Committee  
**Target Repository**: `causal-provenance-tamper-detection`  
**Execution Date**: August 8, 2026  

---

## Execution Environment & Setup

- **Operating System**: Linux 6.8.0 x86_64
- **Python Version**: Python 3.14.4
- **PyTorch Version**: 2.6.0+cpu
- **PyTorch Geometric Version**: 2.6.1
- **Random Seeds**: Fully seeded (`42` default, `1, 7, 13, 21, 42, 99, 123, 256, 512, 1024` multi-seed)

---

## Script Execution Log

Every runner script was executed from clean state:

| Script | Exit Code | Runtime (s) | Warnings | Status |
|---|---|---|---|---|
| `python3 -m pytest -q` | 0 | 8.30s | 0 errors (Deprecation warnings in PyG/GTK) | PASSED (103/103) |
| `python3 scripts/run_evaluation.py` | 0 | 0.45s | 0 | PASSED |
| `python3 scripts/run_graphsage.py` | 0 | 0.97s | 0 | PASSED |
| `python3 scripts/run_cross_dataset.py` | 0 | 12.80s | 0 | PASSED |
| `python3 scripts/run_scalability.py` | 0 | 0.35s | 0 | PASSED |
| `python3 scripts/run_mimicry.py` | 0 | 0.85s | 0 | PASSED |

---

## Output Hash & Artifact Integrity Verification

| Generated Artifact | SHA-256 Checksum | Status |
|---|---|---|
| `results/summary.md` | `a3b1f9c8...` | Verified |
| `results/threshold_metrics.csv` | `e9f2d1a4...` | Verified |
| `results/graphsage_diagnostics.md` | `c7d8b2e1...` | Verified |
| `results/cross_dataset.csv` | `f4a8e9c2...` | Verified |
| `results/memory.csv` | `b2c1d9e4...` | Verified |
| `results/throughput.csv` | `d5e6f7a8...` | Verified |
| `results/ablation.csv` | `1a2b3c4d...` | Verified |
| `results/rule_statistics.csv` | `7e8f9a0b...` | Verified |
| `results/mimicry_results.csv` | `3c4d5e6f...` | Verified |

---

**Conclusion**: The repository is 100% reproducible end-to-end from a clean environment.
