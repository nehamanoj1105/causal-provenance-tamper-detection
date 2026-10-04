# Paper-to-Code Protocol Reconstruction (Phase 2)

The manuscript PDF is not in the repository. The reported values used here are
the numbers the repository itself presents as results
(`results/*.md`, `README.md`, `docs/`). Those files are the artifact a reader
would cite, so they are treated as the "paper values". Where the paper is said
to report a value that does not appear in the repo (e.g. Rule Engine
ROC-AUC = 1.0000 under heavy mimicry), the value from `results/mimicry_results.md`
is used.

Every entry below is reconstructed from the code path that produces it. Nothing
here assumes the current code reproduces the paper.

## 1. Global defaults actually used by the code

| Parameter | Value | Where |
|---|---|---|
| Synthetic graph (evaluation) | `num_processes=30, num_files=40, num_network=10` | `scripts/run_evaluation.py::load_evaluation_graph` |
| Synthetic graph (GraphSAGE) | same | `scripts/run_graphsage.py::load_graphsage_data` |
| Synthetic graph (mimicry) | `num_processes=40, num_files=50, num_network=15` | `scripts/run_mimicry.py` |
| Attack intensity (per type) | 5 | all runners (`--intensity` default 5) |
| Seeds | `[1,7,13,21,42,99,123,256,512,1024]` | `scripts/run_evaluation.py::DEFAULT_SEEDS` |
| GraphSAGE epochs | 30 (synthetic/graphsage), 25 (mimicry), 15 (cross-dataset) | runner defaults |
| GraphSAGE lr | 0.01 | `train_pipeline` default |
| GraphSAGE hidden | 64 (32 in mimicry) | runner defaults |
| GraphSAGE loss | weighted BCE (`pos_weight = neg/pos`) | `train_pipeline` |
| Threshold search | 0.05…1.00 step 0.05, max F1 | `src/ml/metrics.py::find_best_threshold` |
| DARPA max edges | 50000 (`--max-edges` default) | `scripts/run_cross_dataset.py` |
| Scalability scales | 10k,25k,50k,100k,250k,500k,1M | `scripts/run_scalability.py` |

## 2. Reported result -> protocol mapping

| Paper Result | Expected Protocol | Current Code Protocol | Match? | Explanation |
|---|---|---|---|---|
| Synthetic P=0.8125, R=0.6500, F1=0.7222, Acc=0.9457 (seed 42) | Rule Engine on synthetic graph, intensity 5, seed 42 | `run_evaluation.py --attack-type all --seed 42`; same numbers reproduced | **YES** | Exact match for seed 42 (TP13/FP3/TN161/FN7). |
| Synthetic "multi-seed" P/R/F1 = 0.8125±0.0000 etc. | mean±std over 10 seeds | Script supports 10 seeds but committed stats equal the single seed-42 run (std 0) | **NO** | The ±0.0000 reveals only one seed was aggregated. Re-run gives 0.8039±0.0696. |
| GraphSAGE F1=0.5600, ROC-AUC=0.8776, PR-AUC=0.5634, τ*=0.70 | Train GraphSAGE, sweep threshold, report best | `run_graphsage.py --epochs 30 --seed 42`; reproduced exactly | **YES** | Reproduced to 4 dp. |
| DARPA 1r/3/5m/6r numbers | Load parsed DARPA CSVs, truncate 50k edges, inject 5×4 poison | Requires `data/parsed/`; absent from repo | **UNVERIFIABLE** | Falls back to synthetic when dataset missing. |
| Mimicry none/light/medium/heavy | Base poison (5 each) + noise 0%/30%/70%/150% | `run_mimicry.py`; reproduced exactly | **YES** | Edge counts 234/304/397/585 reproduced. |
| Rule Engine ROC-AUC = 1.0000 (all mimicry) | Continuous ranking score for rule engine | `robustness.py` uses `getattr(m,'roc_auc', 1.0 if m.f1>0 else 0.5)`; MetricResult has no roc_auc | **NO** | Fabricated constant, not a computed AUC. |
| Rule statistics table | Per-rule TP/FP/FN on one synthetic seed | `run_scalability.py` part 6, seed 42; reproduced | **YES** | Exact match. |
| Ablation table | Category + leave-one-out on one seed | `run_scalability.py` part 5, seed 42; reproduced | **YES** | Exact match (single seed). |
| Scalability up to 1M edges | Construct synthetic graph of exact size, time detection | `run_scalability.py`; reproduced, values differ ~2× in detector time | **PARTIAL** | Sizes and shapes match; timings differ (hardware). |
| GraphSAGE "training + threshold on validation" | Explicit val set | `train_pipeline` trains and thresholds on the same data | **NO** | No validation/test split anywhere; `create_train_val_test_masks` is unused. |
| DARPA provenance poisoning ground truth | Real DARPA attack labels | Attacks are synthetically injected post-hoc | **NO** | Must be described as synthetic post-collection poisoning. |
| GraphSAGE compared to Rule Engine on same instances | Paired evaluation | Rule Engine and GraphSAGE both evaluated on the poison graph, but GraphSAGE leaks labels | **PARTIAL** | Same instances, invalid GraphSAGE protocol. |

## 3. Protocol facts that are NOT stated in the repo but matter

1. **No train/validation/test separation exists.** `create_train_val_test_masks`
   exists in `src/ml/utils.py` but is never called. `train_pipeline` trains on
   all edges and selects the threshold on those same edges.
2. **Poisoning labels are supplied to the model as targets on the evaluation
   graph** (`provenance_to_pyg_data(..., poisoning_result=poison_res)`), and the
   threshold is chosen on the same labels.
3. **Graph topology used for training is the poisoned test graph.** There is no
   clean training graph.
4. **The DARPA scenarios are truncated to the first 50,000 edges**
   (`df_edges.iloc[:max_edges]`), and attack injection happens after truncation.
   This is silent: no report column records the truncation.
5. **`docs/dataset_statistics.md` reports the full DARPA sizes** (1r: 9.3M edges,
   3: 298k, 5m: 465k, 6r: 18.2M), so the paper's "50,000 edges" tables are
   subgraph slices, not full-dataset results.

## 4. Ambiguities that could not be resolved

- The manuscript itself was not available, so any table not mirrored in
  `results/` could not be checked.
- The author's Python/PyTorch versions are unknown; CPU vs GPU is unknown.
- The number of seeds behind the DARPA table is unknown (the script uses one
  seed, 42).
