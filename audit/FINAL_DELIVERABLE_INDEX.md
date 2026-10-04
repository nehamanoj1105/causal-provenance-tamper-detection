# Final Deliverable Index

Complete inventory of the final-pass deliverables, with a one-line description and
a verification status for each. Every number referenced anywhere traces back to
`audit/raw_runs/` through the scripts listed in `audit/FINAL_MANUSCRIPT_REPORT.md`.

## 1. Manuscripts

| Deliverable | Path | Status |
|---|---|---|
| Conference paper (LaTeX) | `final_manuscripts/conference/conference_paper.tex` | 6 pp, compiles clean |
| Conference paper (PDF) | `final_manuscripts/conference/conference_paper.pdf` | 0 errors / 0 undef / 0 overfull |
| Journal paper (LaTeX) | `final_manuscripts/journal/journal_paper.tex` | 9 pp, compiles clean |
| Journal paper (PDF) | `final_manuscripts/journal/journal_paper.pdf` | 0 errors / 0 undef / 0 overfull |
| Figures | `final_manuscripts/{conference,journal}/figures/` | 7 figures, PNG + PDF |
| Tables | `final_manuscripts/{conference,journal}/tables/` | 9 tables, CSV + LaTeX |
| Bibliography | `final_manuscripts/conference/references/references.bib` | 15 entries |

## 2. FINAL_RESULTS package

| Deliverable | Path |
|---|---|
| Inspection guide | `audit/FINAL_RESULTS/README.md` |
| Numerical source of truth | `audit/FINAL_RESULTS/FINAL_NUMBERS.md` |
| Dataset summary | `audit/FINAL_RESULTS/DATASET_SUMMARY.md` |
| Experimental protocol | `audit/FINAL_RESULTS/EXPERIMENTAL_PROTOCOL.md` |
| Reproducibility | `audit/FINAL_RESULTS/REPRODUCIBILITY.md` |
| Limitations | `audit/FINAL_RESULTS/LIMITATIONS.md` |
| Raw results | `audit/FINAL_RESULTS/raw_results/` |
| Statistics | `audit/FINAL_RESULTS/statistics/` |
| Dataset/model/robustness/ablation/scalability result bundles | `audit/FINAL_RESULTS/{dataset_results,model_results,robustness,ablation,scalability}/` |
| Figures (PNG/PDF + source CSV) | `audit/FINAL_RESULTS/figures/` |
| Figure source map | `audit/FINAL_RESULTS/figures/FIGURE_SOURCE_MAP.md` |
| Tables (CSV/Markdown/LaTeX) | `audit/FINAL_RESULTS/tables/` |
| Paper source package | `audit/FINAL_RESULTS/paper_sources/` |

## 3. Reports

| Deliverable | Path |
|---|---|
| Final manuscript report | `audit/FINAL_MANUSCRIPT_REPORT.md` |
| Final proposal | `audit/final_proposal.md` |
| Reviewer feedback resolution | `audit/reviewer_feedback_resolution.md` |
| Manuscript validation report | `audit/manuscript_validation/manuscript_validation_report.md` |
| Corrected audit report | `audit/final_audit_report.md` (pre-existing, authoritative) |
| Result reconciliation | `audit/final_result_reconciliation.csv` (pre-existing) |
| Leakage audit | `audit/graphsage_leakage_audit.md` (pre-existing) |
| Poisoning ground-truth audit | `audit/poisoning_ground_truth_audit.md` (pre-existing) |
| Original reproduction report | `audit/original_reproduction_report.md` (pre-existing) |
| Run log | `audit/final_manuscript_pass.log` |

## 4. Verification scripts

| Script | Purpose | Last result |
|---|---|---|
| `audit/scripts/final_validation.py` | Recompute metrics, cross-check numbers | 1,890 recomputed, 0 mismatches; 226 checks, 0 discrepancies |
| `audit/scripts/independent_recheck.py` | Determinism re-run | seeds 1/42/1024 deterministic |
| `audit/manuscript_validation/check_conference.py` | Conference number audit | 48/48 match |
| `audit/manuscript_validation/check_journal.py` | Journal number audit | 89/89 match |
| `audit/scripts/make_final.py` | Aggregate all tables | exit 0 |
| `audit/scripts/make_manuscript_tables.py` | Build manuscript tables | exit 0 |
| `audit/scripts/make_latex_tables.py` | Curated LaTeX tables | exit 0 |
| `audit/scripts/build_final_results.py` | Build FINAL_RESULTS | exit 0 |
| `audit/scripts/gen_final_figures.py` | Build final figures | exit 0 |

## 5. Verification status

| Check | Result |
|---|---|
| Conference claims match verified data | 48 / 48 |
| Journal claims match verified data | 89 / 89 |
| Metric recomputation mismatches | 0 |
| Cross-check discrepancies | 0 |
| Determinism | exact for seeds 1, 42, 1024 |
| LaTeX errors | 0 |
| Undefined references | 0 |
| Overfull boxes | 0 |

## 6. Explicitly not delivered (and why)

| Not delivered | Reason |
|---|---|
| Theia 1r / 6r results | Datasets unavailable (HTTP 403 quota); not estimated |
| Real DARPA attack detection results | No usable real attack labels; all DARPA numbers are synthetic post-collection poisoning |
| Genuine cross-graph GraphSAGE transfer | Not implemented; reported as target-trained |
| Deletion detection rate | Deleted edges cannot be edge-matched; excluded and disclosed |
| Manuscript rewrite of the original paper | Out of scope for this pass; corrected result set established first |
