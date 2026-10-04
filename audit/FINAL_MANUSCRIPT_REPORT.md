# Final Manuscript Pass — Report

This report covers the final experimental + manuscript pass requested after the
corrected audit. The corrected audit (`audit/final_audit_report.md` and
companions) is treated as the authoritative source of truth. No earlier flawed
methodology was re-run, no paper number was used where it conflicts with the
corrected audit, and no result was invented, smoothed, estimated, interpolated or
"fixed".

## Deliverables

| # | Deliverable | Location | Status |
|---|---|---|---|
| 1 | Final manuscript report | `audit/FINAL_MANUSCRIPT_REPORT.md` | this file |
| 2 | FINAL_RESULTS package | `audit/FINAL_RESULTS/` | complete |
| 3 | Proposal | `audit/final_proposal.md` | complete |
| 4 | Conference manuscript | `final_manuscripts/conference/` | complete, 6 pp PDF |
| 5 | Journal manuscript | `final_manuscripts/journal/` | complete, 9 pp PDF |
| 6 | Paper source package | `audit/FINAL_RESULTS/paper_sources/` | complete |
| 7 | Final figures | `audit/FINAL_RESULTS/figures/` | 7 figures, PNG+PDF+source CSV |
| 8 | Final tables | `audit/FINAL_RESULTS/tables/{csv,markdown,latex}/` | 9 tables |
| 9 | Dataset summary | `audit/FINAL_RESULTS/DATASET_SUMMARY.md` | complete |
| 10 | Manuscript validation | `audit/manuscript_validation/` | 137 claims, 0 discrepancies |
| 11 | Run log | `audit/final_manuscript_pass.log` | complete |

## FINAL_RESULTS (/1)

The single convenient inspection point. 156+ files: final numbers, dataset
summary, experimental protocol, reproducibility notes, limitations, raw results
(copied from `audit/raw_runs/`), statistics, and figures/tables in three formats.
See `audit/FINAL_RESULTS/README.md`.

## Numerical provenance (source of truth)

`audit/FINAL_RESULTS/FINAL_NUMBERS.md` is the numerical source of truth. Every
value is re-derived from `audit/raw_runs/` by `audit/scripts/final_validation.py`
(previously: 1,890 metric recomputations, 0 mismatches; 226 checks, 0
discrepancies). Values stay at full precision in the CSV artifacts; rounding is
display-only.

## Manuscripts

Two complete manuscripts were written and compiled:

* **Conference** — 6 pages, IEEE conference style; contributions, related work,
  threat model, method, protocol, main results, robustness, ablation, scalability.
* **Journal** — 9 pages, IEEE journal style; full sections for parsing,
  evaluation protocol, cross-dataset generalization, poisoning ground-truth
  validity, leakage integrity, ROC-AUC verification, scalability, statistics,
  discussion, limitations, reproducibility. The journal version is the extended
  counterpart of the conference paper.

Both use only corrected-audit numbers. The intellectually central result - that
the conventional GraphSAGE protocol inflates F1 by 0.342 absolute through
threshold-on-test leakage - is presented as a first-class finding in both.

## Figures generation (part 7)

All 7 final figures are generated programmatically by
`audit/scripts/gen_final_figures.py` from verified data or a deterministic
re-run, each with PNG, PDF and a sibling source CSV. The ROC/PR figure uses the
genuine continuous severity-weighted score (not a fallback). See
`audit/FINAL_RESULTS/figures/FIGURE_SOURCE_MAP.md`.

## Tables generation (part 8)

`audit/scripts/make_manuscript_tables.py` builds 9 tables (CSV + Markdown +
LaTeX) from the verified tables; `audit/scripts/make_latex_tables.py` produces
curated booktabs LaTeX for the manuscripts. No number is typed by hand.

## Manuscript numerical audit (part 11)

`audit/manuscript_validation/check_conference.py` and `check_journal.py` compare
every empirical number against the verified source: 48 + 89 = 137 claims, all
matching. One real rounding error was found (0.329 vs 0.328467) and the
manuscript was corrected. Report:
`audit/manuscript_validation/manuscript_validation_report.md`.

## Reproducibility commands (part 12)

```
# environment
pip install numpy pandas scikit-learn scipy matplotlib networkx tqdm fastavro \
            torch torch-geometric

# regenerate all tables and figures from verified raw results
python3 audit/scripts/make_final.py
python3 audit/scripts/make_manuscript_tables.py
python3 audit/scripts/make_latex_tables.py
python3 audit/scripts/build_final_results.py
python3 audit/scripts/gen_final_figures.py

# validate
python3 audit/scripts/final_validation.py
python3 audit/scripts/independent_recheck.py
python3 audit/manuscript_validation/check_conference.py
python3 audit/manuscript_validation/check_journal.py

# compile
cd final_manuscripts/conference && pdflatex conference_paper.tex   # twice
cd final_manuscripts/journal    && pdflatex journal_paper.tex      # twice
```

The complete command transcript with exit codes and results is in
`audit/final_manuscript_pass.log`.

## Safety constraints honoured

* No experimental result modified to match the paper.
* No parameter tuned to improve the proposed method.
* No inconvenient result deleted.
* No methodology silently fixed and re-presented as original.
* Original implementation preserved (`audit/original_results_backup/`).
* Real and synthetic evaluations are separated in every table and in the text.
* Fabricated ROC-AUC removed; genuine continuous score used.
* Leakage-free protocol used for all GraphSAGE numbers; leaky value reported
  only as a defect.
* Deleted-edge scoring differs from the repo convention; both are disclosed.

## Key verified numbers used

| Quantity | Value |
|---|---|
| Rule Engine synthetic F1 | 0.8048 ± 0.0627 |
| Rule Engine synthetic precision / recall | 0.7146 / 0.9329 |
| Rule Engine synthetic ROC-AUC / PR-AUC | 0.9528 / 0.7403 |
| GraphSAGE leakage-free synthetic F1 | 0.3224 ± 0.1942 |
| Paired F1 difference (RE − GS) | +0.482, 95% CI [0.328, 0.636], dz 2.24, p = 0.0020 |
| Leaky vs clean GraphSAGE F1 | 0.5876 vs 0.2461 (inflation 0.3415) |
| Theia 3 RE F1 (synthetic poisoning) | 0.8347 ± 0.0459 |
| Theia 5m RE F1 (synthetic poisoning) | 0.8504 ± 0.0599 |
| Mimicry RE F1 (none→heavy) | 0.8048 unchanged |
| Scalability | linear to 1M edges; ~2.9e4 edges/s |
