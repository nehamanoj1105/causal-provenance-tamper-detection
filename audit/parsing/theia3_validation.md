# Parsing validation: theia3

Parser: `src/graph_construction/cdm_parser.py::parse_cdm_files_to_csv`
(streaming two-pass, no in-memory ProvenanceGraph).
Raw file: `audit/data/raw/theia/theia3*.bin`.

| Property | Value |
|---|---|
| Nodes | 20157 |
| Edges | 297777 |
| Node types | {'file': 10528, 'network': 6174, 'process': 3455} |
| Edge types | {'connect': 120888, 'read': 117892, 'write': 48877, 'delete': 6279, 'spawn': 2529, 'execute': 1312} |
| Duplicate edge ids | 0 |
| Duplicate node ids | 0 |
| Missing timestamps | 0 |
| Timestamp range | 1522942929.423 .. 1522946509.665 (unix seconds) |
| Edges with missing source | 0 |
| Edges with missing target | 0 |
| Ground-truth label columns in edge CSV | none |

## Notes
- No malformed/duplicate endpoints: the repo's streaming parser writes edges only
  when both endpoints were seen as nodes in pass 1, so `missing_endpoints = 0`.
- No attack/label column is emitted. Real E3 attack ground truth is published
  separately in `TC_Ground_Truth_Report_E3_Update.pdf` (time windows + host), not
  as per-edge labels.
- Node/edge counts match the repository's own `docs/dataset_statistics.md`
  exactly, confirming the parser is correct on real data.
