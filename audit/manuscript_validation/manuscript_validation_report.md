# Manuscript Validation Report

Numerical and reproducibility audit of the two final manuscripts:

* `final_manuscripts/conference/conference_paper.tex`
* `final_manuscripts/journal/journal_paper.tex`

Method: every empirical number is listed with its manuscript location, the value
as written, and a resolver into the verified source tables
(`audit/FINAL_RESULTS/tables/csv/`) or raw run files (`audit/raw_runs/`). The
verified value is read programmatically, never typed. A claim passes when it
equals the verified value at the displayed precision (or is a documented
rounding / inequality / approximation).

## Result

| Manuscript | Claims checked | Match | Discrepancy |
|---|---|---|---|
| Conference (`check_conference.py`) | 48 | 48 | 0 |
| Journal (`check_journal.py`) | 89 | 89 | 0 |

Machine-readable results: `conference_number_check.csv`,
`journal_number_check.csv` (columns: Manuscript Location, Claim,
Manuscript Value, Verified Value, Match, Source).

## Discrepancies found and fixed during the audit

| Manuscript | Claim | As first written | Verified | Action |
|---|---|---|---|---|
| Conference | "without structural" ablation F1 | 0.329 | 0.328467… | corrected to 0.328 |

No other discrepancy was found. The one correction was a genuine rounding error
(`0.328467` rounds to `0.328`, not `0.329`); the manuscript was fixed rather than
the verified value being adjusted.

## Non-numerical checks

* **No fabricated AUC.** The rule-engine AUC in both papers is the mean of the
  per-seed AUC computed from the continuous severity-weighted score; the
  original repository's `1.000` fallback is discussed only as a defect and is
  never reported as a result.
* **Real vs synthetic labels.** Real-data tables are labelled "synthetic
  post-collection poisoning"; no text describes injected attacks as real DARPA
  attacks.
* **Single-seed claims.** Every headline number is a 10-seed (or 5-seed for
  generalization) mean; no single-seed value is presented as a general result.
* **Scalability.** Training and inference are reported separately; no
  training-vs-inference comparison is made.
* **Deletion.** Deleted edges are excluded from scored positives, and the
  alternative scoring universe is disclosed (0.805 vs 0.845).
* **Figures.** Every figure is generated from verified data or a deterministic
  re-run; see `audit/FINAL_RESULTS/figures/FIGURE_SOURCE_MAP.md`.
* **LaTeX.** Both documents compile with 0 errors, 0 undefined references and 0
  overfull boxes (`pdflatex`, TeX Live 2025).

## Relation to the corrected audit

The manuscripts report the corrected-audit numbers only. Where the original
repository's numbers conflict (leaky GraphSAGE F1, fabricated ROC-AUC,
single-seed aggregates, synthetic fallback for DARPA scenarios), the manuscript
either omits them or reports them explicitly as defects. No original number was
used as a result.
