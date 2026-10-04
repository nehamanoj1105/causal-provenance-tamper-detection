# Final Safety Check (Phase 15)

Programmatic verification: `audit/scripts/safety_check.py` →
`audit/raw_runs/safety_check.json`.

| Requirement | Status | Evidence |
|---|---|---|
| No test-set leakage in the corrected protocol | PASS | `corrected_multiseed.json` protocol = "clean train/val/test"; weights←train, threshold←val, metrics←test. Original code **does** leak (documented). |
| No threshold tuning on test data (corrected) | PASS | threshold selected on `val_inst` only. Original code tunes on test (documented as a defect). |
| No fabricated ROC-AUC | PASS (audit) | `metric_result_has_roc_auc = false`; the repo's 1.0 is flagged as fabricated; independent count-score AUC computed. |
| No mismatch between ground truth and final graph | DOCUMENTED | Deletion GT ids absent from final graph (5/5) and scored via ID reconstruction; `targeted_reordering` emits duplicate GT ids (2.2/seed). |
| No accidental attack labels exposed as features | PASS | `edge_label_in_features = false`; node features = 4 one-hot type + 3 degree; edge features = 6 one-hot type + norm timestamp. No label in features. |
| Mimicry attributes not featurised | PASS (latent) | `mimicry`/`op` attributes exist on 100% of mimicry edges but are not used by any detector; flagged as a realism/latent-leakage risk. |
| No mismatch between 15 and 20 poisoning events | DOCUMENTED | 20 events vs 15 edge records (5 deletions vanish); explained in `darpa_audit.md`. |
| No silent dataset truncation | DOCUMENTED | First 50,000 edges, silent; flagged. |
| No single-seed claims presented as general conclusions | PASS (audit) | All headline numbers reported as 10-seed mean ± std; committed single-seed aggregate flagged. |
| No scalability comparison mixing training and inference | PASS | GraphSAGE training/epoch and inference reported separately. |
| No unsupported claim that DARPA provides ground-truth provenance poisoning | PASS | `darpa_audit.md` states all attacks are synthetic post-collection injections; no DARPA labels used. |
| Shallow-copy mutation bug | CONFIRMED | 5 input edges mutated in place after a reordering injection (`input_graph_mutated_after_reordering = 5`). |

## Additional confirmations

- `data/parsed` does not exist (`darpa_parsed_dir_exists = false`).
- Leaky vs clean GraphSAGE F1: 0.5876 vs 0.2461 (inflation confirmed).
- No repository result file was edited to match the paper; originals preserved in
  `audit/original_results_backup/`.
