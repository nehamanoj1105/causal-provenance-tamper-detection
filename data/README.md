# Data

This project uses DARPA Transparent Computing (TC) Engagement 3, Theia dataset.
The raw data is not stored in this repo (multi-GB, not useful to version).

## Source

DARPA released TC program data publicly for research use:
https://github.com/darpa-i2o/Transparent-Computing

Engagement 3 (E3) Theia: single-host Ubuntu 12.04 provenance data, includes
labeled attack scenarios (e.g. backdoor installation via browser exploit,
phishing-delivered malware).

## Setup

1. Run `scripts/download_data.sh` (or follow the manual steps in that script's
   comments if the automated pull fails).
2. Raw files land in `data/raw/` (gitignored).
3. Run the parsing pipeline in `src/graph_construction/` to produce provenance
   graphs into `data/processed/` (also gitignored).

## Small samples

`data/samples/` holds a few small, hand-picked graph snippets (not the full
dataset) for quick local testing and for anyone browsing the repo without
downloading the full data.
