# causal-provenance-tamper-detection

## Reference Papers
-- https://www.sciencedirect.com/science/article/pii/S1389128625007728
-- https://arxiv.org/pdf/2508.21323v2
-- https://www.usenix.org/legacy/event/tapp11/tech/final_files/Meliou.pdf

Graph-based detection of provenance poisoning attacks (event deletion, insertion,
reordering, and dependency forgery) in system audit logs, using causal
consistency analysis over provenance graphs.

## Problem

System provenance graphs (built from audit logs) are the primary evidence used
to reconstruct attack timelines during incident response. Once an attacker has
privileged access, these records can be tampered with directly: events deleted,
forged, reordered, or reattached to fake dependencies. This project detects
that class of tampering by checking whether a provenance graph's causal
structure (who spawned what, what read/wrote what, in what order) is still
internally consistent.

## Scope

This repo covers provenance graph construction and poisoning detection only.
It does not include post-quantum signing, Merkle anchoring, or risk-adaptive
tiering, those are part of a larger system and out of scope here.

## Approach

1. Parse provenance graphs from the DARPA Transparent Computing (E3 Theia)
   dataset (`src/graph_construction/cdm_parser.py`), or generate synthetic
   graphs for development/testing without the real dataset
   (`src/graph_construction/synthetic.py`).
2. Inject poisoning attacks (deletion, insertion, reordering, dependency
   forgery) with ground-truth labels (`src/detection/poisoning_injection.py`).
3. Detect poisoning two ways: deterministic rule-based causal consistency
   checks (`src/detection/rule_based.py`), and a feature-based anomaly
   detector (`src/detection/graph_anomaly.py`).
4. Evaluate with Provenance Integrity Score (PIS) and Tamper Detection Rate
   (TDR) (`src/eval/metrics.py`).

## Current state, read this before trusting any numbers

This pipeline runs end to end right now, but entirely on **synthetic** data,
not the real DARPA dataset yet. Running it will print PIS/TDR/precision
numbers; those numbers describe how well the current detector does against
synthetic poisoning, not real-world performance, don't cite them anywhere.

Two things are explicitly not done yet:

- **CDM parser is untested against real data.** `cdm_parser.py` is written
  against the documented schema and passes unit tests against hand-built
  records shaped like CDM output, but has never run against an actual
  Theia `.bin` file, because that file hasn't been downloaded yet (see
  `data/README.md`, it's a manual Google Drive download, not something
  this repo can automate). Field names like `subjectUuid` and
  `predicateObjectUuid` are inferred from schema docs and could be wrong.
- **Anomaly detector is IsolationForest on hand-built features, not a GNN.**
  The original proposal specified GraphSAGE. `torch`/`torch-geometric`
  aren't wired in yet. The current detector (`graph_anomaly.py`) is a real,
  working, honestly-evaluated baseline (proper train-on-clean/score-on-
  poisoned split, see `detect_against_baseline()`), but it's a placeholder
  for the GNN, not the final method. Swapping it out later doesn't require
  touching graph construction, injection, or eval, they all just consume
  edge lists and scores.

## Running it

```bash
pip install -r requirements.txt
python3 -m src.run_pipeline
```

This generates two separate synthetic graphs (one as a clean baseline, one
to poison), injects 24 labeled poisoning events across all four attack
types, runs both detectors, and prints a PIS/TDR/precision report for each
detector individually and combined.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

21 tests covering CDM record-to-graph mapping, poisoning injection
correctness (deleted edges actually gone, inserted edges actually present,
original graph untouched), and metrics math (perfect detection gives
TDR=1, empty graph doesn't crash, etc).

## Dataset

This repo does not include the dataset. See `data/README.md` for the actual
two-step download process and which Theia files to use.

## Next steps, in order

1. Download a real Theia `.bin` file, run `cdm_parser.py` against it, fix
   whatever field-name assumptions turn out wrong.
2. Re-run the full pipeline on real parsed graphs instead of synthetic ones,
   see whether TDR/PIS hold up.
3. Add `torch` + `torch-geometric`, replace the IsolationForest baseline
   with a GraphSAGE detector, compare the two head to head.
4. Add real baselines from prior provenance-detection literature for
   comparison, not just rules-vs-anomaly-detector internally.

## Repo layout

```
src/graph_construction/   schema, CDM parser, synthetic graph generator
src/detection/            poisoning injection, rule-based + anomaly detection
src/eval/                 PIS/TDR metrics
tests/                    unit tests for all of the above
scripts/                  data download utility
notebooks/                exploratory analysis
docs/                     write-up notes, not the paper itself
```
