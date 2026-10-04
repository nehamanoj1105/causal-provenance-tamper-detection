# GraphSAGE Leakage Audit (Phase 4)

## 1. Pipeline as implemented

`scripts/run_graphsage.py::load_graphsage_data`:

```python
graph = generate_synthetic_graph(...)                 # clean graph
poison_res = inject_poisoning(graph, 5, 5, 5, 5, seed) # poisoned graph + labels
pyg_data = provenance_to_pyg_data(poison_res.graph, poisoning_result=poison_res)
```

`src/ml/train.py::train_pipeline` then:
1. Trains the model on `data.edge_label` (the poisoning ground truth).
2. Every 5 epochs evaluates on the **same** `data`.
3. Runs `find_best_threshold(y_true, y_prob)` on the **same** `data`.
4. Reports the best-F1 metrics from the **same** `data`.

`scripts/run_graphsage.py` then re-derives `y_true = pyg_data.edge_label` and
`y_prob` from the same graph and produces the ROC/PR curves and the diagnostic
report.

## 2. Findings

| Question | Finding |
|---|---|
| Are training edges the same edges used for evaluation? | **Yes.** `train_epoch` uses all edges of `data`; evaluation and thresholding use the identical tensor. |
| Does threshold tuning use test labels? | **Yes.** `find_best_threshold` is called with the ground-truth labels of the evaluation set. |
| Does validation data exist? | **No.** `create_train_val_test_masks` is defined but never called. |
| Does test data exist? | **No.** There is a single `Data` object used for train/val/test. |
| Does graph structure leak test information? | **Yes.** Message passing runs over the same poisoned graph that is scored, so node embeddings encode the test edges (including fabricated/deleted edges). |
| Are poisoning labels visible during training? | **Yes.** `data.edge_label` is the poisoning ground truth and is the training target. |
| Does threshold optimisation use the final evaluation set? | **Yes.** The reported threshold is the argmax-F1 threshold on the evaluation labels. |
| Are edge-level graph features leaky? | **Yes (structural).** `provenance_to_pyg_data` computes node degrees from the poisoned graph, so a deleted edge changes degrees and an inserted edge adds degree — an evaluation-time artefact the model can exploit. |

## 3. Leakage classes present

1. **Train-on-test.** Model weights are fit on the exact edges later scored.
2. **Threshold-on-test.** The decision threshold is selected to maximise F1 on
   the evaluation labels — a direct, unbounded optimism.
3. **No held-out structure.** Node features (degree) and the message-passing
   neighbourhood are computed on the poisoned graph.
4. **Label leakage via selection.** Because both weights and threshold are
   chosen on the scored set, the reported F1/ROC/PR are upper bounds, not
   generalisation estimates.

## 4. Effect measured in this audit

Final 10-seed comparison (same instances, `audit/raw_runs/synthetic/`):

| Protocol | GraphSAGE F1 (mean ± std) |
|---|---|
| Original (train + threshold on test), seed 42 | 0.5600 |
| Corrected (train on train, threshold on val, score on test) | 0.3224 ± 0.1942 |

The leaky protocol inflates GraphSAGE F1 by ≈0.24 absolute at seed 42 and by
≈0.34 in the earlier instance-split audit (`corrected_multiseed.json`, leaky
0.5876 vs clean 0.2452). The exact inflation depends on the split, but the sign
and order of magnitude are robust. The same comparison for the Rule Engine is
unaffected because it has no training step.

Leakage-free GraphSAGE across 10 seeds spans F1 0.00–0.57 with ROC-AUC
0.83 ± 0.16 — i.e. it is unstable and weak on these instances even before any
attack-specific consideration.

## 5. Clean evaluation protocol implemented

`audit/scripts/corrected_multiseed.py` implements the following, per seed `s`:

```
base       = generate_synthetic_graph(seed=s)
train_inst = inject_poisoning(base, seed=f(s,1))   # GraphSAGE weights
val_inst   = inject_poisoning(base, seed=f(s,2))   # threshold only
test_inst  = inject_poisoning(base, seed=f(s,3))   # reported metrics
```

Rules enforced:
- **Weights** depend only on `train_inst`.
- **Threshold** depends only on `val_inst` (argmax F1 over 0.05…1.00).
- **Metrics** are computed on `test_inst` with the validation threshold.
- The test set never influences weights, threshold, attack intensity, or rule
  selection.

**Explicit topology protocol.** Train/val/test are separate *poisoning
instances* over the same benign base topology. This isolates the tamper-detection
decision (which edges are forged) from graph-topology generalisation. It does
**not** test generalisation to unseen base topologies; that is listed as
remaining work in the final report.

## 6. Recommended protocol (journal-safe)

1. Split **instances**, not only edges: disjoint train/val/test poisoned graphs.
2. Select the threshold on validation only; never touch test labels.
3. Report test metrics at the validation-selected threshold.
4. Never re-select features, thresholds, or intensity using test performance.
5. For topology generalisation, hold out base graphs (or DARPA scenarios)
   entirely, not just edges.
