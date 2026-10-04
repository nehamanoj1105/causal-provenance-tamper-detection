# Phase 3 — Manuscript Rewrite + Final Numerical Audit

Authoritative sources: `audit/FINAL_RESEARCH_REPORT/verified_numbers.json` /
`.csv` (549 verified claims, recomputed from `audit/raw_runs/`) and
`audit/FINAL_RESULTS/tables/csv/`. Nothing in the manuscripts is typed by hand:
every empirical number resolves to one of those artifacts.

## 1. Manuscripts updated

| Manuscript | Source | Pages | Tables | Figures |
|---|---|---|---|---|
| Conference (`final_manuscripts/conference/`) | rewritten from Phase 1 verified values + corrected Phase 2 PPT | 6 | 9 | 7 |
| Journal (`final_manuscripts/journal/`) | expanded/restructured from the conference paper, contribution and methodology preserved | 9 | 10 | 7 |

Additions in Phase 3:
- Conference: an explicit GraphSAGE value-reconciliation paragraph (three
  values: 0.5600 leaky seed-42, 0.588 leaky 10-seed, 0.322 ± 0.194 corrected).
- Journal: a new "Reconciliation of reported values" subsection plus
  `tables/table10_reconciliation.tex`, recording every changed value with reason.
- Both READMEs updated with the reconciliation and the consolidated audit result.

## 2. Final numerical audit

`audit/scripts/final_numerical_audit.py` → `audit/final_numerical_audit.json`.

| Check | Result |
|---|---|
| Conference numeric claims | 48 ok / 0 discrepancies |
| Journal numeric claims | 89 ok / 0 discrepancies |
| Retracted-value misuse | 0 |
| Manuscript-vs-audit table mismatches | 0 (all 9 tables byte-identical) |
| LaTeX errors | 0 |
| Undefined references / citations | 0 |
| Overfull boxes | 0 |
| Page counts | conference 6, journal 9 |
| **Overall** | **PASS** |

## 3. GraphSAGE discrepancy — resolved explicitly

The Phase 1 checkpoint reported `0.3224` corrected and `0.5600` leaky, while an
earlier manuscript artifact contained `0.246` / `0.588`. These are not
competing estimates of the same quantity:

| Value | Protocol | Seeds | Role |
|---|---|---|---|
| 0.5600 | leaky (repo, seed 42) | 1 | ORIGINAL — audit comparison only |
| 0.588 | leaky | 10 | ORIGINAL — audit comparison only |
| 0.246 | leakage-free | 10 | CORRECTED — per-seed mean of the clean protocol |
| 0.3224 ± 0.1942 | leakage-free | 10 | CORRECTED — authoritative result used in both papers |

Resolution: the raw verified Phase 1 artifact
(`audit/raw_runs/corrected_multiseed.json`, recomputed from
`audit/raw_runs/synthetic/seed_*.json`) is the authority. The corrected,
leakage-free result is **0.3224 ± 0.1942**; it is used as the generalisation
estimate. The leaky values are retained only inside the audit comparison that
measures the leakage effect and are labelled as such in both papers. No value
was silently chosen and none was tuned.

## 4. Retracted / original-protocol values

None of the following is presented as a final result. Each appears (if at all)
only in an explicitly labelled audit or reconciliation context, verified by the
automated scan:

| Value | Reason |
|---|---|
| Rule Engine ROC-AUC 1.0000 | hard-coded fallback constant, not computed |
| GraphSAGE F1 0.5600 / 0.588 | leaky protocol |
| Mimicry Rule Engine F1 0.0882 | invalid generator (attribute leak) |
| Scalability 15.26 s / 364 MB | uncorrected measurement |
| Unit tests 103 | actual is 98 passed / 5 failed |
| Synthetic RE F1 0.6154 / 0.7222 | superseded single-seed values |
| DARPA 4-scenario average | only 2 scenarios available |

## 5. Category separation (enforced throughout)

- **Corrected results** — the leakage-free, label-free protocol; the only results
  used as findings.
- **Original/leaky results** — retained solely for the audit comparison of the
  leakage effect.
- **Real DARPA/Theia data** — Theia E3 scenarios 3 and 5m, truncated to the first
  50,000 edges, used only to test detection on real graph structure.
- **Synthetic post-collection poisoning** — every attack on the real graphs is a
  synthetic injection; the papers never claim detection of naturally occurring
  DARPA attacks.

## 6. Validation of build, references, tables, figures, numbers

- Both PDFs compile with `pdflatex` (TeX Live 2025): 0 errors, 0 undefined
  references, 0 overfull boxes.
- Conference 6 pages, journal 9 pages (as intended).
- All 9 shared tables byte-identical to `audit/FINAL_RESULTS/tables/csv/`.
- All figures referenced exist in `figures/`.
- 137 empirical claims (48 + 89) verified against the authoritative artifacts.

## 7. Packages

| Artifact | Files | Bytes |
|---|---|---|
| `final_manuscripts/conference_manuscript.zip` | 38 | 1,340,910 |
| `final_manuscripts/journal_manuscript.zip` | 39 | 1,378,076 |

Manifests with SHA-256 per file: `*_manuscript_manifest.json`. Build artifacts
(aux/log/out) are excluded; PDF, TeX, figures, tables and README are included.

## 8. Verdict

Phase 3 complete. Both manuscripts use only verified corrected values, every
changed value is reconciled and documented, no retracted value is presented as a
final result, and the build is clean. Ready for Phase 4 (audit repository).
