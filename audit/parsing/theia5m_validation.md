# Parsing validation: theia5m

Parser: `src/graph_construction/cdm_parser.py::parse_cdm_files_to_csv`
(streaming two-pass, no in-memory ProvenanceGraph).
Raw file: `audit/data/raw/theia/theia5m*.bin`.

| Property | Value |
|---|---|
| Nodes | 34835 |
| Edges | 464858 |
| Node types | {'file': 20012, 'process': 13916, 'network': 907} |
| Edge types | {'connect': 234573, 'read': 143036, 'write': 64408, 'spawn': 13170, 'execute': 9660, 'delete': 11} |
| Duplicate edge ids | 0 |
| Duplicate node ids | 0 |
| Missing timestamps | 0 |
| Timestamp range | 1523278015.005 .. 1523312112.001 (unix seconds) |
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
