"""Parse real DARPA CDM .bin files into normalized CSVs via the repo's own parser.

Usage: python3 audit/scripts/parse_real.py '{"theia3": "/path/to/file.bin"}'
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
from src.graph_construction.cdm_parser import parse_cdm_files_to_csv  # noqa: E402

out = Path("audit/data/raw/theia")
for name, f in json.loads(sys.argv[1]).items():
    t = time.time()
    n, e, s = parse_cdm_files_to_csv(
        [Path(f)], out / f"{name}_nodes.csv", out / f"{name}_edges.csv"
    )
    print(
        name, "nodes", n, "edges", e, "skipped", s,
        "sec", round(time.time() - t, 1), flush=True,
    )
