# Causal Provenance Graph Tamper Detection Framework

A framework for validating causal consistency and detecting provenance graph tampering on DARPA Transparent Computing Engagement 3 datasets and synthetic provenance graphs using deterministic semantic rules and a GraphSAGE baseline.

---

## Overview

Modern provenance-based intrusion detection systems (PIDS) assume that collected system provenance graphs are trustworthy. This project investigates:

> **Has the provenance graph itself been tampered with?**

The framework evaluates detection resilience against post-collection provenance attacks:
- **Edge Deletion** (erasing causal log events)
- **Edge Insertion** (fabricating unperformed system actions)
- **Edge Reordering** (shifting event timestamps out of true causal order)
- **Dependency Forgery** (re-attributing actions to different actors)
- **Adversarial Mimicry** (camouflaging poisoning within statistical background noise)

---

## Repository Structure

```text
src/
├── graph_construction/
│   ├── schema.py         # ProvenanceGraph, ProvenanceNode, ProvenanceEdge data model
│   ├── cdm_parser.py     # Parser interfaces
│   ├── graph_loader.py   # Data loader for parsed DARPA CSV scenarios
│   ├── converter.py      # DataFrame to ProvenanceGraph schema converter
│   └── synthetic.py      # Synthetic provenance graph generator
│
├── detection/
│   ├── poisoning_injection.py  # Random & targeted poisoning attack suite
│   ├── mimicry_attack.py       # Adversarial mimicry attack generator & camouflage
│   ├── rule_engine.py          # 15 deterministic semantic validation rules
│   └── rule_based.py           # Rule engine entrypoints
│
├── ml/
│   ├── dataset.py        # ProvenanceGraph to PyTorch Geometric Data converter
│   ├── graphsage.py      # 2-Layer GraphSAGE architecture & edge predictor
│   ├── train.py          # FocalLoss, weighted BCE training & threshold search
│   ├── predict.py        # Edge & node tamper prediction
│   ├── metrics.py        # ROC, PR curves, threshold sweep & calibration stats
│   └── utils.py          # PyTorch device & random seed management
│
├── eval/
│   ├── metrics.py        # Evaluation metrics (Precision, Recall, F1, MCC, AP)
│   ├── confusion_matrix.py # Confusion matrix calculations
│   ├── evaluator.py      # Ground-truth comparison engine
│   ├── report.py         # CSV & Markdown report generators
│   ├── cross_dataset.py  # Cross-scenario evaluation across DARPA datasets
│   ├── scalability.py    # Runtime, RSS/peak memory & throughput benchmarking
│   ├── ablation.py       # Rule ablation study & per-rule statistics
│   └── robustness.py     # Adversarial mimicry robustness evaluation
│
scripts/
├── run_evaluation.py     # Executes multi-seed rule engine evaluation
├── run_graphsage.py      # Trains GraphSAGE & generates ROC/PR curves
├── run_cross_dataset.py  # Executes cross-scenario evaluation across DARPA datasets
├── run_scalability.py    # Runs scalability, memory & throughput benchmarks
└── run_mimicry.py        # Evaluates detector robustness under mimicry attacks

tests/                    # 103 unit tests covering all components
results/                  # Generated CSV reports, Markdown summary tables & plots
```

---

## Implementation Status

### Implemented

- ✅ **Provenance Graph Data Model**: Node (`process`, `file`, `user`, `network`) and Edge (`read`, `write`, `execute`, `connect`, `spawn`, `delete`) schemas in [`src/graph_construction/schema.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/graph_construction/schema.py).
- ✅ **DARPA Scenario Support**: Pre-parsed DARPA TC E3 scenarios (`1r`, `3`, `5m`, `6r`) loaded via [`src/graph_construction/graph_loader.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/graph_construction/graph_loader.py).
- ✅ **Synthetic Graph Generator**: Parametric provenance graph generator in [`src/graph_construction/synthetic.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/graph_construction/synthetic.py).
- ✅ **Poisoning Attack Suite**: 4 random attack vectors and 4 targeted attack vectors in [`src/detection/poisoning_injection.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/detection/poisoning_injection.py).
- ✅ **Adversarial Mimicry Generator**: Realistic camouflage noise injection preserving degree, type, and timestamp distributions in [`src/detection/mimicry_attack.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/detection/mimicry_attack.py).
- ✅ **Semantic Rule Engine**: 15 deterministic semantic rules in [`src/detection/rule_engine.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/detection/rule_engine.py).
- ✅ **Evaluation Framework**: 13 evaluation metrics (Precision, Recall, F1, Accuracy, Specificity, FPR, FNR, Balanced Accuracy, MCC, AP, ROC-AUC, PR-AUC) in [`src/eval/metrics.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/eval/metrics.py).
- ✅ **GraphSAGE Baseline**: PyTorch Geometric implementation with class-imbalance loss weighting and threshold optimization in [`src/ml/`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/ml/).
- ✅ **Scalability Benchmarking**: Runtime, RSS/peak memory, and throughput ($\text{Edges / Second}$) profiling up to 1,000,000 edges in [`src/eval/scalability.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/eval/scalability.py).
- ✅ **Rule Ablation & Rule Statistics**: Category removal, leave-one-out ablation, and per-rule violation tracking in [`src/eval/ablation.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/eval/ablation.py).
- ✅ **Detector Robustness Benchmarking**: Evaluates Rule Engine and GraphSAGE under `none`, `light`, `medium`, and `heavy` mimicry strengths in [`src/eval/robustness.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/eval/robustness.py).
- ✅ **Multi-Scenario Evaluation**: Automated evaluation across DARPA datasets (`1r`, `3`, `5m`, `6r`) and `synthetic` in [`src/eval/cross_dataset.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/eval/cross_dataset.py).
- ✅ **Unit Test Suite**: 103 unit tests passing via `pytest`.

### In Progress

- 🔄 Fine-grained microsecond temporal sequence window tuning for online provenance log streams.

### Future Work

- 🔮 Direct binary Common Data Model (`.bin`) raw log stream ingestion parser.
- 🔮 Joint hybrid inference architecture combining GNN embeddings with deterministic rule violation constraints.

---

## Implemented Semantic Rules

The Semantic Rule Engine implements 15 rules categorized into structural, temporal, and semantic invariants:

| # | Rule Class Name | Category | Primary Invariant Checked |
|---|---|---|---|
| 1 | `DuplicateEdgeRule` | Structural | Identifies duplicate edge tuples |
| 2 | `DuplicateEventRule` | Structural | Identifies duplicate event IDs |
| 3 | `SpawnConsistencyRule` | Semantic | Validates `SPAWN` edges target `process` nodes |
| 4 | `ExecutionConsistencyRule` | Semantic | Validates `EXECUTE` edges target `file` nodes |
| 5 | `ReadWriteConsistencyRule` | Semantic | Validates `READ`/`WRITE` edges target `file` nodes |
| 6 | `NetworkConsistencyRule` | Semantic | Validates `CONNECT` edges target `network` endpoints |
| 7 | `DeleteConsistencyRule` | Semantic | Validates `DELETE` edges target `file` nodes |
| 8 | `SelfLoopRule` | Structural | Flags invalid self-referential edges |
| 9 | `MissingNodeRule` | Structural | Flags edges referencing non-existent nodes |
| 10 | `TimestampRule` | Temporal | Validates non-negative Unix epoch timestamps |
| 11 | `UnspawnedProcessRule` | Structural | Detects active processes missing parent `SPAWN` edges |
| 12 | `SequenceGapRule` | Structural | Identifies missing event sequence indices |
| 13 | `ParentChildTemporalRule` | Temporal | Ensures child spawn timestamp succeeds parent spawn |
| 14 | `ProcessActivityTemporalRule` | Temporal | Ensures process activity succeeds process spawn |
| 15 | `SequenceMonotonicityRule` | Temporal | Detects timestamp inversions in process streams |

---

## Execution Instructions

### 1. Run Unit Test Suite
```bash
python3 -m pytest -q
```

### 2. Run Semantic Rule Engine Multi-Seed Evaluation
```bash
python3 scripts/run_evaluation.py
```

### 3. Run GraphSAGE Training, Threshold Sweep & Plot Generation
```bash
python3 scripts/run_graphsage.py --epochs 30 --seed 42
```

### 4. Run Multi-Scenario DARPA Evaluation
```bash
python3 scripts/run_cross_dataset.py
```

### 5. Run Scalability, Memory & Throughput Benchmarking
```bash
python3 scripts/run_scalability.py
```

### 6. Run Adversarial Mimicry Robustness Evaluation
```bash
python3 scripts/run_mimicry.py
```

---

## Dataset & Evaluation Architecture

The framework supports three distinct data ingestion and evaluation modes:

1. **Synthetic Evaluation**: Fast, reproducible evaluation on parametrically generated synthetic provenance graphs ([`src/graph_construction/synthetic.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/graph_construction/synthetic.py)).
2. **Parsed DARPA CSV Evaluation**: The primary benchmark evaluation mode across DARPA TC E3 scenarios (`1r` Trace, `3` CADETS, `5m` ClearScope, `6r` THEIA) using pre-parsed node/edge CSV tables ([`src/graph_construction/graph_loader.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/graph_construction/graph_loader.py)).
3. **Raw CDM Parser**: Parser interfaces for raw binary Common Data Model (`.bin`) stream files exist in [`src/graph_construction/cdm_parser.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/graph_construction/cdm_parser.py), but raw binary ingestion is **not** part of the reported evaluation execution scripts.

---

## Current Framework Limitations

1. **Evaluation Data Source**: Reported benchmarks execute on pre-parsed DARPA TC E3 CSV tables (`data/parsed/`) and synthetic graphs. Raw binary CDM (`.bin`) stream parsing interface exists in `src/graph_construction/cdm_parser.py` but is not invoked during standard evaluation runner scripts.
2. **GNN Precision Under Heavy Mimicry Noise**: GraphSAGE aggregates features over 2-hop neighborhoods, which smooths node representations. Under heavy mimicry camouflage (+150% noise edges), GraphSAGE precision degrades as noise edges resemble benign process interactions.
3. **Sub-graph Slicing for Benchmarks**: Evaluation across multiple DARPA TC E3 scenarios processes sub-graph slices (up to 50,000 edges) to maintain reproducible execution times.

