# Experimental Protocol

## Seeds

`1, 7, 13, 21, 42, 99, 123, 256, 512, 1024` (10 seeds) for synthetic, mimicry,
ablation, real-Theia poisoning and the paired significance tests.
`1, 7, 13, 21, 42` (5 seeds) for cross-dataset generalization.
5 independent repetitions for each scalability size.

## Synthetic controlled poisoning

Generator: `src/graph_construction/synthetic.py` (30 processes, 40 files,
10 network). Injection: `audit/experiments/poisoning/poisoning_v2.py`.
Per seed: 5 deletions, 5 insertions, 5 reorderings, 5 dependency forgeries.
The corrected injector deep-copies the clean graph, records explicit
original/modified state, an `expected_detection_target` and an `effective` flag,
and asserts integrity (`integrity_problems = []` on every seed).

**Positive universe.** Detection is scored only over edges present in the final
graph. Ten positives are detectable (insertions, reorderings, forgeries); the
five deleted edges leave no final-graph record and are reported as undetectable
under an edge-matching protocol. This is the *final-graph universe*. The
repository's evaluator instead adds the absent deleted-edge ids, yielding
F1 0.8453 vs the corrected 0.8048; the paper uses the corrected universe and
states the assumption.

## Rule Engine

`src/detection/rule_engine.py` (unmodified) with a genuine continuous anomaly
score in `audit/experiments/corrected/harness.py`: each violation contributes a
severity weight (HIGH 3, MEDIUM 2, LOW 1) to the edge it is attributed to (by
`edge_id`, or via `node_id` to incident edges). This score is used for ROC-AUC
and PR-AUC; binary detection uses score > 0. No ROC-AUC is fabricated.

## GraphSAGE baseline (leakage-free)

`audit/experiments/corrected/harness.py`. Nodes/edges are split into disjoint
train / validation / test sets. Weights are trained on train only; the decision
threshold is selected on validation only; all reported metrics are computed on
the untouched test set. Message passing for test-node features uses only
train+validation edges. The original repository protocol
(`src/ml/train.py::train_pipeline`) trains on all edges and selects the threshold
on the scored set; that leakage is documented, not used.

## Evaluation metrics

Precision, recall, F1, accuracy, balanced accuracy, MCC, FPR, FNR, specificity,
ROC-AUC and PR-AUC (average precision). ROC-AUC/PR-AUC are only reported when a
genuine continuous score exists and both classes are present.

## Statistics

Per-metric mean, sample standard deviation (ddof = 1), median, min, max and 95%
confidence interval (Student-t, df = n−1). Paired RuleEngine−GraphSAGE
comparisons use the Wilcoxon signed-rank test with Cohen's d_z.

## Artifacts

All raw per-seed files live in `raw_results/`; aggregation is
`audit/scripts/make_final.py`; validation is `audit/scripts/final_validation.py`.
