# DARPA Audit (Phase 8)

## 1. What data the code expects

`src/graph_construction/graph_loader.py` reads
`data/parsed/<dataset>_nodes.csv` and `data/parsed/<dataset>_edges.csv` with
`DATA_DIR = Path("data/parsed")`. `available_datasets()` globs
`data/parsed/*_nodes.csv`.

## 2. What data is present

**None.** In a fresh clone, `data/parsed/` does not exist (gitignored) and
`data/samples/` contains only `.gitkeep`. `scripts/download_data.sh` only clones
the DARPA manifest (schema/tools/ground truth); it does **not** download the
`.bin` event data, which the README says must be fetched manually from Google
Drive and parsed.

`docs/dataset_statistics.md` reports the full parsed sizes:

| dataset | nodes | edges | node_file | node_network | node_process | edge_connect | edge_delete | edge_execute | edge_read | edge_spawn | edge_write |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1r | 408,320 | 9,295,127 | 246,074 | 69,870 | 92,376 | 4,422,611 | 172,431 | 35,025 | 3,299,826 | 65,227 | 1,300,007 |
| 3 | 20,157 | 297,777 | 10,528 | 6,174 | 3,455 | 120,888 | 6,279 | 1,312 | 117,892 | 2,529 | 48,877 |
| 5m | 34,835 | 464,858 | 20,012 | 907 | 13,916 | 234,573 | 11 | 9,660 | 143,036 | 13,170 | 64,408 |
| 6r | 1,123,475 | 18,206,475 | 785,675 | 168,156 | 169,644 | 10,670,635 | 231,370 | 70,890 | 4,808,697 | 158,894 | 2,265,989 |

These are **Theia** files per `data/README.md`:
`ta1-theia-e3-official-1r`, `-3`, `-5m`, `-6r`. The README's mapping of scenario
labels (1r→TRACE, 3→CADETS, 5m→ClearScope, 6r→THEIA) is inconsistent with
`data/README.md`, which lists all four as Theia. This is a documentation
discrepancy.

## 3. Edge truncation

`src/eval/cross_dataset.py::load_dataset_graph`:

```python
if max_edges is not None and len(df_edges) > max_edges:
    df_edges = df_edges.iloc[:max_edges]
    edge_node_ids = set(df_edges["source_id"]).union(set(df_edges["target_id"]))
    df_nodes = df_nodes[df_nodes["node_id"].isin(edge_node_ids)]
```

- The **first 50,000 edges** (in CSV order) are taken; nodes are then restricted
  to those incident to the retained edges.
- The default `--max-edges` is 50,000. The truncation is **silent**: no report
  column records it, and the committed `cross_dataset.md` shows `Edges = 50000`
  for all four scenarios, which a reader may mistake for the dataset size.
- Attack injection happens **after** truncation (`inject_poisoning` is called on
  the truncated `graph` in `run_cross_dataset_eval`).

## 4. Are injected attacks random or targeted?

`run_cross_dataset_eval` calls `inject_poisoning(...)` — the **random** attacker
(random deletion/insertion/reordering/forgery of 5 edges each), not the targeted
variants. So the DARPA rows are random post-collection poisoning, not
dataset-native attacks.

## 5. Same intensity across scenarios?

Yes. `run_cross_dataset_eval` uses one `intensity=5` for all four scenarios and
the synthetic fallback, with a single seed (42).

## 6. The 15 vs 20 poisoning-operations discrepancy

`inject_poisoning(intensity=5)` requests 5 deletions + 5 insertions +
5 reorderings + 5 forgeries = **20 requested operations**. However:

- Deletion removes the edge, so the ground truth contains 5 IDs that no longer
  exist in the graph.
- Reordering mutates timestamps only (same edge IDs).
- Forgery mutates source only (same edge IDs).
- Insertion adds 5 new edge IDs.

So the final graph contains only **15** newly-or-affected edge records with IDs
(5 insertions + 10 mutated-in-place), while **20** events are recorded. The
"20 poisoning edges" reported in `mimicry_results.md` (column `PoisonEdges = 20`)
counts *events*, not edges present in the graph. A reader comparing "20 poison
edges" against "final graph edges" will double-count the 5 deleted edges. This
is the source of the 15-vs-20 confusion and should be stated explicitly in any
write-up.

## 7. Ground-truth provenance poisoning claim

**The DARPA evaluation does not use real DARPA attack labels.** The attacks are
synthetically injected into the truncated provenance graph after collection.
There is no use of the DARPA ground-truth labels in the evaluation path. Any
claim that the DARPA numbers reflect detection of naturally occurring provenance
poisoning would be unsupported. The evaluation must distinguish:

- **A. Real DARPA attack labels** — not used anywhere in this codebase.
- **B. Synthetic post-collection poisoning injected into DARPA provenance** —
  what `run_cross_dataset.py` actually measures.

## 8. Verdict

| Check | Result |
|---|---|
| Exact source CSVs | `data/parsed/{1r,3,5m,6r}_{nodes,edges}.csv` — **absent** |
| Node/edge counts | Full counts in `docs/dataset_statistics.md`; benchmarks use 50k-edge slices |
| Exact scenario | Theia E3 (`1r`,`3`,`5m`,`6r`) |
| Edge truncation | First 50,000 edges, silent |
| Injection after truncation | Yes |
| Attacks random vs targeted | Random |
| Same intensity across scenarios | Yes (5 per type, seed 42) |
| 15 vs 20 discrepancy | 20 events vs 15 edge records — real, explainable |
| DARPA numbers reproducible | **No** (data not in repo) |
| Real DARPA attack labels used | **No** |
