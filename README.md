
# Causal Provenance Tamper Detection

Detecting poisoning of system provenance graphs by validating causal consistency and identifying provenance graph tampering using semantic rules and (future) graph anomaly detection.

---

## Overview

Modern provenance-based intrusion detection systems assume the provenance graph is trustworthy. This project instead asks:

> **Has the provenance graph itself been tampered with?**

The system detects attacks that modify provenance graphs after collection, including:

- Edge deletion
- Edge insertion
- Edge reordering
- Dependency forgery

using deterministic semantic validation followed by (future) graph anomaly detection.

---

# Repository Layout

```text
src/
├── graph_construction/
│   ├── schema.py
│   ├── cdm_parser.py
│   ├── graph_loader.py
│   ├── converter.py
│   └── synthetic.py
│
├── detection/
│   ├── poisoning_injection.py
│   ├── rule_engine.py
│   ├── graph_anomaly.py
│   └── rule_based.py
│
├── eval/
│   └── metrics.py
│
tests/
scripts/
docs/
results/
data/
```

---

# Completed Components

## Dataset Processing

- Parsed DARPA Transparent Computing Engagement 3 datasets:
  - 1r
  - 3
  - 5m
  - 6r
- Normalized CDM records into provenance graphs
- Graph loader API
- DataFrame → ProvenanceGraph converter
- Dataset characterization utilities

---

## Graph Statistics

Automatically computes:

- Node count
- Edge count
- Node type distribution
- Edge type distribution
- Degree statistics

Outputs:

- `results/dataset_statistics.csv`
- `docs/dataset_statistics.md`

---

## Provenance Poisoning Framework

### Random attacks

- Random deletion
- Random insertion
- Random reordering
- Random dependency forgery

### Targeted attacks

- Targeted deletion
- Targeted insertion
- Targeted reordering
- Targeted dependency forgery

Each attack returns:

- Poisoned graph
- Ground-truth tampered edges
- Attack metadata

---

# Semantic Rule Engine

Implemented rules:

| Rule | Purpose |
|------|---------|
| DuplicateEdgeRule | Duplicate edge IDs |
| DuplicateEventRule | Duplicate provenance events |
| SpawnConsistencyRule | Process spawn validation |
| ExecutionConsistencyRule | EXECUTE semantics |
| ReadWriteConsistencyRule | READ/WRITE semantics |
| NetworkConsistencyRule | CONNECT semantics |
| DeleteConsistencyRule | DELETE semantics |
| SelfLoopRule | Invalid self-loops |
| MissingNodeRule | Missing node references |
| TimestampRule | Timestamp validation |

Current validation on benign DARPA 1r:

- Nodes: **408,320**
- Edges: **9,295,127**
- **0 rule violations**

---

# Testing

Current status:

- 43 unit tests
- All passing

Run:

```bash
python3 -m pytest -q
```

---

# Running

Run parser

```bash
python3 src/graph_construction/cdm_parser.py
```

Generate statistics

```bash
python3 scripts/dataset_statistics.py
```

Run rule engine

```bash
python3 -m scripts.run_rule_engine
```

Run tests

```bash
python3 -m pytest -q
```

---

# Current Progress

Completed

- ✅ DARPA dataset parsing
- ✅ Provenance graph schema
- ✅ Graph loader
- ✅ Graph conversion
- ✅ Dataset characterization
- ✅ Provenance poisoning framework
- ✅ Semantic rule engine
- ✅ Validation on 9M+ edge graph
- ✅ 43 passing unit tests

In progress

- Temporal consistency reasoning
- Dependency consistency reasoning
- Evaluation framework

Planned

- Graph anomaly detection
- Hybrid rule + ML detector
- Full benchmark against adaptive poisoning attacks

---

# Roadmap

1. Temporal consistency detection
2. Dependency consistency detection
3. Evaluation pipeline
4. Graph anomaly detector
5. Hybrid semantic + ML detector
6. Experimental evaluation
7. Paper preparation
