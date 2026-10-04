# Final Audit Report — Causal Provenance Graph Tamper Detection

**Repository:** `nehamanoj1105/causal-provenance-tamper-detection`
**Commit audited:** `d8b8617c4478846ace3b82dbd9fb819c8e2f6a64`
**Audit date:** 2026-10-02
**Scope:** full pipeline re-run, paper-to-code reconciliation, GraphSAGE leakage
audit, poisoning/DARPA/mimicry audits, corrected multi-seed evaluation,
statistical validity, scalability, journal-ready tables.

Nothing in the repository was modified to change results. Pre-run committed
results are preserved in `audit/original_results_backup/`. All new artifacts are
under `audit/`.

---

## 1. Executive Summary

The repository is a coherent, well-structured implementation whose **synthetic
results reproduce exactly at the committed seed**, but whose headline claims do
not survive methodological scrutiny:

1. **Exact reproductions (good news).** The synthetic Rule Engine (seed 42),
   the GraphSAGE run (seed 42), the mimicry table, the rule-level statistics, and
   the single-seed ablation all reproduce bit-for-bit.
2. **The "multi-seed" aggregate is a single seed.** Committed
   `seed_statistics.md` shows `0.8125 ± 0.0000`; the script's own 10-seed run
   yields `0.7921 ± 0.0578` F1. A zero standard deviation over 10 seeds is
   impossible.
3. **GraphSAGE is trained and thresholded on the test set.** There is no
   validation or test split. Correcting this drops GraphSAGE F1 from 0.588 to
   0.246 and ROC-AUC from 0.911 to 0.663.
4. **The Rule Engine ROC-AUC = 1.0000 is fabricated.** `MetricResult` has no
   `roc_auc` field; the value comes from a `getattr(..., default=1.0)` fallback.
   A legitimate violation-count score gives 0.85 → 0.54 as mimicry rises.
5. **DARPA numbers are not reproducible and are not real DARPA attacks.** The
   parsed CSVs are absent; the runner silently substitutes synthetic graphs; and
   all "DARPA" attacks are synthetically injected after truncating to the first
   50,000 edges.
6. **Mimicry is not benign camouflage.** 52–80% of mimicry edges violate the
   rules, and 100% carry a `mimicry=True` attribute.
7. **Seven of fifteen rules contribute nothing** on the benchmark; one
   (`ProcessActivityTemporalRule`) slightly hurts F1.

---

## 2. Repository Integrity

| Check | Result |
|---|---|
| Commit | `d8b8617c…` (shallow clone) |
| Tests | **98 passed, 5 failed** (5 failures are missing-data errors) |
| Dataset present | **No** (`data/parsed/` absent, gitignored) |
| Committed artifacts consistent with code | **No** (single-seed stats labelled as multi-seed; fabricated ROC-AUC) |
| Model checkpoint committed | Yes (`results/graphsage_checkpoint.pt`, despite `*.pt` gitignore) |
| `create_train_val_test_masks` | Defined but **never used** |

Details: `audit/repository_audit.md`.

---

## 3. Paper-to-Code Reconciliation

Full table in `audit/paper_protocol.md` and
`audit/final_result_reconciliation.csv`. Key mismatches:

| Reported | Actual code protocol | Match |
|---|---|---|
| 10-seed mean ± std | single seed 42 with std 0 | No |
| Validation-based threshold | threshold on test labels | No |
| Rule Engine ROC-AUC 1.0 | constant fallback | No |
| DARPA detection | synthetic fallback + 50k truncation + synthetic attacks | No |
| "15 rules" | 7 contribute zero on this benchmark | Misleading |

---

## 4. Original Reproduction Results

Full detail: `audit/original_reproduction_report.md`; raw logs in
`audit/original_reproduction/raw_logs/`.

| Experiment | Verdict |
|---|---|
| Synthetic Rule Engine (seed 42) | Reproduced exactly |
| Synthetic multi-seed aggregate | **Discrepancy** (single seed reported as multi-seed) |
| GraphSAGE (seed 42) | Reproduced exactly (protocol invalid) |
| DARPA 1r/3/5m/6r | **Not reproducible** (data absent) |
| Mimicry | Reproduced exactly |
| Rule statistics | Reproduced exactly |
| Ablation (single seed) | Reproduced exactly |
| Scalability | Partial (≈2× slower host; scaling shape correct) |

---

## 5. GraphSAGE Leakage Findings

Full detail: `audit/graphsage_leakage_audit.md`.

- Train edges = evaluation edges = test edges.
- Threshold tuned on test labels.
- No validation or test split; `create_train_val_test_masks` unused.
- Node degree features and message passing computed on the poisoned test graph.
- Poisoning labels are the training targets on the scored set.

Measured inflation (same 10 seeds): F1 0.588 (leaky) → 0.246 (clean);
ROC-AUC 0.911 → 0.663; MCC 0.559 → 0.168.

---

## 6. Poisoning Ground-Truth Audit

Full detail: `audit/poisoning_ground_truth_audit.md`.

| Attack | Requested | Events | GT ids absent from graph | Detectable | Undetectable | Aliased input edges |
|---|---|---|---|---|---|---|
| random_deletion | 5 | 5 | 50/50 | 49 | 1 | 0 |
| random_insertion | 5 | 5 | 0 | 45 | 5 | 0 |
| random_reordering | 5 | 5 | 0 | 31 | 19 | 5.0 |
| random_dependency_forgery | 5 | 5 | 0 | 35 | 15 | 4.9 |
| targeted_deletion | 5 | 5 | 50/50 | 50 | 0 | 0 |
| targeted_insertion | 5 | 5 | 0 | 48 | 2 | 0 |
| targeted_reordering | 5 | **10** | 0 | 58 | 20 | 0 (deepcopy) |
| targeted_dependency_forgery | 5 | 5 | 0 | 36 | 14 | 5.0 |

Key issues: deletions are scored via ID reconstruction from the synthetic naming
scheme; reordering often leaves semantics unchanged and creates false positives;
forgery is often undetectable; `targeted_reordering` emits duplicate GT IDs; the
shallow copy mutates the caller's "clean" graph for random reorder/forgery.

---

## 7. DARPA Audit

Full detail: `audit/darpa_audit.md`.

- Source CSVs `data/parsed/{1r,3,5m,6r}_{nodes,edges}.csv` are **absent**.
- Benchmarks use the **first 50,000 edges** (silent truncation), then inject
  attacks.
- Attacks are **random**, single seed 42, intensity 5 for all scenarios.
- 20 events vs 15 graph edge records (5 deletions vanish) explains the 15/20
  discrepancy.
- **No real DARPA attack labels are used.** All labels are synthetic
  post-collection poisoning. Any claim of detecting naturally occurring
  provenance poisoning is unsupported.
- Scenario label mapping in `README.md` (1r→TRACE, 3→CADETS, 5m→ClearScope,
  6r→THEIA) contradicts `data/README.md` (all Theia).

---

## 8. Mimicry Audit

Full detail: `audit/mimicry_audit.md`.

| Strength | Noise edges | Flagged by rules | Truly benign | Leaky attributes |
|---|---|---|---|---|
| none | 0 | 0 | 0 | 0 |
| light | 70 | 36.6 | 33.4 | 70/70 |
| medium | 163 | 108.9 | 54.1 | 163/163 |
| heavy | 351 | 281.8 | 69.2 | 351/351 |

Mimicry edges are not benign; they add detectable violations and carry
`mimicry=True` attributes (latent leakage, not currently featurised).

---

## 9. Ablation Audit

Full detail: `audit/ablation_audit.md` (10-seed mean ± std).

| Configuration | F1 |
|---|---|
| ALL | 0.7921 ± 0.0578 |
| Without Structural | 0.6203 ± 0.0789 |
| Without Temporal | 0.7592 ± 0.0569 |
| Without Semantic | 0.5293 ± 0.0619 |

Structural and semantic rules contribute; temporal rules contribute weakly and
one is net-harmful. Seven individual rules contribute exactly zero on this
benchmark.

---

## 10. Scalability Audit

Full detail: `audit/raw_runs/scalability_audit.json`; plots in `audit/plots/`.
5 repetitions per size; GraphSAGE training and inference reported separately.

| Edges | RE detect (s) | GS infer (s) | GS train/epoch (s) | RE peak MB | GS peak MB | RE eps |
|---|---|---|---|---|---|---|
| 10,000 | 0.2756 | 0.0065 | 0.014 | 2.1 | 11.0 | 36,313 |
| 25,000 | 0.7044 | 0.0152 | 0.035 | 4.9 | 25.2 | 35,499 |
| 50,000 | 1.4664 | 0.0284 | 0.068 | 8.6 | 49.9 | 34,102 |
| 100,000 | 3.0174 | 0.0597 | 0.140 | 17.8 | 53.4 | 33,141 |
| 250,000 | 7.9325 | 0.1886 | 0.423 | 43.5 | 55.8 | 31,517 |
| 500,000 | 16.2688 | 0.3766 | 0.889 | 81.8 | 91.7 | 30,735 |
| 1,000,000 | 34.0593 | 0.8425 | 1.909 | 177.1 | 182.8 | 29,362 |

Both scale roughly linearly. Rule Engine detection is ~40× slower than GraphSAGE
*inference*, but GraphSAGE inference assumes a trained model; its per-epoch
training cost is comparable to or above the Rule Engine's single pass. Comparing
Rule Engine inference to GraphSAGE training would be invalid; the audit keeps
them separate.

---

## 11. Multi-Seed Statistics

Full detail: `audit/statistics_audit.md`. Clean protocol, n = 10.

| Metric | Rule Engine (mean ± std) | GraphSAGE clean (mean ± std) |
|---|---|---|
| Precision | 0.3394 ± 0.0465 | 0.2056 ± 0.1006 |
| Recall | 0.7267 ± 0.1063 | 0.4000 ± 0.1257 |
| F1 | 0.4620 ± 0.0621 | 0.2461 ± 0.0580 |
| Accuracy | 0.8581 ± 0.0190 | 0.7788 ± 0.1033 |
| Balanced Accuracy | 0.7984 ± 0.0556 | 0.6067 ± 0.0438 |
| MCC | 0.4310 ± 0.0775 | 0.1682 ± 0.0796 |
| FPR | 0.1299 ± 0.0163 | 0.1866 ± 0.1210 |
| FNR | 0.2733 ± 0.1063 | 0.6000 ± 0.1257 |
| Specificity | 0.8701 ± 0.0163 | 0.8134 ± 0.1210 |
| ROC-AUC | 0.8046 ± 0.0555 | 0.6634 ± 0.0619 |
| PR-AUC | 0.3243 ± 0.0725 | 0.2427 ± 0.0547 |

---

## 12. Statistical Significance

Paired across the same 10 test instances:

| Statistic | Value |
|---|---|
| Mean F1 difference (RE − GS) | 0.2159 |
| 95% CI | [0.1553, 0.2766] |
| Wilcoxon statistic / p | 0.0 / 0.00195 |
| Paired t p | 6.47e-05 |
| Cohen's d_z | 2.21 |

The Rule Engine's F1 advantage is statistically significant and large in effect
size, but the absolute F1 of both detectors is modest. No single-seed claim of
superiority is defensible.

---

## 13. Reproducible Results

- Synthetic Rule Engine metrics at seed 42 (exact).
- GraphSAGE metrics at seed 42 (exact, but leaky).
- Mimicry edge counts and Rule Engine F1/Precision/Recall (exact).
- Rule-level statistics at seed 42 (exact).
- Ablation at seed 42 (exact).
- Scalability scaling shape and memory growth.

## 14. Non-Reproducible Results

- Committed 10-seed aggregate statistics (actually one seed).
- DARPA 1r/3/5m/6r numbers (dataset absent).
- Rule Engine ROC-AUC = 1.0000 (fabricated).
- PR-AUC values equal to `precision × recall`.

---

## 15. Methodological Problems

1. Train/validation/test leakage in GraphSAGE (no split; threshold on test).
2. Fabricated ROC-AUC for a deterministic binary detector.
3. Single-seed results presented as multi-seed aggregates (std = 0).
4. Silent DARPA fallback to synthetic and silent 50k-edge truncation.
5. Synthetic post-collection attacks mislabelled as DARPA provenance poisoning.
6. Mimicry generator produces rule-violating, attribute-tagged "camouflage".
7. Shallow-copy mutation corrupts the clean input graph.
8. Deletion detection relies on reconstructable synthetic edge-ID sequencing.
9. Scalability compares Rule Engine inference to GraphSAGE inference without
   accounting for GraphSAGE training cost.
10. "15 semantic rules" overstates the effective rule set (7 contribute zero).

---

## 16. Recommended Experimental Protocol

1. **Three-way instance split** (train/val/test) with disjoint poisoning
   instances; threshold from validation only.
2. **Report mean ± std and 95% CI over ≥10 seeds**; never present one seed as an
   aggregate.
3. **Continuous scores only for AUC.** Rule Engine AUC from violation-count
   score; GraphSAGE from calibrated probabilities.
4. **Paired tests** (Wilcoxon + effect size) for detector comparisons.
5. **Realistic mimicry**: benign noise that satisfies all invariants and carries
   no ground-truth-like attributes.
6. **Declare all truncation and fallbacks explicitly.**
7. **DARPA**: state that attacks are synthetic post-collection injections;
   report full-graph and sliced results separately; use real DARPA labels if
   available.
8. **Separate GraphSAGE training and inference** in scalability comparisons.
9. **Fix the shallow-copy bug** so the clean graph is never mutated.
10. **Hold out base topologies / scenarios** for genuine generalisation claims.

---

## 17. Exact Numbers Safe to Put in a Journal

- Synthetic Rule Engine @ seed 42: P 0.8125, R 0.6500, F1 0.7222, Acc 0.9457.
- Mimicry noise counts: 0 / 70 / 163 / 351 (none/light/medium/heavy).
- GraphSAGE @ seed 42 **only if** labelled "leaky, non-generalising".
- Rule Engine ROC-AUC / PR-AUC from the violation-count score (0.8502/0.6041 →
  0.5422/0.0373 across strengths), clearly labelled.
- Clean multi-seed means ± std (Section 11), with the protocol described.
- Scalability table (Section 10) with hardware noted.
- Paired significance (Section 12).

## 18. Numbers That Must NOT Be Used

- Committed `seed_statistics.md` multi-seed values (single seed, std 0).
- Rule Engine `ROC-AUC = 1.0000`.
- Any `PR-AUC` equal to `precision × recall`.
- DARPA cross-scenario table as "real DARPA" results.
- GraphSAGE seed-42 metrics presented as generalising performance.
- Any claim that the 15 rules all contribute.
- Any DARPA claim of naturally occurring provenance poisoning.

---

## A. Results reproduced exactly

- Synthetic Rule Engine @ seed 42 (all metrics, confusion counts).
- GraphSAGE @ seed 42 (all metrics; leaky protocol).
- Mimicry table (Rule Engine and GraphSAGE) @ seed 42.
- Rule-level statistics @ seed 42.
- Ablation table @ seed 42.

## B. Results reproduced approximately

- Scalability scaling shape and memory growth (absolute times ≈2× slower on the
  4-vCPU audit host).
- Mimicry multi-seed means (differ from the single committed seed by ~4–8%).

## C. Results not reproducible

- DARPA 1r/3/5m/6r cross-scenario numbers (dataset absent).
- Committed multi-seed aggregate (was a single seed).

## D. Results invalid under rigorous evaluation

- GraphSAGE metrics under the original train-on-test protocol.
- Rule Engine ROC-AUC = 1.0000 and the `precision × recall` PR-AUC.
- Any DARPA row interpreted as detecting real DARPA attacks.

## E. Corrected journal-safe results

- Clean-protocol multi-seed means ± std and 95% CI (Section 11).
- Violation-count ROC-AUC / PR-AUC for the Rule Engine (Section 6 of
  `rule_engine_roc_audit.md`).
- Paired significance (Section 12).
- Honest scalability with separated training/inference (Section 10).
- Poisoning/mimicry ground-truth audits (Sections 6, 8).

## F. Remaining experiments required before journal submission

1. Re-run the corrected protocol on **real DARPA data** (full graphs and
   declared slices) with real or clearly-labelled synthetic labels.
2. Hold out **base topologies/scenarios** to test topology generalisation.
3. Replace the mimicry generator with invariant-preserving, attribute-free noise
   and re-run robustness.
4. Fix the shallow-copy mutation bug and re-run all poisoning-dependent results.
5. Add per-rule ablation on DARPA data.
6. Multi-seed (≥10) DARPA evaluation with paired statistics.
7. Calibrate GraphSAGE probabilities before reporting AUC.
8. Repeat on a GPU host to confirm device-independence of GraphSAGE numbers.
