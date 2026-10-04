# FINAL_NUMBERS — verified numerical source of truth

Every value below is re-derived from `audit/raw_runs/` by `audit/scripts/final_validation.py` (0 discrepancies) and aggregated by `audit/scripts/make_final.py`. Values are means over the stated seeds unless noted. Full precision lives in the CSV artifacts; this file rounds to 4 dp for readability only.

## 0. Scoring-universe sensitivity (must be stated in the paper)

The corrected protocol scores only edges present in the final graph. The repository's evaluator additionally adds the ids of deleted edges (which no longer exist) to the scoring universe. Using the same detector:

- Final-graph universe (corrected, used in the paper): F1 = 0.8048 ± 0.0627, precision = 0.7146, recall = 0.9329, ROC-AUC = 0.9528.
- Repo-style universe (final ∪ absent GT ids): F1 = 0.8453 ± 0.0513, precision = 0.7700, recall = 0.9445, ROC-AUC = 0.9583.
Raw: `audit/raw_runs/gt_sensitivity.json`. The manuscript reports the final-graph universe and states the assumption; a deletion cannot be edge-matched in the final graph and is reported separately as a limitation.

## 1. Dataset characteristics (real data)

- **DARPA TC E3 Theia (scenario 3)**: 20157 nodes, 297777 edges, 0 skipped. Raw: `audit/data/raw/theia/`; parse via `src/graph_construction/cdm_parser.py`.
- **DARPA TC E3 Theia (scenario 5m)**: 34835 nodes, 464858 edges, 0 skipped. Raw: `audit/data/raw/theia/`; parse via `src/graph_construction/cdm_parser.py`.

## 2. Synthetic detection — Rule Engine (10 seeds)

Protocol: synthetic graph (30 processes, 40 files, 10 network), 5 deletions + 5 insertions + 5 reorderings + 5 dependency forgeries; 10 detectable + 5 undetectable (deleted) positives; corrected final-graph scoring universe. Seeds 1,7,13,21,42,99,123,256,512,1024.

### Rule Engine precision

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** PRECISION
- **Mean:** 0.7146
- **Std:** 0.0948
- **95% CI:** [0.6468, 0.7824]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine recall

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** RECALL
- **Mean:** 0.9329
- **Std:** 0.0629
- **95% CI:** [0.8879, 0.9778]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine f1

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine accuracy

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** ACCURACY
- **Mean:** 0.9614
- **Std:** 0.0155
- **95% CI:** [0.9504, 0.9725]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine balanced_accuracy

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** BALANCED_ACCURACY
- **Mean:** 0.9484
- **Std:** 0.0304
- **95% CI:** [0.9267, 0.9702]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine mcc

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** MCC
- **Mean:** 0.7954
- **Std:** 0.0642
- **95% CI:** [0.7494, 0.8413]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine fpr

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** FPR
- **Mean:** 0.0360
- **Std:** 0.0174
- **95% CI:** [0.0236, 0.0484]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine fnr

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** FNR
- **Mean:** 0.0671
- **Std:** 0.0629
- **95% CI:** [0.0222, 0.1121]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine specificity

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** SPECIFICITY
- **Mean:** 0.9640
- **Std:** 0.0174
- **95% CI:** [0.9516, 0.9764]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine roc_auc

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** ROC_AUC
- **Mean:** 0.9528
- **Std:** 0.0312
- **95% CI:** [0.9306, 0.9751]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### Rule Engine pr_auc

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** corrected poisoning, final-graph universe
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** PR_AUC
- **Mean:** 0.7403
- **Std:** 0.0796
- **95% CI:** [0.6834, 0.7972]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

## 3. Synthetic detection — GraphSAGE (10 seeds, leakage-free)

Protocol: same graphs and positives; strict train/val/test split; threshold selected on validation only.

### GraphSAGE precision

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** PRECISION
- **Mean:** 0.3416
- **Std:** 0.3093
- **95% CI:** [0.1203, 0.5629]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE recall

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** RECALL
- **Mean:** 0.5017
- **Std:** 0.3637
- **95% CI:** [0.2415, 0.7618]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE f1

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.3224
- **Std:** 0.1942
- **95% CI:** [0.1835, 0.4614]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE accuracy

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** ACCURACY
- **Mean:** 0.8514
- **Std:** 0.0756
- **95% CI:** [0.7972, 0.9055]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE balanced_accuracy

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** BALANCED_ACCURACY
- **Mean:** 0.6949
- **Std:** 0.1428
- **95% CI:** [0.5927, 0.7970]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE mcc

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** MCC
- **Mean:** 0.3121
- **Std:** 0.1985
- **95% CI:** [0.1701, 0.4540]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE fpr

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** FPR
- **Mean:** 0.1119
- **Std:** 0.1095
- **95% CI:** [0.0336, 0.1902]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE fnr

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** FNR
- **Mean:** 0.4983
- **Std:** 0.3637
- **95% CI:** [0.2382, 0.7585]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE specificity

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** SPECIFICITY
- **Mean:** 0.8881
- **Std:** 0.1095
- **95% CI:** [0.8098, 0.9664]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE roc_auc

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** ROC_AUC
- **Mean:** 0.8289
- **Std:** 0.1595
- **95% CI:** [0.7148, 0.9430]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

### GraphSAGE pr_auc

- **Experiment:** Synthetic main detection
- **Dataset:** Synthetic controlled
- **Protocol:** leakage-free train/val/test
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** PR_AUC
- **Mean:** 0.5909
- **Std:** 0.2445
- **95% CI:** [0.4160, 0.7658]
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table2_synthetic_detection.csv
- **Source figure:** figures/fig_main_performance.png
- **Status:** SUPPORTED

## 4. Statistical significance (paired, 10 seeds)

### Paired RuleEngine−GraphSAGE f1

- **Experiment:** Paired comparison
- **Dataset:** Synthetic controlled
- **Protocol:** paired over identical test instances; Wilcoxon signed-rank
- **Model:** RuleEngine vs GraphSAGE
- **Seeds:** 10
- **Metric:** F1
- **Mean:** mean_diff=0.4824
- **Std:** std_diff=0.2152
- **95% CI:** [0.3285, 0.6363]; Wilcoxon p=0.001953; Cohen dz=2.2419
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table8_significance.csv
- **Source figure:** figures/fig_significance.png
- **Status:** SUPPORTED

### Paired RuleEngine−GraphSAGE roc_auc

- **Experiment:** Paired comparison
- **Dataset:** Synthetic controlled
- **Protocol:** paired over identical test instances; Wilcoxon signed-rank
- **Model:** RuleEngine vs GraphSAGE
- **Seeds:** 10
- **Metric:** ROC_AUC
- **Mean:** mean_diff=0.1239
- **Std:** std_diff=0.1655
- **95% CI:** [0.0055, 0.2423]; Wilcoxon p=0.105469; Cohen dz=0.7485
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json
- **Source table:** table8_significance.csv
- **Source figure:** figures/fig_significance.png
- **Status:** SUPPORTED

## 5. Mimicry robustness (corrected invariant-preserving generator)

### Mimicry none — RuleEngine

- **Experiment:** Mimicry robustness
- **Dataset:** Synthetic controlled
- **Protocol:** none camouflage; noise_self_violations=0.00
- **Model:** RuleEngine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** see table4
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json (.mimicry)
- **Source table:** table4_mimicry_robustness.csv
- **Source figure:** figures/fig_mimicry.png
- **Status:** SUPPORTED

### Mimicry none — GraphSAGE

- **Experiment:** Mimicry robustness
- **Dataset:** Synthetic controlled
- **Protocol:** none camouflage; noise_self_violations=0.00
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.3224
- **Std:** 0.1942
- **95% CI:** see table4
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json (.mimicry)
- **Source table:** table4_mimicry_robustness.csv
- **Source figure:** figures/fig_mimicry.png
- **Status:** SUPPORTED

### Mimicry light — RuleEngine

- **Experiment:** Mimicry robustness
- **Dataset:** Synthetic controlled
- **Protocol:** light camouflage; noise_self_violations=0.00
- **Model:** RuleEngine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** see table4
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json (.mimicry)
- **Source table:** table4_mimicry_robustness.csv
- **Source figure:** figures/fig_mimicry.png
- **Status:** SUPPORTED

### Mimicry light — GraphSAGE

- **Experiment:** Mimicry robustness
- **Dataset:** Synthetic controlled
- **Protocol:** light camouflage; noise_self_violations=0.00
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.3737
- **Std:** 0.2205
- **95% CI:** see table4
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json (.mimicry)
- **Source table:** table4_mimicry_robustness.csv
- **Source figure:** figures/fig_mimicry.png
- **Status:** SUPPORTED

### Mimicry medium — RuleEngine

- **Experiment:** Mimicry robustness
- **Dataset:** Synthetic controlled
- **Protocol:** medium camouflage; noise_self_violations=0.00
- **Model:** RuleEngine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** see table4
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json (.mimicry)
- **Source table:** table4_mimicry_robustness.csv
- **Source figure:** figures/fig_mimicry.png
- **Status:** SUPPORTED

### Mimicry medium — GraphSAGE

- **Experiment:** Mimicry robustness
- **Dataset:** Synthetic controlled
- **Protocol:** medium camouflage; noise_self_violations=0.00
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.3044
- **Std:** 0.2603
- **95% CI:** see table4
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json (.mimicry)
- **Source table:** table4_mimicry_robustness.csv
- **Source figure:** figures/fig_mimicry.png
- **Status:** SUPPORTED

### Mimicry heavy — RuleEngine

- **Experiment:** Mimicry robustness
- **Dataset:** Synthetic controlled
- **Protocol:** heavy camouflage; noise_self_violations=0.00
- **Model:** RuleEngine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** see table4
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json (.mimicry)
- **Source table:** table4_mimicry_robustness.csv
- **Source figure:** figures/fig_mimicry.png
- **Status:** SUPPORTED

### Mimicry heavy — GraphSAGE

- **Experiment:** Mimicry robustness
- **Dataset:** Synthetic controlled
- **Protocol:** heavy camouflage; noise_self_violations=0.00
- **Model:** GraphSAGE
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.5418
- **Std:** 0.3547
- **95% CI:** see table4
- **Raw artifact:** audit/raw_runs/synthetic/seed_*.json (.mimicry)
- **Source table:** table4_mimicry_robustness.csv
- **Source figure:** figures/fig_mimicry.png
- **Status:** SUPPORTED

## 6. Rule ablation (10 seeds)

### Ablation all_rules

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_DeleteConsistencyRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_DuplicateEdgeRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_DuplicateEventRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_ExecutionConsistencyRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_MissingNodeRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_NetworkConsistencyRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.7455
- **Std:** 0.0844
- **95% CI:** [0.6851, 0.8059]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_ParentChildTemporalRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8170
- **Std:** 0.0412
- **95% CI:** [0.7875, 0.8464]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_ProcessActivityTemporalRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8280
- **Std:** 0.0382
- **95% CI:** [0.8007, 0.8553]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_ReadWriteConsistencyRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.5173
- **Std:** 0.1136
- **95% CI:** [0.4360, 0.5985]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_SelfLoopRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_SequenceGapRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_SequenceMonotonicityRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.7802
- **Std:** 0.0863
- **95% CI:** [0.7185, 0.8420]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_SpawnConsistencyRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.7417
- **Std:** 0.0903
- **95% CI:** [0.6771, 0.8063]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_TimestampRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation loo_UnspawnedProcessRule

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation without_semantic

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8048
- **Std:** 0.0627
- **95% CI:** [0.7600, 0.8496]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation without_structural

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.3285
- **Std:** 0.0731
- **95% CI:** [0.2762, 0.3807]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

### Ablation without_temporal

- **Experiment:** Rule ablation
- **Dataset:** Synthetic controlled
- **Protocol:** 10 seeds; F1
- **Model:** Rule Engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.7983
- **Std:** 0.0055
- **95% CI:** [0.7943, 0.8022]
- **Raw artifact:** audit/raw_runs/ablation/seed_*.json
- **Source table:** table5_rule_ablation.csv
- **Source figure:** figures/fig_ablation.png
- **Status:** SUPPORTED

## 7. Real Theia + synthetic post-collection poisoning

NOT real attack labels. Real provenance graph; attacks injected after collection. 50,000-edge cap. 20 requested ops → 15 detectable positives (5 deletions vanish). 10 seeds.

### DARPA theia3 — synthetic_post_collection_rule_engine

- **Experiment:** Real-data + synthetic poisoning
- **Dataset:** Theia E3 theia3 (50k edges)
- **Protocol:** synthetic post-collection poisoning
- **Model:** synthetic_post_collection_rule_engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8347
- **Std:** 0.0459
- **95% CI:** see table3
- **Raw artifact:** audit/raw_runs/darpa/theia3_50000.json
- **Source table:** table3_darpa_cross_scenario.csv
- **Source figure:** figures/fig_darpa.png
- **Status:** SUPPORTED

### DARPA theia3 — synthetic_post_collection_graphsage

- **Experiment:** Real-data + synthetic poisoning
- **Dataset:** Theia E3 theia3 (50k edges)
- **Protocol:** synthetic post-collection poisoning
- **Model:** synthetic_post_collection_graphsage
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.0340
- **Std:** 0.1052
- **95% CI:** see table3
- **Raw artifact:** audit/raw_runs/darpa/theia3_50000.json
- **Source table:** table3_darpa_cross_scenario.csv
- **Source figure:** figures/fig_darpa.png
- **Status:** SUPPORTED

### DARPA theia5m — synthetic_post_collection_rule_engine

- **Experiment:** Real-data + synthetic poisoning
- **Dataset:** Theia E3 theia5m (50k edges)
- **Protocol:** synthetic post-collection poisoning
- **Model:** synthetic_post_collection_rule_engine
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.8504
- **Std:** 0.0599
- **95% CI:** see table3
- **Raw artifact:** audit/raw_runs/darpa/theia5m_50000.json
- **Source table:** table3_darpa_cross_scenario.csv
- **Source figure:** figures/fig_darpa.png
- **Status:** SUPPORTED

### DARPA theia5m — synthetic_post_collection_graphsage

- **Experiment:** Real-data + synthetic poisoning
- **Dataset:** Theia E3 theia5m (50k edges)
- **Protocol:** synthetic post-collection poisoning
- **Model:** synthetic_post_collection_graphsage
- **Seeds:** 10
- **Metric:** F1
- **Mean:** 0.0099
- **Std:** 0.0093
- **95% CI:** see table3
- **Raw artifact:** audit/raw_runs/darpa/theia5m_50000.json
- **Source table:** table3_darpa_cross_scenario.csv
- **Source figure:** figures/fig_darpa.png
- **Status:** SUPPORTED

## 8. Scalability (Rule Engine inference; 5 reps/size)

### Scalability 10000 edges

- **Experiment:** Scalability
- **Dataset:** Synthetic controlled
- **Protocol:** 5 reps; construction/poisoning/inference separated
- **Model:** Rule Engine inference
- **Seeds:** 5 reps
- **Metric:** time/memory/throughput
- **Mean:** infer=0.3661 s; throughput=28087.9 edges/s; peak_python=36.9 MB
- **Std:** 0.0762
- **95% CI:** n/a
- **Raw artifact:** audit/raw_runs/scalability/size_*_rep_*.json
- **Source table:** table6_scalability.csv
- **Source figure:** figures/fig_scalability.png
- **Status:** SUPPORTED

### Scalability 25000 edges

- **Experiment:** Scalability
- **Dataset:** Synthetic controlled
- **Protocol:** 5 reps; construction/poisoning/inference separated
- **Model:** Rule Engine inference
- **Seeds:** 5 reps
- **Metric:** time/memory/throughput
- **Mean:** infer=1.1417 s; throughput=22296.7 edges/s; peak_python=24.9 MB
- **Std:** 0.1860
- **95% CI:** n/a
- **Raw artifact:** audit/raw_runs/scalability/size_*_rep_*.json
- **Source table:** table6_scalability.csv
- **Source figure:** figures/fig_scalability.png
- **Status:** SUPPORTED

### Scalability 50000 edges

- **Experiment:** Scalability
- **Dataset:** Synthetic controlled
- **Protocol:** 5 reps; construction/poisoning/inference separated
- **Model:** Rule Engine inference
- **Seeds:** 5 reps
- **Metric:** time/memory/throughput
- **Mean:** infer=2.0759 s; throughput=24368.1 edges/s; peak_python=49.4 MB
- **Std:** 0.2533
- **95% CI:** n/a
- **Raw artifact:** audit/raw_runs/scalability/size_*_rep_*.json
- **Source table:** table6_scalability.csv
- **Source figure:** figures/fig_scalability.png
- **Status:** SUPPORTED

### Scalability 100000 edges

- **Experiment:** Scalability
- **Dataset:** Synthetic controlled
- **Protocol:** 5 reps; construction/poisoning/inference separated
- **Model:** Rule Engine inference
- **Seeds:** 5 reps
- **Metric:** time/memory/throughput
- **Mean:** infer=3.1541 s; throughput=31709.4 edges/s; peak_python=98.1 MB
- **Std:** 0.0441
- **95% CI:** n/a
- **Raw artifact:** audit/raw_runs/scalability/size_*_rep_*.json
- **Source table:** table6_scalability.csv
- **Source figure:** figures/fig_scalability.png
- **Status:** SUPPORTED

### Scalability 250000 edges

- **Experiment:** Scalability
- **Dataset:** Synthetic controlled
- **Protocol:** 5 reps; construction/poisoning/inference separated
- **Model:** Rule Engine inference
- **Seeds:** 5 reps
- **Metric:** time/memory/throughput
- **Mean:** infer=7.9138 s; throughput=31596.1 edges/s; peak_python=244.1 MB
- **Std:** 0.1177
- **95% CI:** n/a
- **Raw artifact:** audit/raw_runs/scalability/size_*_rep_*.json
- **Source table:** table6_scalability.csv
- **Source figure:** figures/fig_scalability.png
- **Status:** SUPPORTED

### Scalability 500000 edges

- **Experiment:** Scalability
- **Dataset:** Synthetic controlled
- **Protocol:** 5 reps; construction/poisoning/inference separated
- **Model:** Rule Engine inference
- **Seeds:** 5 reps
- **Metric:** time/memory/throughput
- **Mean:** infer=17.1089 s; throughput=29224.7 edges/s; peak_python=486.6 MB
- **Std:** 0.0501
- **95% CI:** n/a
- **Raw artifact:** audit/raw_runs/scalability/size_*_rep_*.json
- **Source table:** table6_scalability.csv
- **Source figure:** figures/fig_scalability.png
- **Status:** SUPPORTED

### Scalability 1000000 edges

- **Experiment:** Scalability
- **Dataset:** Synthetic controlled
- **Protocol:** 5 reps; construction/poisoning/inference separated
- **Model:** Rule Engine inference
- **Seeds:** 5 reps
- **Metric:** time/memory/throughput
- **Mean:** infer=34.4796 s; throughput=29006.8 edges/s; peak_python=971.4 MB
- **Std:** 0.4639
- **95% CI:** n/a
- **Raw artifact:** audit/raw_runs/scalability/size_*_rep_*.json
- **Source table:** table6_scalability.csv
- **Source figure:** figures/fig_scalability.png
- **Status:** SUPPORTED

## 9. Cross-dataset generalization (Rule Engine, no retraining; 5 seeds)

### Generalization synthetic→theia3

- **Experiment:** Cross-dataset generalization
- **Dataset:** synthetic → theia3
- **Protocol:** fixed invariants, no retraining
- **Model:** Rule Engine
- **Seeds:** 5
- **Metric:** F1
- **Mean:** 0.8566
- **Std:** 0.0289
- **95% CI:** see table9
- **Raw artifact:** audit/raw_runs/generalization/*.json
- **Source table:** table9_generalization.csv
- **Source figure:** figures/fig_generalization.png
- **Status:** SUPPORTED

### Generalization theia3→theia5m

- **Experiment:** Cross-dataset generalization
- **Dataset:** theia3 → theia5m
- **Protocol:** fixed invariants, no retraining
- **Model:** Rule Engine
- **Seeds:** 5
- **Metric:** F1
- **Mean:** 0.8369
- **Std:** 0.0206
- **95% CI:** see table9
- **Raw artifact:** audit/raw_runs/generalization/*.json
- **Source table:** table9_generalization.csv
- **Source figure:** figures/fig_generalization.png
- **Status:** SUPPORTED

### Generalization theia5m→theia3

- **Experiment:** Cross-dataset generalization
- **Dataset:** theia5m → theia3
- **Protocol:** fixed invariants, no retraining
- **Model:** Rule Engine
- **Seeds:** 5
- **Metric:** F1
- **Mean:** 0.8566
- **Std:** 0.0289
- **95% CI:** see table9
- **Raw artifact:** audit/raw_runs/generalization/*.json
- **Source table:** table9_generalization.csv
- **Source figure:** figures/fig_generalization.png
- **Status:** SUPPORTED
