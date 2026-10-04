# Repository Audit (Phase 1)

**Repository:** `causal-provenance-tamper-detection`
**Remote:** https://github.com/nehamanoj1105/causal-provenance-tamper-detection
**Commit SHA:** `d8b8617c4478846ace3b82dbd9fb819c8e2f6a64`
**Commit date:** 2026-08-09 01:34:27 +0530 (`Update README.md`)
**Shallow clone:** yes (grafted, single commit)

## 1. Environment

| Item | Value |
|---|---|
| OS | Linux 6.8.0-1055-gke x86_64 (glibc 2.41) |
| Python | 3.13.15 |
| PyTorch | 2.14.1+cpu |
| PyTorch Geometric | 2.8.0.post1 |
| scikit-learn | 1.9.1 |
| numpy | 2.5.3 |
| pandas | 3.0.6 |
| networkx | 3.7 |
| matplotlib | 3.11.2 |
| psutil | 7.2.2 |
| scipy | 1.18.1 |
| fastavro | 1.12.2 |
| CPU | 4 vCPU |
| GPU | none (`cuda_available=false`) |
| RAM | 15 GiB total (≈13 GiB available) |

Full machine-readable record: `audit/original_reproduction/env/environment.json`.
Installed package list: `audit/original_reproduction/env/pip_freeze.txt`.

**Note on versions.** `requirements.txt` pins `torch>=2.2`, `torch-geometric>=2.5`,
`scikit-learn>=1.4`, `numpy>=1.26`, `pandas>=2.2`. The audit environment uses
newer releases (torch 2.14, PyG 2.8, sklearn 1.9, numpy 2.5, pandas 3.0) because
the original author environment (a `Final Year Project` directory under
`/home/neha-manoj/`) is not available. CPU-only execution differs from any
GPU run the author may have used; GraphSAGE training is stochastic and
device-dependent, so small numerical differences are possible.

## 2. Unit tests

Command: `python3 -m pytest -q`

Result: **98 passed, 5 failed** (103 collected).

All 5 failures are in `tests/test_graph_loader.py` and are caused by the
**absence of the DARPA parsed CSVs** (`data/parsed/*.csv`), which are gitignored
and not shipped:

```
FAILED tests/test_graph_loader.py::test_available_datasets
FAILED tests/test_graph_loader.py::test_dataset_exists
FAILED tests/test_graph_loader.py::test_load_nodes      # FileNotFoundError: data/parsed/3_nodes.csv
FAILED tests/test_graph_loader.py::test_load_edges
FAILED tests/test_graph_loader.py::test_load_graph
```

The README claims "103 unit tests passing"; in a clean checkout that is not
true without the separately-downloaded dataset. The failure is environmental,
not a code defect.

## 3. Files inspected

| Area | Files |
|---|---|
| Synthetic graph generation | `src/graph_construction/synthetic.py` |
| Schema / data model | `src/graph_construction/schema.py` |
| DARPA loading | `src/graph_construction/graph_loader.py`, `converter.py`, `cdm_parser.py` |
| Poisoning injection | `src/detection/poisoning_injection.py` |
| Mimicry | `src/detection/mimicry_attack.py` |
| Rule engine | `src/detection/rule_engine.py`, `rule_based.py` |
| GraphSAGE | `src/ml/graphsage.py`, `dataset.py`, `train.py`, `predict.py`, `metrics.py`, `utils.py` |
| Evaluation metrics | `src/eval/metrics.py`, `confusion_matrix.py`, `evaluator.py` |
| Threshold selection | `src/ml/train.py::train_pipeline`, `src/ml/metrics.py::find_best_threshold` |
| Cross-scenario | `src/eval/cross_dataset.py` |
| Scalability | `src/eval/scalability.py` |
| Ablation | `src/eval/ablation.py` |
| Robustness / mimicry eval | `src/eval/robustness.py` |
| Report generation | `src/eval/report.py` |
| Runner scripts | `scripts/run_evaluation.py`, `run_rule_engine.py`, `run_graphsage.py`, `run_cross_dataset.py`, `run_scalability.py`, `run_mimicry.py` |

## 4. Structural observations

1. **No dataset is present in the repository.** `data/parsed/` does not exist;
   `data/samples/` contains only `.gitkeep`. Every "DARPA" number in
   `results/cross_dataset.md` therefore cannot be regenerated from a fresh
   clone, and the cross-scenario runner silently falls back to a synthetic
   graph (see `load_dataset_graph`: `if dataset_name.lower()=="synthetic" or
   not dataset_exists(dataset_name)`).
2. **Committed result files are inconsistent with the current code.** The
   committed `results/seed_statistics.md` reports `0.8125 ± 0.0000` (a single
   seed), while re-running the multi-seed script with the code's own
   `DEFAULT_SEEDS` gives `0.8039 ± 0.0696` (see Phase 3).
3. **`results/graphsage_checkpoint.pt` is committed** despite `.gitignore`
   listing `*.pt`, indicating it was force-added.
4. **The rule engine emits only binary flags.** `src/eval/metrics.MetricResult`
   has no `roc_auc` field, so the `ROC-AUC = 1.0000` reported for the Rule
   Engine is a hard-coded default (`getattr(m, "roc_auc", 1.0 if m.f1 > 0 else 0.5)`).
5. **`src/detection/poisoning_injection.py` mutates the caller's graph** for
   reordering and dependency forgery because the "copy" is shallow
   (`edges=list(graph.edges)`); the edge objects are shared. This corrupts any
   intended clean baseline and creates duplicate ground-truth edge IDs.
