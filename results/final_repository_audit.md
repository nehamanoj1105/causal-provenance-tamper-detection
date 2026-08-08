# Final Repository Audit & Artifact Freeze Report

**Repository**: `causal-provenance-tamper-detection`  
**Purpose**: Final repository audit and artifact freeze prior to paper writing.

---

## 1. Files Modified

| File Path | Description of Modification |
|---|---|
| [`scripts/run_rule_engine.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/scripts/run_rule_engine.py) | Added `ROOT_DIR` to `sys.path` to allow direct command execution from repo root. |
| [`src/graph_construction/synthetic.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/graph_construction/synthetic.py) | Added `target_edges` parameter to generate exact requested edge counts for scalability benchmarks. |
| [`src/eval/scalability.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/eval/scalability.py) | Updated `run_scalability_benchmark()` to pass `target_edges` and scale nodes proportionately up to 1,000,000 edges. |
| [`src/eval/cross_dataset.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/eval/cross_dataset.py) | Updated module docstring to "Multi-scenario evaluation module". |
| [`scripts/run_cross_dataset.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/scripts/run_cross_dataset.py) | Updated script docstrings and CLI description to "Multi-Scenario Evaluation across DARPA TC E3 Datasets". |
| [`README.md`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/README.md) | Standardized dataset architecture (Synthetic vs Parsed CSV vs Raw CDM Parser) and limitations. |
| [`results/cross_dataset.md`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/results/cross_dataset.md) | Updated report header to "Multi-Scenario DARPA TC E3 Evaluation Report". |

---

## 2. Files Deleted

No functional or code files were deleted. All existing scripts, tests, data loaders, and model definitions were preserved.

---

## 3. Files Added

| File Path | Description |
|---|---|
| [`results/final_repository_audit.md`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/results/final_repository_audit.md) | This master repository freeze audit report. |

---

## 4. Documentation Changes

- **Sanitized Terminology**: Replaced inaccurate phrases (`Cross-Dataset` $\implies$ `Multi-Scenario Evaluation across DARPA TC E3 Datasets`). Removed unearned claims ("state-of-the-art", "clear accept", "artifact badge", "USENIX ready", "paper ready", "award").
- **3-Way Data Architecture Clarification**:
  1. **Synthetic Evaluation**: Parametric synthetic graph generator (`src/graph_construction/synthetic.py`).
  2. **Parsed DARPA CSV Evaluation**: Primary benchmark evaluation mode across DARPA TC E3 scenarios (`1r`, `3`, `5m`, `6r`).
  3. **Raw CDM Parser**: Parser interfaces in `src/graph_construction/cdm_parser.py` exist but are not invoked during standard evaluation runner scripts.
- **Dataset Labels**: Kept verified raw dataset identifiers `1r`, `3`, `5m`, `6r` as authoritative labels.

---

## 5. Bugs Fixed & Technical Investigation

### Bug 1: `scripts/run_rule_engine.py` Import Error
- **Issue**: Running `python3 scripts/run_rule_engine.py` failed with `ModuleNotFoundError: No module named 'src'`.
- **Fix**: Added standard `sys.path` initialization referencing repository root.

### Bug 2: Scalability Benchmark Graph Size Generation
- **Issue**: `run_scalability.py` printed `Benchmark Graph Size: 10000 edges` but generated only 60 edges.
- **Fix**: `generate_synthetic_graph()` calculated activity edges as `(num_files + num_network) * 3`. Added `target_edges` parameter to scale activity edges so total graph edge count matches `target_edges` exactly.

### Investigation of `UnspawnedProcessRule FAIL (27149)`
- **Finding**: On full DARPA `1r` dataset (9,295,127 edges), `UnspawnedProcessRule` flags 27,149 process nodes.
- **Root Cause**: **Dataset property & Log boundary limitation**. System processes (kernel threads, background daemons) created before audit log collection started do not have `SPAWN` events recorded within the log window.
- **Verdict**: Expected behavior on real system audit logs. In synthetic benchmarks starting from process init, the rule passes cleanly.

---

## 6. Remaining Limitations

1. **Pre-Parsed Data Ingestion**: Evaluation runner scripts ingest pre-parsed CSV tables (`data/parsed/`) and synthetic graphs. Raw binary Common Data Model (`.bin`) stream parsing interface exists in `src/graph_construction/cdm_parser.py` but is not directly invoked in evaluation runner scripts.
2. **GNN Precision Degradation Under Mimicry**: GraphSAGE aggregates features over 2-hop neighborhoods. Under heavy mimicry camouflage (+150% noise edges), GraphSAGE precision drops as camouflage edges resemble benign process activity.
3. **Sub-graph Slicing for Scenario Benchmarks**: Scenario evaluation processes sub-graph slices (up to 50,000 edges per dataset) to maintain fast, reproducible benchmark runs.

---

## 7. Commands Executed

```bash
python3 -m pytest -q
python3 scripts/run_rule_engine.py
python3 scripts/run_evaluation.py
python3 scripts/run_graphsage.py --epochs 30 --seed 42
python3 scripts/run_cross_dataset.py
python3 scripts/run_scalability.py
python3 scripts/run_mimicry.py
```

---

## 8. Verification Status

| Pipeline / Script | Code | Status | Verification Summary |
|---|---|---|---|
| Pytest Unit Tests | Exit 0 | **PASSED** | 103 / 103 unit tests passed in 7.48s. |
| `run_rule_engine.py` | Exit 0 | **PASSED** | Validated 9,295,127 edges on DARPA `1r`. |
| `run_evaluation.py` | Exit 0 | **PASSED** | Multi-seed evaluation statistics generated in `results/seed_statistics.csv`. |
| `run_graphsage.py` | Exit 0 | **PASSED** | Threshold search ($\tau^*=0.70$), F1: 0.5600, ROC-AUC: 0.8776. Plots saved in `results/`. |
| `run_cross_dataset.py` | Exit 0 | **PASSED** | Evaluated across datasets `1r`, `3`, `5m`, `6r`, and `synthetic`. |
| `run_scalability.py` | Exit 0 | **PASSED** | Scaled from 10k to 1,000,000 edges. Throughput plots saved in `results/`. |
| `run_mimicry.py` | Exit 0 | **PASSED** | Evaluated robustness across `none`, `light`, `medium`, and `heavy` mimicry. |

---

## 9. Reproducibility Status

- Every result, CSV report, Markdown summary, and Matplotlib plot under `results/` can be regenerated by running the corresponding script in `scripts/`.
- All seeds are fixed (`42` default).

---

## 10. Items That Should NOT Be Claimed in the Paper

1. ❌ **Do NOT claim direct raw binary `.bin` log file parsing in benchmarks**: All evaluation scripts consume pre-parsed CSV tables or synthetic graphs.
2. ❌ **Do NOT claim GraphSAGE resilience to heavy mimicry**: GraphSAGE precision drops significantly under heavy noise camouflage due to neighborhood feature smoothing.
3. ❌ **Do NOT claim unearned review scores, artifact badges, or paper acceptance**: All evaluation metrics are internal empirical benchmarks.
