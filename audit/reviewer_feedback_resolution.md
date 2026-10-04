# Reviewer Feedback Resolution

The five findings raised in the corrected audit were resolved before this pass.
This document maps each finding to what the final manuscripts and artifacts do
about it. None was papered over with a smoothed number.

## Finding 1 — GraphSAGE train/test leakage

**Problem.** The original `train_pipeline` trained on all edges and selected the
decision threshold on the same scored labels, after message passing over the full
graph.

**Resolution.** All GraphSAGE numbers in the manuscripts come from the
leakage-free harness `audit/experiments/corrected/harness.py`: disjoint
train/validation/test edges, weights on train only, threshold on validation
only, message passing restricted to train+val edges. The leaky value
(F1 0.588) is reported only as a defect, next to the clean value (0.246), and is
never presented as a result. Reported GraphSAGE synthetic F1 is
0.322 ± 0.194.

## Finding 2 — Rule Engine ROC-AUC fabricated fallback

**Problem.** The repository reported ROC-AUC = 1.0000 for the rule engine under
heavy mimicry, produced by a fallback constant (the evaluation record contains no
ROC-AUC field).

**Resolution.** The manuscripts never report 1.0000. A genuine continuous
severity-weighted anomaly score is computed per edge and used for AUC, giving
ROC-AUC 0.953 ± 0.031 and PR-AUC 0.740 ± 0.080. The fallback is discussed as a
defect in the integrity section.

## Finding 3 — "10-seed" results were actually single-seed

**Problem.** Aggregated results were reported as multi-seed but originated from a
single seed.

**Resolution.** All reported aggregates are true per-seed means over seeds
1,7,13,21,42,99,123,256,512,1024 (10 seeds) or 1,7,13,21,42 (5 seeds for
generalization). Seed counts are stated in every table caption, and per-seed raw
files are released.

## Finding 4 — DARPA experiments silently fell back to synthetic graphs

**Problem.** When parsed DARPA CSVs were missing, the pipeline fell back to
synthetic graphs without signalling it, so "DARPA" results could be synthetic.

**Resolution.** The corrected real-data experiment loads the actual parsed Theia
CSVs and records the source path and load counts in every raw file
(`audit/raw_runs/darpa/theia3_50000.json`, `theia5m_50000.json`). It never falls
back. The two unavailable scenarios (1r, 6r) are reported as unavailable, not
estimated.

## Finding 5 — additional DARPA-related issue

**Problem.** The original material blurred real DARPA attack labels with
synthetic injections, and used a silent 50,000-edge truncation.

**Resolution.** The manuscripts explicitly separate real labels (none used) from
synthetic post-collection poisoning, state the 50,000-edge cap, and describe the
experiments as "real provenance with synthetic post-collection poisoning" in
every table, caption and paragraph. `audit/FINAL_RESULTS/DATASET_SUMMARY.md`
records the category separation.

## Additional defects documented (not used as results)

| Defect | Treatment |
|---|---|
| Deleted-edge-scoring universe (0.845 vs 0.805) | Both disclosed; corrected universe reported |
| Double-counted deleted-edge ids in ground truth | Corrected ground truth used; discrepancy quantified |
| Mimicry edges carrying a `mimicry` attribute | Attribute verified unused by all detectors; flagged as latent risk |
| Shallow-copy mutation of input graph | Corrected injector deep-copies and asserts integrity |
| Inert rules (unspawned-process, timestamp) | Reported as inert rather than claimed necessary |

## Verification

* 137 manuscript numerical claims checked against verified source data, 0
  discrepancies after fixing one rounding error (0.329 → 0.328).
* 1,890 metric recomputations from confusion matrices, 0 mismatches.
* Deterministic re-run of seeds 1, 42, 1024 reproduces stored raw files exactly.
