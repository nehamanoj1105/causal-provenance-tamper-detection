# Source Map — where every final number comes from

Each row maps a manuscript-level result to: the raw artifact, the aggregator, the
table, and the generation script. All paths are relative to the repository root.

| Result | Raw artifact | Aggregator / script | Published table |
|---|---|---|---|
| Synthetic detection (RE + GraphSAGE) | `audit/raw_runs/synthetic/seed_{1,7,13,21,42,99,123,256,512,1024}.json` | `audit/scripts/make_final.py::synthetic_tables` | `table2_synthetic_detection`, `table7_multiseed` |
| Mimicry robustness (none/light/medium/heavy) | embedded in the same synthetic seed records under `.mimicry` | `make_final.py::mimicry_tables` | `table4_mimicry_robustness` |
| Rule ablation + LOO | `audit/raw_runs/ablation/seed_*.json` | `make_final.py::ablation_tables` | `table5_rule_ablation` |
| Real Theia + synthetic poisoning | `audit/raw_runs/darpa/{theia3,theia5m}_50000.json` | `make_final.py::darpa_tables` | `table3_darpa_cross_scenario` |
| Scalability | `audit/raw_runs/scalability/size_*_rep_*.json` (7 sizes × 5 reps) | `make_final.py::scalability_tables` | `table6_scalability` |
| Cross-dataset generalization | `audit/raw_runs/generalization/*__seed_*.json` (15) | `make_final.py::generalization_tables` | `table9_generalization` |
| Paired significance tests | derived from synthetic seed records | `make_final.py::stats_table` | `table8_significance` |
| Dataset characteristics | `audit/data/raw/theia/*.csv` via `src/graph_construction/cdm_parser.py` | `make_final.py::dataset_table` | `table1_dataset_characteristics` |
| Rule Engine ROC/PR (genuine score) | `audit/raw_runs/synthetic/seed_42.json` | `audit/scripts/make_final.py::plots` | `plots/rule_engine_roc_pr_seed42.png` |

## Source code for each experiment

| Experiment | Runner |
|---|---|
| Synthetic + mimicry | `audit/experiments/synthetic/run_synthetic.py` |
| Ablation | `audit/experiments/ablation/run_ablation.py` |
| DARPA / real Theia | `audit/experiments/darpa/run_darpa.py` |
| Generalization | `audit/experiments/generalization/run_generalization.py` |
| Scalability | `audit/experiments/scalability/run_scalability.py` |
| Corrected poisoning operators | `audit/experiments/poisoning/poisoning_v2.py` |
| Corrected mimicry generator | `audit/experiments/mimicry/mimicry_v2.py` |
| Leakage-free harness | `audit/experiments/corrected/harness.py` |
| Corrected metrics | `audit/experiments/corrected/metrics.py` |
| Aggregation | `audit/scripts/make_final.py` |
| Validation | `audit/scripts/final_validation.py`, `audit/scripts/independent_recheck.py` |

## Real vs synthetic

| Category | Experiments |
|---|---|
| Real data only | `table1_dataset_characteristics` (Theia E3 parse counts) |
| Real data + synthetic poisoning | `table3_darpa_cross_scenario` (Theia 3 / 5m, 50k-edge cap) |
| Synthetic controlled | `table2`, `table4`, `table5`, `table6`, `table7`, `table8` |
| Mixed source→target | `table9_generalization` (synthetic + real Theia) |
