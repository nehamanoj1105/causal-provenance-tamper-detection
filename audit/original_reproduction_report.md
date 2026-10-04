# Original Reproduction Report (Phase 3)

**Label:** ORIGINAL-REPRODUCTION — the current repository code was run unchanged.
No parameters were tuned, no results edited, no inconvenient runs dropped.

Raw logs: `audit/original_reproduction/raw_logs/`. Copies of regenerated CSVs /
MD / JSON: `audit/original_reproduction/csv/`. Pre-run committed results are
preserved untouched in `audit/original_results_backup/`.

Tolerance: `numerical equality` if |abs error| ≤ 1e-4; `close` if relative error
≤ 1%; otherwise `discrepancy`.

## 1. Synthetic benchmark (Rule Engine)

| Metric | Paper/committed (seed 42) | Reproduced (seed 42) | Abs err | Rel err | Verdict |
|---|---|---|---|---|---|
| Precision | 0.8125 | 0.8125 | 0.0000 | 0.000% | numerical equality |
| Recall | 0.6500 | 0.6500 | 0.0000 | 0.000% | numerical equality |
| F1 | 0.7222 | 0.7222 | 0.0000 | 0.000% | numerical equality |
| Accuracy | 0.9457 | 0.9457 | 0.0000 | 0.000% | numerical equality |
| TP/FP/TN/FN | 13/3/161/7 | 13/3/161/7 | 0 | 0% | numerical equality |

**Verdict: REPRODUCED EXACTLY** for seed 42.

### 1b. Synthetic "multi-seed" aggregate — DISCREPANCY

| Metric | Committed (`results/seed_statistics.md`) | Reproduced (10 seeds) | Abs err | Rel err | Verdict |
|---|---|---|---|---|---|
| Precision | 0.8125 ± 0.0000 | 0.8039 ± 0.0696 | -0.0086 | -1.06% | discrepancy |
| Recall | 0.6500 ± 0.0000 | 0.7900 ± 0.1022 | +0.1400 | +21.5% | discrepancy |
| F1 | 0.7222 ± 0.0000 | 0.7921 ± 0.0578 | +0.0699 | +9.68% | discrepancy |
| Accuracy | 0.9457 ± 0.0000 | 0.9554 ± 0.0111 | +0.0097 | +1.03% | discrepancy |

**Root cause:** the committed statistics are the single seed-42 result reported
with a zero standard deviation; they are not a 10-seed aggregate. The code's own
`DEFAULT_SEEDS` list contains all 10 seeds and the script runs them. The
committed `attack_breakdown.md` contains exactly one row (`all | 42`). This is a
**reporting error**, not a stochastic discrepancy.

## 2. GraphSAGE benchmark

| Metric | Committed | Reproduced | Abs err | Rel err | Verdict |
|---|---|---|---|---|---|
| Optimal threshold | 0.70 | 0.70 | 0.00 | 0% | numerical equality |
| Precision | 0.7000 | 0.7000 | 0.0000 | 0% | numerical equality |
| Recall | 0.4667 | 0.4667 | 0.0000 | 0% | numerical equality |
| F1 | 0.5600 | 0.5600 | 0.0000 | 0% | numerical equality |
| Accuracy | 0.9385 | 0.9385 | 0.0000 | 0% | numerical equality |
| ROC-AUC | 0.8776 | 0.8776 | 0.0000 | 0% | numerical equality |
| PR-AUC | 0.5634 | 0.5634 | 0.0000 | 0% | numerical equality |
| MCC | 0.5410 | 0.5410 | 0.0000 | 0% | numerical equality |

**Verdict: REPRODUCED EXACTLY.** (This protocol is nonetheless methodologically
invalid — see Phase 4.)

## 3. DARPA cross-scenario

| Dataset | Committed Rule Engine F1 | Reproduced | Verdict |
|---|---|---|---|
| 1r | 0.4783 | — | **UNVERIFIABLE** |
| 3 | 0.4706 | — | **UNVERIFIABLE** |
| 5m | 0.4571 | — | **UNVERIFIABLE** |
| 6r | 0.3438 | — | **UNVERIFIABLE** |
| synthetic | 0.7222 | 0.7222 | numerical equality |

**Verdict: NOT REPRODUCIBLE from the repository.** `data/parsed/` is absent and
gitignored; `scripts/run_cross_dataset.py` discovers zero datasets and silently
evaluates only the synthetic graph. The committed DARPA numbers cannot be
regenerated without the separately-downloaded CSVs.

## 4. Mimicry robustness

| Strength | Detector | Metric | Committed | Reproduced | Verdict |
|---|---|---|---|---|---|
| none | Rule Engine | F1 | 0.7778 | 0.7778 | numerical equality |
| light | Rule Engine | F1 | 0.3000 | 0.3000 | numerical equality |
| medium | Rule Engine | F1 | 0.1657 | 0.1657 | numerical equality |
| heavy | Rule Engine | F1 | 0.0882 | 0.0882 | numerical equality |
| none | Rule Engine | ROC-AUC | 1.0000 | 1.0000 | numerical equality (but fabricated — Phase 6) |
| heavy | GraphSAGE | F1 | 0.1067 | 0.1067 | numerical equality |
| heavy | GraphSAGE | ROC-AUC | 0.7333 | 0.7333 | numerical equality |
| noise edges (light/medium/heavy) | — | count | 70/163/351 | 70/163/351 | numerical equality |

**Verdict: REPRODUCED EXACTLY**, including the fabricated Rule Engine ROC-AUC
(the code hard-codes it).

## 5. Rule-level statistics (seed 42)

All 15 rows of `results/rule_statistics.md` reproduced exactly
(e.g. `SequenceGapRule` 5 violations / TP5 / FN15; `SequenceMonotonicityRule`
6 violations / TP3 / FP3).

**Verdict: REPRODUCED EXACTLY** (single seed).

## 6. Rule-group ablation (seed 42)

| Configuration | Committed F1 | Reproduced F1 | Verdict |
|---|---|---|---|
| ALL Rules | 0.7222 | 0.7222 | numerical equality |
| Without Structural | 0.5161 | 0.5161 | numerical equality |
| Without Temporal | 0.6667 | 0.6667 | numerical equality |
| Without Semantic | 0.5161 | 0.5161 | numerical equality |

**Verdict: REPRODUCED EXACTLY** (single seed; multi-seed audit in Phase 10).

## 7. Scalability

Sizes and detector shapes reproduce; absolute times are hardware-dependent.

| Size | Detector | Committed time (s) | Reproduced time (s) | Committed eps | Reproduced eps |
|---|---|---|---|---|---|
| 10,000 | Rule Engine | 0.1470 | 0.2729 | 68,025 | 36,640 |
| 100,000 | Rule Engine | 1.4513 | 3.0585 | 68,906 | 32,696 |
| 1,000,000 | Rule Engine | 16.9903 | 33.7208 | 58,857 | 29,655 |
| 1,000,000 | GraphSAGE Inference | 0.5271 | 0.8593 | 1,897,309 | 1,163,698 |

**Verdict: PARTIAL.** Scaling behaviour (roughly linear in edges) is reproduced;
absolute throughput is ≈2× lower on the 4-vCPU audit host. Memory footprints are
close (1M edges: RE peak 361.6 MB committed vs 381.1 MB reproduced).

## 8. Summary of original-reproduction verdicts

| Experiment | Verdict |
|---|---|
| Synthetic Rule Engine (seed 42) | Reproduced exactly |
| Synthetic multi-seed aggregate | **Discrepancy — committed value is a single seed** |
| GraphSAGE (seed 42) | Reproduced exactly (protocol invalid) |
| DARPA 1r/3/5m/6r | Not reproducible (data absent) |
| Mimicry | Reproduced exactly |
| Rule statistics | Reproduced exactly |
| Ablation | Reproduced exactly (single seed) |
| Scalability | Partial (hardware-dependent timing) |
