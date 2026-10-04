# Journal Manuscript

`journal_paper.tex` — IEEE journal style, 9 pages.

Title: *Causal Consistency as a Defense: Detecting and Auditing Provenance Graph
Poisoning*

## Build

```
pdflatex journal_paper.tex
pdflatex journal_paper.tex   # second pass for references
```

Output: `journal_paper.pdf`. Compiles with 0 errors, 0 undefined references and
0 overfull boxes (TeX Live 2025).

## Contents

| File | Purpose |
|---|---|
| `journal_paper.tex` | Manuscript source |
| `journal_paper.pdf` | Compiled paper |
| `figures/` | 7 figures (PNG + PDF) |
| `tables/` | 9 tables (CSV + LaTeX) |
| `references/` | Bibliography (embedded `thebibliography` used) |
| `supplementary/` | Extended material directory |

## Relationship to the conference paper

Extended version adding: data parsing and preprocessing detail, a full
evaluation-protocol section, cross-dataset generalization, poisoning
ground-truth validity, a dedicated GraphSAGE leakage-integrity section, ROC-AUC
verification, scalability, a statistical-analysis section, discussion, and an
expanded reproducibility section.

## Data provenance

Every number comes from the corrected audit via
`audit/FINAL_RESULTS/tables/csv/`. All 89 empirical claims were checked against
that source (`audit/manuscript_validation/check_journal.py`), 0 discrepancies.
The final consolidated audit (`audit/scripts/final_numerical_audit.py`) reports
0 claim discrepancies, 0 retracted-value misuse, 0 table mismatches, 0 LaTeX
errors, 0 undefined references and 0 overfull boxes. Table 10
(`tables/table10_reconciliation.tex`) records every previously reported value
that differs from the corrected one.

## GraphSAGE value reconciliation

Three GraphSAGE F1 values exist and are not interchangeable. `0.5600` is the
starting repository's seed-42 result under the leaky protocol; `0.588` is that
same leaky protocol averaged over ten seeds; `0.3224 +/- 0.1942` is the
corrected, leakage-free ten-seed result. Only the corrected value is used as a
generalisation estimate. The leaky values appear only in the explicit audit
comparison that quantifies the leak and are labelled as such.

## Scope

As the conference paper, with the additional generalization and integrity
analyses. Categories (real-only, real + synthetic poisoning, synthetic
controlled) are never pooled.
