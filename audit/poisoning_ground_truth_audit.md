# Poisoning Ground-Truth Audit (Phase 7)

Source: `audit/raw_runs/poisoning_audit.json` (10 seeds: 1,7,13,21,42,99,123,256,512,1024;
intensity 5 per type; synthetic graph 30/40/10). All numbers are sums over the
10 seeds unless marked *mean*.

## 1. Per-attack table

| Attack | Requested | Successful events (mean) | GT positives (mean) | GT ids absent from final graph | Detectable positives | Undetectable positives | Duplicate GT ids (mean) | Duplicate final edge ids | Input edges mutated in place (mean) | FP (mean) |
|---|---|---|---|---|---|---|---|---|---|---|
| random_deletion | 5 | 5.0 | 5.0 | 50 | 49 | 1 | 0.0 | 0 | 0.0 | 0.0 |
| random_insertion | 5 | 5.0 | 5.0 | 0 | 45 | 5 | 0.0 | 0 | 0.0 | 0.5 |
| random_reordering | 5 | 5.0 | 5.0 | 0 | 31 | 19 | 0.0 | 0 | 5.0 | 3.2 |
| random_dependency_forgery | 5 | 5.0 | 5.0 | 0 | 35 | 15 | 0.0 | 0 | 4.9 | 0.0 |
| targeted_deletion | 5 | 5.0 | 5.0 | 50 | 50 | 0 | 0.0 | 0 | 0.0 | 0.0 |
| targeted_insertion | 5 | 5.0 | 5.0 | 0 | 48 | 2 | 0.0 | 0 | 0.0 | 2.9 |
| targeted_reordering | 5 | **10.0** | 10.0 | 0 | 58 | 20 | **2.2** | 0 | 0.0 | 1.9 |
| targeted_dependency_forgery | 5 | 5.0 | 5.0 | 0 | 36 | 14 | 0.0 | 0 | 5.0 | 0.0 |

## 2. Findings

### 2.1 Deleted edges do not remain in the graph
For both deletion variants, every ground-truth edge ID is **absent from the final
graph** (`gt_ids_absent_from_final_graph = 50` over 10 seeds). The evaluator
nevertheless counts them as true positives because `SequenceGapRule` and
`UnspawnedProcessRule` *reconstruct* the deleted edge ID from the synthetic
naming convention (`e_activity_<i>`, `e_spawn_<i>`) and emit a violation with
that reconstructed ID. Detection of deletion therefore depends entirely on the
synthetic sequential edge-ID scheme; on real logs (non-sequential IDs) it would
not transfer. The evaluator's "universe" also explicitly adds GT IDs not present
in the graph (`universe = graph_edge_ids | gt_ids | det_ids`), so a deletion is
scored even though it has no edge to score.

### 2.2 Inserted edges receive new IDs
Inserted edges use `poison_insert_<i>` (random) or `targeted_insert_<i>`
(targeted). They are new, unique IDs; no duplicates. The edge type is copied from
an arbitrary existing edge, and endpoints are random node pairs, so most
insertions are benign-looking (semantically valid type/target) and are only
caught when a rule such as `ReadWriteConsistencyRule`/`NetworkConsistencyRule`
sees a type/target mismatch. 5/50 random insertions and 2/50 targeted insertions
were undetectable in the 10-seed audit.

### 2.3 Reordered edges are semantically changed, but only sometimes
Reordering shifts a timestamp by a random `uniform(-50, +50)` seconds. If the
shift keeps the timestamp consistent with the process lineage, the change is
**not semantically detectable**; 19/50 random reorderings and 20/50 targeted
reorderings were undetectable. Worse, reordering produces **false positives**:
3.2 FP/seed (random) and 1.9 FP/seed (targeted), because the shift also triggers
`SequenceMonotonicityRule` on neighbouring benign edges.

### 2.4 Forgery changes only the endpoint, not event semantics
`inject_poisoning` forgery rewrites `edge.source_id` to a random other node while
keeping type and timestamp. `targeted_dependency_forgery` likewise reassigns the
source. 15/50 and 14/50 respectively were undetectable: when the new source is
the same node type as the original (e.g. process→process) and the target type
still matches the edge type, no rule fires.

### 2.5 Ground truth does not always align with final graph edge IDs
- Deletion: 100% of GT IDs absent from the final graph (by construction).
- Targeted reordering: **2.2 duplicate GT IDs per seed** — `targeted_reordering`
  records *both* edges of each swapped pair, but a single edge can be swapped more
  than once, so its ID appears multiple times in `events`. The deduplicated GT
  count is lower than `len(events)`.

### 2.6 False positives caused by construction
- Reordering shifts create genuine violations on *unmodified* edges via
  monotonicity checks (3.2 FP/seed random, 1.9 FP/seed targeted).
- Targeted insertion creates edges that violate type/target consistency
  (2.9 FP/seed) — these are "FP" only because the GT set records the inserted
  edge, so this is a scoring artefact, not a detector error.

## 3. Aliasing bug (input graph mutated in place)

`inject_poisoning` claims to return a copy and not mutate the input, but the copy
is shallow (`edges=list(graph.edges)`), so the `ProvenanceEdge` objects are
shared. Reordering and forgery mutate those objects, changing the caller's
"clean" graph:

| Attack | Input edges mutated in place (mean) |
|---|---|
| random_reordering | 5.0 |
| random_dependency_forgery | 4.9 |
| targeted_dependency_forgery | 5.0 |
| targeted_reordering | 0.0 (uses `deepcopy`) |

This invalidates any clean-vs-poisoned comparison that relies on the input graph
staying clean. In particular, `targeted_reordering` and `targeted_insertion` use
`copy.deepcopy` while the random versions do not, so the module is internally
inconsistent.

## 4. Requested vs. successful

All attack types produce exactly the requested number of events **except
targeted_reordering**, which produces `2 × max_swaps` events (10 for a request of
5). No attack type silently produces zero events on the synthetic graph.
