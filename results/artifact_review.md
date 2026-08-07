# USENIX Security Artifact Evaluation Review Report

**Evaluator**: USENIX Security Artifact Evaluation Committee  
**Artifact Repository**: `causal-provenance-tamper-detection`  
**Badge Recommendation**: **Artifacts Evaluated - Functional & Reproducible**  

---

## 1. Artifact Structure & Organization Audit

```
causal-provenance-tamper-detection/
├── data/                       # Raw DARPA TC E3 & Synthetic Data
├── results/                    # Generated Reports, CSVs & Matplotlib Figures
│   ├── precision_recall_curve.png
│   ├── roc_curve.png
│   ├── prediction_histogram.png
│   ├── runtime_vs_edges.png
│   ├── memory_vs_edges.png
│   ├── throughput_vs_edges.png
│   ├── robustness_curve.png
│   └── *.csv / *.md
├── scripts/                    # Clean Master CLI Runners
│   ├── run_evaluation.py
│   ├── run_graphsage.py
│   ├── run_cross_dataset.py
│   ├── run_scalability.py
│   └── run_mimicry.py
├── src/                        # Core Library Implementation
│   ├── parsers/
│   ├── graph_construction/
│   ├── detection/
│   ├── ml/
│   └── eval/
├── tests/                      # Automated Pytest Suite (103 Unit Tests)
├── README.md                   # Setup & Execution Documentation
└── requirements.txt            # Dependencies
```

---

## 2. Reproduction Verification Matrix

| Claim / Figure | Generating Command | Output Verification | Badge Criteria |
|---|---|---|---|
| **Phase 6 Multi-Seed Stats** | `python3 scripts/run_evaluation.py` | `results/seed_statistics.csv` | PASSED |
| **GraphSAGE Curves & Histograms** | `python3 scripts/run_graphsage.py` | `results/precision_recall_curve.png` | PASSED |
| **Cross-Dataset Benchmark** | `python3 scripts/run_cross_dataset.py` | `results/cross_dataset.csv` | PASSED |
| **Scalability & Memory Plots** | `python3 scripts/run_scalability.py` | `results/runtime_vs_edges.png` | PASSED |
| **Mimicry Robustness Curves** | `python3 scripts/run_mimicry.py` | `results/robustness_curve.png` | PASSED |
| **Full Unit Test Suite** | `python3 -m pytest -q` | 103 / 103 Tests Passed | PASSED |

---

**Conclusion**: Another researcher can clone this repository, install requirements, run 5 standalone scripts, and reproduce every single table, CSV report, and Matplotlib figure.
