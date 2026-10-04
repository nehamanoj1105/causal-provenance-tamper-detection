# Repository notes (agent memory)

## Project
`causal-provenance-tamper-detection` — deterministic semantic-rule engine +
GraphSAGE baseline for detecting poisoning of provenance graphs.

## Environment
- Python 3.13, torch 2.14 CPU, torch-geometric 2.8, sklearn 1.9, numpy 2.5, pandas 3.0.
- Install: `pip3 install -r requirements.txt` then
  `pip3 install torch --index-url https://download.pytorch.org/whl/cpu`.
- `python3 -m pytest -q`: 98 pass / 5 fail. The 5 failures
  (`tests/test_graph_loader.py`) are only because `data/parsed/*.csv` is absent
  (gitignored). This is environmental, not a code bug.

## Running experiments
- `python3 scripts/run_evaluation.py --attack-type all --multiple-seeds`
- `python3 scripts/run_graphsage.py --epochs 30 --seed 42`
- `python3 scripts/run_cross_dataset.py` (falls back to synthetic without data)
- `python3 scripts/run_scalability.py` (slow; ~10 min, run in background)
- `python3 scripts/run_mimicry.py`

## Known methodology facts (verified in audit/)
- GraphSAGE `train_pipeline` trains AND selects the threshold on the same graph
  (`data`); there is no train/val/test split. `create_train_val_test_masks` is
  unused. Train-on-test inflation ≈ F1 0.59→0.25.
- Rule Engine has no continuous score field in `MetricResult`; the reported
  ROC-AUC=1.0 comes from a `getattr(...,1.0)` default. A legitimate
  violation-count score gives 0.85→0.54.
- `inject_poisoning` shallow-copies edges, so reordering/forgery mutate the
  caller's "clean" graph.
- Deletion ground-truth IDs are absent from the final graph and are "detected"
  via ID reconstruction from the synthetic naming scheme.
- Mimicry noise edges carry `attributes={"mimicry": True, ...}` and 52–80% of
  them violate rules (not benign camouflage).
- DARPA `data/parsed/` is not in the repo; the cross-dataset runner silently
  substitutes synthetic graphs. DARPA tables are 50k-edge slices with synthetic
  post-collection attacks (not real DARPA labels).

## Task B (3-phase research package)
- Phase 1 verification engine: `audit/scripts/phase1_verify.py` recomputes every
  reported quantity from `audit/raw_runs/` -> `audit/FINAL_RESEARCH_REPORT/
  verified_numbers.{json,csv}` (549 claims) + `environment.json` +
  `phase1_verification_report.md`. No number is hand-typed.
- Cross-checks: FINAL_RESULTS tables (3/6/8/9) vs verified values = 0 mismatches;
  `final_validation.py` 226 checks / 0 discrepancies (1890 metric recomputations);
  `independent_recheck.py` deterministic seeds 1/42/1024.
- Two internal discrepancies surfaced (NOT fixed): (a) two conflicting ablation
  sources (`raw_runs/ablation/seed_*.json` corrected vs
  `raw_runs/ablation_multiseed.json` repo-protocol); (b) two conflicting mimicry
  sources (`raw_runs/synthetic/*.mimicry` corrected vs `raw_runs/mimicry_audit.json`
  repo-protocol with `mimicry:True` attribute leak). Authoritative = corrected.
- Task B Phase 2 blocker: `Mid_review_PPT_Template.pptx` not in environment.

## Audit artifacts
All audit output lives under `audit/` (reports, `raw_runs/*.json`,
`journal_ready_tables/`, `plots/`, `original_reproduction/`, and
`original_results_backup/` = pre-run committed results).

## Corrected-evaluation results (10 seeds; leakage-free)
- Rule Engine synthetic F1 0.8048 ± 0.0627, ROC-AUC 0.9528 ± 0.0312
  (continuous severity-weighted violation score; no fallback constant).
- GraphSAGE leakage-free F1 0.3224 ± 0.1942 (vs 0.5600 leaky).
- Mimicry-invariant: with label-free, invariant-preserving camouflage the Rule
  Engine F1 is unchanged none→heavy and noise self-violations = 0.
- Ablation: structural rules dominate (without-structural F1 0.3285);
  `UnspawnedProcessRule` contributes 0 on synthetic.
- Real Theia (3 / 5m), 50k-edge cap, synthetic post-collection poisoning:
  Rule Engine F1 0.835 / 0.850; unmodified-graph flag rate 0.038% / 0.014%.
- Paired RuleEngine−GraphSAGE F1 diff +0.4824 (Wilcoxon p=0.0020);
  ROC-AUC diff not significant (p=0.1055).
- Runners: `audit/experiments/run_all.py`; entry points in `audit/README.md`.

## Task B Phase 2 — COMPLETE (mid-review presentation)
- Uploaded template found at `audit/PPT_CONTENT/Causal_Provenance_Mid_Review.pptx.pptx`
  (12 slides). Corrected deck built from it, structure preserved.
- Deliverables in `audit/PPT_CONTENT/`: `MID_REVIEW_PPT_CONTENT.{md,docx}`,
  `PPT_RESULT_SOURCE_MAP.csv` (26 claims), `Causal_Provenance_Mid_Review_CORRECTED.pptx`,
  `PHASE2_CORRECTIONS.md`, `build_corrected_ppt.py`, `build_docx.py`.
- Key corrections: ROC-AUC 1.0000 retracted -> 0.9528±0.0312; tests 103 -> 98/5;
  DARPA 4 -> 2 scenarios; 1M 15.26s/364MB -> 34.48s/~971MB; synthetic RE seed-42
  0.7273/0.5333/0.6154 -> 0.8125/0.6500/0.7222 (ORIGINAL) and 0.7146/0.9329/0.8048
  (CORRECTED 10-seed).
- No `soffice`/LibreOffice in env: PPTX verified via python-pptx, not rasterised.

## Task B Phase 3 — COMPLETE (manuscript rewrite + final numerical audit)
- Conference (6pp) and journal (9pp) manuscripts updated in `final_manuscripts/`.
  All numbers resolve to `audit/FINAL_RESEARCH_REPORT/verified_numbers.*` and
  `audit/FINAL_RESULTS/tables/csv/`; no hand-typed numbers.
- Journal adds `tables/table10_reconciliation.tex` + a reconciliation subsection.
- GraphSAGE discrepancy resolved explicitly: authoritative corrected = 0.3224±0.1942;
  0.5600 (leaky seed-42) and 0.588 (leaky 10-seed) retained only as audit comparison.
- `audit/scripts/final_numerical_audit.py` -> `audit/final_numerical_audit.json`:
  48+89 claims ok, 0 discrepancies, 0 retracted misuse, 0 table mismatches,
  0 LaTeX errors, 0 undefined refs, 0 overfull. Build: conf 6pp, journal 9pp.
- TeX Live 2025 installed (texlive-latex-base/-recommended/-extra/-publishers).
- Packages: `final_manuscripts/{conference,journal}_manuscript.zip` (+ manifests,
  SHA-256 per file) via `audit/scripts/package_manuscripts.py`.
- Report: `audit/PHASE3_MANUSCRIPT_AUDIT.md`.
