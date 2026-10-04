# Final Validation Report

**Scope:** independent verification of every number that will enter the
conference and journal manuscripts, before either is written.

**Method:** `audit/scripts/final_validation.py` re-derives all headline values
directly from `audit/raw_runs/*.json` (never from a Markdown file) and checks
them against `audit/journal_ready_tables/*.csv` and the values quoted in
`audit/final_audit_report.md`. `audit/scripts/independent_recheck.py` re-runs the
corrected pipeline in memory for seeds 1, 42, 1024 and compares to the stored
raw runs.

## 1. Metric recomputation

Every stored confusion matrix (`tp, fp, tn, fn`) was used to independently
recompute precision, recall, F1, accuracy, balanced accuracy, FPR, FNR,
specificity and MCC.

| surface | cells recomputed | mismatches |
|---|---|---|
| synthetic (10 seeds × 2 detectors × 9 metrics) + ablation + DARPA | **1890** | **0** |

No metric in any raw record is inconsistent with its own confusion matrix.

## 2. Number cross-check

`number_crosscheck.csv` — 226 checks.

| result | count |
|---|---|
| MATCH (≤1e-9) | 225 |
| N/A (non-numeric, e.g. throughput ratio) | 1 |
| DISCREPANCY | **0** |

Coverage includes: 10-seed synthetic means/stds/CIs for both detectors (110
checks), mimicry (32), scalability (21), ablation (13), DARPA (12 + 4),
significance tests (8), generalization (6), and 18 provenance/seed assertions.

## 3. Determinism / tamper check

`independent_recheck.json`:

| seed | deterministic match | RE F1 fresh | GS F1 fresh | integrity |
|---|---|---|---|---|
| 1 | True | 0.810811 | 0.500000 | [] |
| 42 | True | 0.848485 | 0.222222 | [] |
| 1024 | True | 0.812500 | 0.000000 | [] |

Fresh in-memory runs reproduce the stored raw runs bit-for-bit; the corrected
poisoning injector reports zero integrity problems.

## 4. Table cross-check

`table_crosscheck.csv` — all 9 tables present in CSV, Markdown and LaTeX
(27 files). Every table is generated programmatically by
`audit/scripts/make_final.py` from `audit/raw_runs/`.

## 5. Figure cross-check

`figure_crosscheck.csv`. Two categories of figures exist:

* **Corrected (usable):** `rule_engine_roc_pr_seed42.png`,
  `scalability_corrected.png`.
* **Stale committed figures** carried from `results/` and mirrored into
  `audit/plots/`: `F1_vs_attack.png` (single-seed), `roc_curve.png` (leakage-era
  GraphSAGE), `robustness_curve.png` (mis-specified mimicry),
  `runtime_vs_edges.png` (different host). These are flagged and are **not**
  used in the manuscripts; all publication figures are regenerated in
  `audit/FINAL_RESULTS/figures/`.

## 6. Resolutions of previously noted cross-artifact differences

1. **`audit/tables/` vs `audit/journal_ready_tables/`** — `audit/tables/` is a
   superseded early snapshot (it omits median/min/max/CI). The authoritative
   directory is `audit/journal_ready_tables/`. Resolved: use journal-ready.
2. **Scoring universe** — the corrected harness scores only edges present in the
   final graph; "repo-style" scoring adds absent deleted-edge ids. Both were
   quantified (`gt_sensitivity`): F1 0.8048 vs 0.8453. The manuscript uses
   **0.8048** (final-graph universe) and states the assumption explicitly.
3. **DARPA provenance label** — raw field is `REAL_DARPA_THEIA_E3`; attacks are a
   separate synthetic post-collection injection. The manuscript always labels
   these as *real data + synthetic poisoning*, never as real attacks.

## 7. Conclusion

No unresolved numerical discrepancy remains. `audit/FINAL_RESULTS/FINAL_NUMBERS.md`
is the single source of truth derived from these verified artifacts.
