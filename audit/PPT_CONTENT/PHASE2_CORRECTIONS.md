# Phase 2 — Mid-Review presentation: corrections applied

Template: `Causal_Provenance_Mid_Review.pptx.pptx` (uploaded, 12 slides, 16:9).
Corrected deck: `Causal_Provenance_Mid_Review_CORRECTED.pptx` (same template,
data-bearing cells/notes replaced). Builders: `build_corrected_ppt.py`,
`build_docx.py`.

## Corrections applied to the template

| Slide | Template value / claim | Corrected value | Reason |
|---|---|---|---|
| 7 | Datasets: DARPA TC E3 "TRACE (1r), CADETS (3), ClearScope (5m), THEIA (6r)" | Theia '3' and Theia '5m' only; **1r and 6r unavailable** | Only 2 of 4 scenarios present in the environment; 1r/6r must not be fabricated. |
| 7 | "103 unit tests (pytest)" | **98 passed / 5 failed** | Verified by running `pytest -q`; the 5 failures are environmental (absent gitignored `data/parsed/`). |
| 7 | Training config: "30 epochs, seed 42, tau*=0.70" | ORIGINAL config + **CORRECTED 60/20/20 split, validation-only threshold** | Documents the leakage-free protocol. |
| 10 | Synthetic Rule Engine 0.7273 / 0.5333 / 0.6154 | **0.8125 / 0.6500 / 0.7222** (ORIGINAL seed 42) and **0.7146 / 0.9329 / 0.8048** (CORRECTED 10-seed) | Template value matched no verified artifact; the committed seed-42 value is 0.8125/0.6500/0.7222 and the authoritative multi-seed value is 0.7146/0.9329/0.8048. |
| 10 | GraphSAGE rows (0.5455/0.4000/0.4615 and 0.7000/0.4667/0.5600) | ORIGINAL leaky 0.7000/0.4667/0.5600 **and** CORRECTED 0.3416/0.5017/0.3224 | Both protocols shown; corrected is authoritative. |
| 10 | "DARPA TC E3 (4 scen. avg)" rows | Theia-3 and Theia-5m rows with per-scenario F1 | 4-scenario average cannot be computed; per-scenario values given. |
| 10 | Heavy mimicry Rule Engine 0.0464/0.9000/0.0882 | CORRECTED label-free 0.7146/0.9329/0.8048; the 0.0882 figure retained only as an audit finding | The original mimicry generator injected an attribute leak and invariant-violating "benign" edges; the corrected generator is label-free and invariant-preserving. |
| 10 | "ROC-AUC stays 1.0000 for the Rule Engine even under heavy mimicry" | **0.9528 ± 0.0312** (genuine continuous violation-score AUC); 1.0000 **retracted** | The 1.0000 came from a hard-coded `getattr(..., 1.0)` fallback, not a computed AUC. |
| 10 | "scales to 1M edges in 15.26s / 364 MB" | **34.48 s inference / ≈971 MB peak / 187.17 s end-to-end / ≈29,007 edges/s** | Corrected-protocol measurements from `raw_runs/scalability`. |
| 10 | (no paired statistics) | Paired RE−GS F1 **+0.4824** (CI 0.3285–0.6363; p=0.001953; dz=2.24); ROC-AUC diff **not** significant (p=0.1055) | Adds the defensible significance result. |
| 11 | "Current Status / Future Plan" | Explicit completed/planned timeline; 1r/6r listed as planned work | Consistency with the audit. |

## Unchanged (verified correct)

- Slide 1 title/authors/guide/event/repo.
- Slide 3 introduction framing.
- Slide 4 problem definition and objectives.
- Slide 5 literature table (no new SOTA comparisons invented).
- Slide 6 research gap.
- Slide 8 architecture novelty statement.
- Slide 9 rule inventory: Structural 6 / Temporal 4 / Semantic 5 = 15.
- Slide 12 references.

## Numbers intentionally excluded

See the final section of `MID_REVIEW_PPT_CONTENT.md`. In brief: the 1.0000
ROC-AUC, the single-seed 0.8125/0.6500/0.7222 as *the* result, the leaky
GraphSAGE 0.5600 as *the* result, "103 tests", the 4-scenario DARPA average,
"15.26 s / 364 MB", the 0.0882 mimicry F1 as robustness, and any claim that
DARPA provides ground-truth provenance poisoning.

## Rendering note

No LibreOffice/`soffice` binary is available in this environment, so the PPTX
was not rasterised to images. Its structure and every edited cell were verified
programmatically via `python-pptx` (slide count, tables, text boxes and notes
all match the corrected content).
