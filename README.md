# causal-provenance-tamper-detection

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
   dataset.
2. Synthetically inject poisoning attacks (deletion, insertion, reordering,
   dependency forgery) with ground-truth labels.
3. Detect poisoning via rule-based causal consistency checks plus a graph
   neural network (GraphSAGE) anomaly detector.
4. Evaluate against baseline provenance-based detection methods using
   Provenance Integrity Score (PIS) and Tamper Detection Rate (TDR).

## Dataset

This repo does not include the dataset. See `data/README.md` for what to
download and where it goes.

## Status

Early-stage, actively being built.

## Repo layout

```
src/graph_construction/   parsing raw audit logs into provenance graphs
src/detection/            rule-based + GNN poisoning detection
src/eval/                 metrics, baselines, evaluation scripts
scripts/                  data download / setup utilities
notebooks/                exploratory analysis
docs/                     write-up notes, not the paper itself
```
