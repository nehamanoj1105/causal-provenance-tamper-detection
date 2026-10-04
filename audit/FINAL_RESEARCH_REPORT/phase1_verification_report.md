# Task B — Phase 1 verification report

Status: **COMPLETE**. Phase 1 built and ran a from-scratch verification engine that
recomputes every reported quantity directly from the raw artifacts in
`audit/raw_runs/`. No number is copied from an earlier report.

## What Phase 1 produced

| Artifact | Description |
|---|---|
| `audit/scripts/phase1_verify.py` | Verification engine (reads `audit/raw_runs/`, recomputes all statistics) |
| `audit/FINAL_RESEARCH_REPORT/verified_numbers.json` | Full-precision machine-readable verified values, one entry per claim |
| `audit/FINAL_RESEARCH_REPORT/verified_numbers.csv` | Flat full-precision table (claim, n, mean, std, median, min, max, CI, source) |
| `audit/FINAL_RESEARCH_REPORT/environment.json` | Frozen environment fingerprint |
| `audit/FINAL_RESEARCH_REPORT/phase1_verification_report.md` | This file |

Sections recomputed: `synthetic, mimicry, ablation, ablation_repo_protocol,
generalization, real_theia, scalability, leakage, scoring_universe, poisoning,
mimicry_audit, rule_score, rule_statistics`.

## Independent cross-checks performed in Phase 1

1. **Verified values vs. the authoritative result tables.** Every row of
   `audit/FINAL_RESULTS/tables/csv/table3_main_detection.csv`,
   `table6_mimicry.csv`, `table8_scalability.csv`, `table9_real_data_poisoning.csv`
   was compared field-by-field against `verified_numbers.json`:
   **0 mismatches** (tolerance 1e-9 for metrics, 1e-6 for timings).
2. **Determinism.** Re-running `run_seed(1)` from the corrected harness reproduced
   the stored `audit/raw_runs/synthetic/seed_1.json` exactly for graph sizes,
   ground-truth counts and all Rule-Engine/GraphSAGE metrics (bit-identical).
3. **Test suite.** `python3 -m pytest -q` → **98 passed, 5 failed**; the 5
   failures are all `tests/test_graph_loader.py` and are caused solely by the
   absence of `data/parsed/*.csv` (gitignored). No code defect.
4. **Figure regeneration.** `audit/scripts/gen_final_figures.py` re-ran clean and
   rewrote all 9 figures + sibling CSVs from `raw_runs/`.

## Discrepancies found during Phase 1 (recorded, not "fixed")

These are genuine internal inconsistencies in the repository that must be
reported to the user. They are **not** corrected here.

1. **Two conflicting ablation sources.**
   - Authoritative (`audit/raw_runs/ablation/seed_*.json`, written by
     `audit/experiments/ablation/run_ablation.py`, 10 seeds, corrected harness):
     ALL-rules F1 **0.8048 ± 0.0627**, without-structural **0.3285 ± 0.0731**,
     without-semantic **0.8048 ± 0.0627** (semantic group = UnspawnedProcessRule
     only), without-temporal **0.7983 ± 0.0055**.
   - Repo-protocol (`audit/raw_runs/ablation_multiseed.json`, written by
     `audit/scripts/audit_ablation.py` via `src/eval/ablation.py`, 10 seeds):
     ALL-rules F1 **0.7921 ± 0.0578**, without-structural **0.6203 ± 0.0789**,
     without-semantic **0.5293 ± 0.0619**, without-temporal **0.7592 ± 0.0569**.
   - Cause: the two use different rule-group definitions (e.g. SpawnConsistency/
     Execution/ReadWrite/Network/Delete are "structural" in the repo, "semantic"
     in the corrected harness; SequenceGap is "temporal" in the repo,
     "structural" in the corrected harness) and different ground-truth/score
     definitions. Only the corrected source is used in the manuscripts; the
     repo-protocol numbers are retained in `verified_numbers.json` under
     `ablation_repo_protocol` for traceability.

2. **Two conflicting mimicry sources.**
   - Corrected (`audit/raw_runs/synthetic/seed_*.json::mimicry`, generated with
     `audit/experiments/mimicry/mimicry_v2.py`): label-free, invariant-preserving
     camouflage; Rule-Engine F1 is unchanged none→heavy at 0.8048, noise
     self-violations = 0.
   - Repo (`audit/raw_runs/mimicry_audit.json`, generated with
     `src/detection/mimicry_attack.py`): noise edges carry
     `attributes={"mimicry": True}` (attribute leak) and 52–80 % of them violate
     rules, so precision/F1 collapse (0.81 → 0.08). This is a detector-visible
     attribute leak and non-benign camouflage, documented in
     `audit/mimicry_audit.md`.

3. **Two ablation script families** both present:
   `audit/scripts/audit_ablation.py` (repo functions) and
   `audit/experiments/ablation/run_ablation.py` (corrected harness). Both write
   under `audit/raw_runs/`; only the latter's output is authoritative.

## What Phase 1 did NOT do

- Did not modify any experimental result, parameter, or methodology.
- Did not overwrite any paper value.
- Did not resolve the discrepancies above; they are surfaced for the user.

## Environment note (resolved)

The session environment had lost its Python packages (`import numpy` failed).
Core scientific packages (numpy, scipy, scikit-learn, pandas, matplotlib,
networkx, psutil, fastavro), CPU PyTorch 2.14.1 and PyG 2.8.0.post1 were
re-installed from the official registries / PyTorch CPU index so the original
pipeline could be re-run. Versions match those recorded at Task A.
