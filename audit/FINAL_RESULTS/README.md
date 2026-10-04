# FINAL_RESULTS — how to inspect the final evidence

This directory is the single convenient location from which the final
experimental evidence can be inspected. Everything here is derived from
`audit/raw_runs/` and was independently cross-checked in
`audit/final_validation/` (226 checks, 0 discrepancies; 1,890 metric
recomputations, 0 mismatches).

## Where to look

| Question | File |
|---|---|
| The final numbers | `FINAL_NUMBERS.md` (the numerical source of truth) |
| The datasets | `DATASET_SUMMARY.md` |
| The exact protocol | `EXPERIMENTAL_PROTOCOL.md` |
| How to reproduce | `REPRODUCIBILITY.md` |
| What is not defensible | `LIMITATIONS.md` |
| Manuscript tables | `tables/{csv,markdown,latex}/table1..table9*` |
| Journal-ready tables (audit numbering) | `tables/journal_ready_{csv,markdown,latex}/` |
| Figures | `figures/*.png` / `*.pdf` + `figures/FIGURE_SOURCE_MAP.md` |
| Seed-level raw values | `raw_results/` (copies of `audit/raw_runs/`) |
| Statistical tests | `statistics/` |

## Table → experiment map

| Table | Contents |
|---|---|
| table1_dataset_statistics | Real Theia parse counts + unavailable scenarios |
| table2_experimental_protocol | Protocol for every experiment |
| table3_main_detection | Synthetic detection, Rule Engine vs GraphSAGE, 10 seeds |
| table4_statistical_comparison | Paired significance tests |
| table5_cross_dataset | Cross-dataset generalization |
| table6_mimicry | Mimicry robustness |
| table7_rule_ablation | Rule ablation / leave-one-rule-out |
| table8_scalability | Runtime, memory, throughput |
| table9_real_data_poisoning | Real Theia + synthetic post-collection poisoning |

## Figure → claim map

| Figure | Claim |
|---|---|
| fig_main_performance | Rule Engine outperforms leakage-free GraphSAGE |
| fig_roc_pr | ROC-AUC/PR-AUC are genuine continuous-score values |
| fig_leakage | Evaluation leakage inflates GraphSAGE F1 |
| fig_mimicry | Rule Engine is invariant to invariant-preserving mimicry |
| fig_ablation | Structural rules carry detection |
| fig_scalability | Linear runtime/memory, stable throughput |
| fig_generalization | Rule Engine transfers without retraining |

## Source code for each result

| Experiment | Runner |
|---|---|
| Synthetic + mimicry | `audit/experiments/synthetic/run_synthetic.py` |
| Ablation | `audit/experiments/ablation/run_ablation.py` |
| Real Theia + poisoning | `audit/experiments/darpa/run_darpa.py` |
| Generalization | `audit/experiments/generalization/run_generalization.py` |
| Scalability | `audit/experiments/scalability/run_scalability.py` |
| Corrected poisoning | `audit/experiments/poisoning/poisoning_v2.py` |
| Corrected mimicry | `audit/experiments/mimicry/mimicry_v2.py` |
| Leakage-free harness | `audit/experiments/corrected/harness.py` |
| Aggregation | `audit/scripts/make_final.py` |
| Validation | `audit/scripts/final_validation.py` |

## Data categories (never merged)

* **Real data only** — `table1_dataset_statistics` (Theia E3 parse counts).
* **Real data + controlled synthetic poisoning** — `table9_real_data_poisoning`
  (Theia 3 / 5m, 50k-edge cap; attacks injected after collection; **not** real
  attack labels).
* **Synthetic controlled** — `table3`, `table4`, `table6`, `table7` and the
  synthetic rows of `table5`.

## Incomplete experiments

* Theia E3 scenarios **1r** and **6r** were not obtained (Google Drive quota,
  HTTP 403). No results are fabricated; see `LIMITATIONS.md`.
* Genuine cross-graph GraphSAGE transfer is not implemented; `table5` reports the
  target-trained GraphSAGE only and is labelled as such.
