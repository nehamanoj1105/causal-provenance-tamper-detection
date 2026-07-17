# Data

This project uses DARPA Transparent Computing (TC) Engagement 3, Theia
performer data. The raw data is not stored in this repo (multi-GB, not
useful to version).

## Two separate sources, don't confuse them

1. **Schema, tools, ground truth** — in the `darpa-i2o/Transparent-Computing`
   git repo (`schema/`, `tools/`, `ground_truth/`, `README-E3.md`). Pulled
   automatically by `scripts/download_data.sh`.

2. **Actual event data (`.bin` files)** — NOT in the git repo. Hosted
   separately by Five Directions Inc. on Google Drive (linked from
   `README-E3.md` in the cloned manifest). Has to be downloaded manually,
   the git repo only ships the manifest and pointer, not the data itself.

## Format

Event data is Avro-serialized, using DARPA's CDM (Common Data Model) schema,
not plain JSON. Each record deserializes to a `TCCDMDatum`, which is a union
type wrapping one of five entity kinds:

- **Subject** — a process/thread (execution context)
- **Object** — a file, socket, memory region, etc (a resource acted upon)
- **Event** — a typed action linking a Subject to an Object or another
  Subject (READ, WRITE, EXECUTE, CONNECT, FORK, EXIT, etc), this is what
  becomes an edge in our provenance graph
- **Principal** — identity/user context
- **Edge** — explicit causal links used when Event-based causality alone
  is ambiguous

`src/graph_construction/cdm_parser.py` reads these records and normalizes
them into our internal `ProvenanceGraph` (see `schema.py`).

## Which files to use

For E3, the "known good" Theia topics are: `ta1-theia-e3-official-1r`,
`ta1-theia-e3-official-3`, `ta1-theia-e3-official-5m`,
`ta1-theia-e3-official-6r`. Some other E3 files have known data quality
issues, listed in the manifest README, worth checking before picking a file.

## Setup

1. Run `scripts/download_data.sh` to pull the manifest, schema, and tools.
2. Open `data/raw/manifest/README-E3.md`, follow the Google Drive link there,
   and manually download the Theia `.bin` files listed above into
   `data/raw/theia/`.
3. Run the parsing pipeline in `src/graph_construction/` to produce
   provenance graphs into `data/processed/` (gitignored).

## Small samples

`data/samples/` holds a few small, hand-picked graph snippets (not the full
dataset) for quick local testing and for anyone browsing the repo without
downloading the full data.
