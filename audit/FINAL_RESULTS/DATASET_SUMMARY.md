# Dataset Summary

## Obtained and parsed (real data)

| Dataset | Nodes | Edges | Skipped | Source | Status |
|---|---|---|---|---|---|
| DARPA TC E3 Theia, scenario 3 (`ta1-theia-e3-official-3`) | 20,157 | 297,777 | 0 | Google Drive (Five Directions) | obtained & parsed |
| DARPA TC E3 Theia, scenario 5m (`ta1-theia-e3-official-5m`) | 34,835 | 464,858 | 0 | Google Drive | obtained & parsed |

Both counts exactly match `docs/dataset_statistics.md`; parsing validated with
`audit/parsing/theia{3,5m}_validation.md`. Raw CSVs under `audit/data/raw/theia/`
(not committed to git). License: public domain (per DARPA `README-E3.md`).

## Not obtained

| Dataset | Expected size | Reason |
|---|---|---|
| Theia E3 scenario 1r | 408,320 nodes / 9,295,127 edges | Google Drive HTTP 403 quota |
| Theia E3 scenario 6r | 1,123,475 nodes / 18,206,475 edges | Google Drive HTTP 403 quota |

No placeholder or estimated results are reported for 1r/6r. If obtained, drop the
`.bin` into `audit/data/raw/theia/` and run `audit/scripts/parse_real.py`; the
corrected protocol applies unchanged.

## How the real data is used

The real Theia graphs are the basis of **one** experiment
(`table9_real_data_poisoning`): the real provenance graph is loaded, capped at
the first 50,000 edges, and **synthetic post-collection poisoning** is injected.
These are therefore *real data + synthetic attacks*, never real attack labels.
The E3 ground-truth report PDF was obtained for context but the repository never
uses real DARPA attack labels; no claim in the manuscript depends on them.

## Synthetic controlled dataset

`src/graph_construction/synthetic.py` generates a provenance graph with 30
processes, 40 files and 10 network entities. Per seed, 5 deletions, 5
insertions, 5 reorderings and 5 dependency forgeries are injected (20 events;
15 detectable positives because deleted edges leave no final-graph record).
