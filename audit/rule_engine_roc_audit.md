# Rule Engine ROC-AUC Verification (Phase 6)

**Paper/committed claim:** Rule Engine ROC-AUC = `1.0000` at every mimicry
strength (`results/mimicry_results.md`).

## 1. Is there a legitimate continuous score?

`src/eval/metrics.MetricResult` fields (verified in
`audit/raw_runs/rule_score_audit.json`):

```
precision, recall, f1, accuracy, false_positive_rate, false_negative_rate,
specificity, balanced_accuracy
```

There is **no** `roc_auc` field. The Rule Engine itself emits only binary
violations (`RuleViolation.edge_id`). The robustness evaluator therefore does:

```python
roc_auc = getattr(m, "roc_auc", 1.0 if m.f1 > 0 else 0.5)
pr_auc  = getattr(m, "pr_auc",  m.precision * m.recall)
```

Since `m` never has `roc_auc`, the default is used: **ROC-AUC = 1.0 whenever any
violation exists**, regardless of correctness. This is a fabricated constant, not
a computed AUC. The committed `PR-AUC` values (0.6125/0.1406/0.0699/0.0418) are
also just `precision × recall`, not average precision.

## 2. Independent recomputation

The only defensible continuous edge-level score the rules expose is the **number
of distinct rule violations per edge** (`0,1,2,…`) from
`src.detection.rule_based.run_all_checks`. That is a genuine ordinal ranking:
higher = more invariants broken. Binary thresholding at `score > 0` reproduces
the reported detector flags exactly.

Computed over the 10 audit seeds (synthetic graph 40/50/15, intensity 5):

| Strength | Count-score ROC-AUC (mean) | Count-score PR-AUC (mean) | Binary-flag ROC-AUC (mean) | Reported | Verdict |
|---|---|---|---|---|---|
| none | 0.8502 | 0.6041 | 0.8496 | 1.0000 | **discrepancy** |
| light | 0.7259 | 0.1110 | 0.7486 | 1.0000 | **discrepancy** |
| medium | 0.6026 | 0.0534 | 0.6385 | 1.0000 | **discrepancy** |
| heavy | 0.5422 | 0.0373 | 0.5764 | 1.0000 | **discrepancy** |

(Exact per-seed values and PR-AUCs in `audit/raw_runs/rule_score_audit.json`.)

## 3. Conclusion

- The reported Rule Engine `ROC-AUC = 1.0000` is **not reproducible** and must
  **not** be reported. It is a default constant emitted because the metric object
  lacks an AUC field.
- A legitimate continuous ranking exists (violation count). Under it the Rule
  Engine's true ROC-AUC degrades from ≈0.85 (no mimicry) to ≈0.54 (heavy
  mimicry) — i.e. essentially chance under heavy camouflage.
- PR-AUC is available from the same score and should replace the
  `precision × recall` placeholder.

### Safe to report
- Rule Engine ROC-AUC / PR-AUC computed from the violation-count score
  (clearly labelled as such).
- Binary operating-point metrics (precision/recall/F1/FPR).

### NOT safe to report
- `ROC-AUC = 1.0000` for the Rule Engine.
- Any `PR-AUC` equal to `precision × recall`.
