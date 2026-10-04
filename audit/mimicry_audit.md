# Mimicry Audit (Phase 9)

Source: `audit/raw_runs/mimicry_audit.json` / `.csv` (10 seeds; base synthetic
graph 40/50/15; intensity 5 per type).

## 1. Edge counts

Noise target in `src/detection/mimicry_attack.py`:

| Strength | Formula | Base edges | Expected noise | Measured noise | Final edges | Match |
|---|---|---|---|---|---|---|
| none | 0 | 234 | 0 | 0 | 234 | exact |
| light | `max(10, 0.3·E)` | 234 | 70 | 70 | 304 | exact |
| medium | `max(20, 0.7·E)` | 234 | 163 | 163 | 397 | exact |
| heavy | `max(30, 1.5·E)` | 234 | 351 | 351 | 585 | exact |

Note: noise volume is computed from `len(graph.edges)` of the **clean** graph
(234), not the poisoned graph, so the final edge counts are base + noise (the
base poisoning keeps the edge count constant because deletions remove 5 and
insertions add 5).

## 2. Are mimicry edges benign under the rule definitions?

**No — the majority are flagged as violations.** The generator builds camouflage
edges with no regard for the invariants the rules check:

| Strength | Noise edges | Noise edges flagged by rules (mean) | Truly benign noise | % flagged |
|---|---|---|---|---|
| light | 70 | 36.6 | 33.4 | 52% |
| medium | 163 | 108.9 | 54.1 | 67% |
| heavy | 351 | 281.8 | 69.2 | 80% |

Causes:
- `mimicry_spawn_*` edges use `rng.sample(proc_nodes, 2)` and connect arbitrary
  process pairs, often producing self-spawn / duplicate-spawn / unspawned-child
  violations.
- `mimicry_pad_*` edges choose a random `EdgeType` over two random nodes, which
  routinely violates type/target consistency (e.g. `READ` to a process).
- Noise timestamps are `uniform(min_ts, max_ts)`, so they create temporal
  inversions.

So the "camouflage" is not benign background noise; it is additional detectable
anomalous activity. The precision collapse under heavy mimicry is therefore
partly caused by the *attack generator*, not only by detector weakness.

## 3. Do mimicry attributes leak the attack condition?

**Yes.** Every noise edge is created with

```python
attributes={"mimicry": True, "op": "fake_file_access" | "fake_process_chain" | ...}
```

In the 10-seed audit, **100% of mimicry edges carry a `mimicry`/`op` attribute**
(light 70/70, medium 163/163, heavy 351/351).

These attributes are **not consumed by the current detectors** (the rule engine
and GraphSAGE use only type/endpoints/timestamp), so they do not currently leak
into the reported metrics. But:

- Any future detector that featurises edge attributes would trivially separate
  mimicry from genuine edges.
- The presence of a ground-truth-like flag in the data means the artifact is
  not adversary-realistic: a real attacker would not label its camouflage.

This is a latent leakage/realism defect and must be removed or explicitly
ignored in any journal protocol.

## 4. Detector vs. ground truth (Rule Engine)

| Strength | Base edges | Poison events | Noise edges | Final edges | Detector positives | GT positives | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| none | 234 | 20 | 0 | 234 | 18.8 | 20 | 0.8435 | 0.7850 | 0.8078 |
| light | 234 | 20 | 70 | 304 | 96.4 | 20 | 0.1739 | 0.8300 | 0.2868 |
| medium | 234 | 20 | 163 | 397 | 190.3 | 20 | 0.0847 | 0.8000 | 0.1530 |
| heavy | 234 | 20 | 351 | 585 | 389.8 | 20 | 0.0439 | 0.8550 | 0.0834 |

Precision falls monotonically because detector positives scale with the noise
volume (false positives on flagged camouflage edges), while GT positives stay at
20. Recall stays high because the base poisoning remains detectable.

## 5. Verdict

| Check | Result |
|---|---|
| Exact noise counts (none/light/medium/heavy) | 0 / 70 / 163 / 351 — verified |
| Mimicry edges actually benign | **No** — 52–80% violate rules |
| Mimicry noise violates implemented invariants | **Yes** |
| Mimicry attributes leak attack condition | **Yes** — 100% carry `mimicry=True` |
| Attributes used by current detector | No (latent risk only) |
| Precision/recall/F1 | Reproduced exactly vs committed |
