# Original-protocol reproduction log (Task B Phase 1)

These are the repository's **own** runner scripts, executed unmodified, with the
current environment. They are the "ORIGINAL-REPRODUCTION" layer (the current
code as shipped), distinct from the "AUDITED/CORRECTED" layer under
`audit/experiments/`.

| Runner | Command | Result |
|---|---|---|
| Multi-seed rule engine | `python3 scripts/run_evaluation.py --attack-type all --multiple-seeds` | OK; committed multi-seed value was a single seed (std 0); true 10-seed mean F1 **0.792082 ± 0.057799** |
| GraphSAGE | `python3 scripts/run_graphsage.py --epochs 30 --seed 42` | OK; F1 **0.5600**, ROC-AUC 0.8776, τ*=0.70 (reproduces committed value exactly; this is the leaky protocol) |
| Cross-dataset | `python3 scripts/run_cross_dataset.py` | Falls back to **synthetic only** — `data/parsed/` absent, so no real 1r/3/5m/6r rows are produced |
| Mimicry | `python3 scripts/run_mimicry.py` | OK; reproduces committed edge counts (234/304/397/585) and the 1.0000 "ROC-AUC" fallback |
| Scalability | `python3 scripts/run_scalability.py` | OK; 10k–1M. **Note:** its "GraphSAGE" column is *inference only* (0.01–0.88 s), not training — the printed 1.1–1.6M edges/s for GraphSAGE vs 30k edges/s for the Rule Engine is an apples-to-oranges comparison. |

Raw logs and CSVs are stored in this directory.

## Key observations

- The repository's original runners reproduce the **committed** repository
  values, but several committed values are themselves methodologically flawed:
  single-seed stats labelled multi-seed, threshold tuning on the evaluation
  graph, a hard-coded 1.0 "ROC-AUC", and a GraphSAGE-vs-Rule-Engine speed
  comparison that mixes training with inference.
- The cross-dataset runner silently substitutes a synthetic graph for the
  missing DARPA data; the committed `results/cross_dataset.md` shows real 1r/3/
  5m/6r rows that the current environment cannot regenerate.
