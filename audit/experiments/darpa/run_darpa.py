"""
Real DARPA (Theia E3) experiments, correctly labelled.

Two distinct evaluations are produced and kept separate:

  A. REAL-DATA RULE BEHAVIOUR (no injected attack):
     run the Rule Engine on the *unmodified* parsed Theia graph and report how
     many edges it flags. These are false positives under the implemented
     invariants on real provenance -- it is NOT a detection of a real DARPA
     attack. The E3 attack ground truth (TC_Ground_Truth_Report_E3_Update.pdf)
     is only published as coarse time windows / host narratives, so per-edge
     real attack labels do not exist for a supervised score.

  B. SYNTHETIC POST-COLLECTION POISONING on a real graph:
     inject the corrected, well-defined poisoning operators into the real
     Theia graph and measure Rule Engine vs GraphSAGE. This is explicitly
     synthetic; it must never be described as "DARPA ground truth".

Usage: python3 audit/experiments/darpa/run_darpa.py <dataset> [n_edges]
"""
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, ".")

import pandas as pd

from src.graph_construction.converter import dataframe_to_schema
from src.graph_construction.graph_loader import ProvenanceGraph as DFGraph
from src.graph_construction.schema import ProvenanceGraph
from audit.experiments.poisoning import poisoning_v2 as pv
from audit.experiments.corrected import harness

RAW = Path("audit/data/raw/theia")
OUT = Path("audit/raw_runs/darpa")
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]


def load_real(dataset: str, n_edges: int | None) -> ProvenanceGraph:
    nodes = pd.read_csv(RAW / f"{dataset}_nodes.csv")
    edges = pd.read_csv(RAW / f"{dataset}_edges.csv")
    truncated = False
    if n_edges is not None and len(edges) > n_edges:
        edges = edges.iloc[:n_edges].copy()
        keep = set(edges.source_id) | set(edges.target_id)
        nodes = nodes[nodes.node_id.isin(keep)].copy()
        truncated = True
    return dataframe_to_schema(DFGraph(nodes=nodes, edges=edges)), truncated, len(nodes), len(edges)


def run(dataset: str, n_edges: int | None):
    t0 = time.time()
    g, truncated, n_nodes, n_edges = load_real(dataset, n_edges)
    rec = {"dataset": dataset, "provenance": "REAL_DARPA_THEIA_E3",
           "source_csv": str(RAW / f"{dataset}_edges.csv"),
           "truncated": truncated, "n_edges_loaded": n_edges,
           "n_nodes_loaded": n_nodes,
           "graph_nodes": len(g.nodes), "graph_edges": len(g.edges),
           "load_sec": time.time() - t0}

    # ---------- A. Real-data rule behaviour (no injected attack) ----------
    out = harness.run_rule_engine(g)
    rec["real_data_rule_behaviour"] = {
        "flagged_edges": len(out.flagged),
        "flag_rate": len(out.flagged) / max(1, len(g.edges)),
        "per_rule_counts": out.per_rule_counts,
        "note": ("False positives under the implemented invariants on real "
                 "provenance. NOT a detection of real DARPA attacks; per-edge "
                 "real attack labels are unavailable."),
    }

    # ---------- B. Synthetic post-collection poisoning ----------
    per_seed = []
    for seed in SEEDS:
        try:
            res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=seed)
            probs = pv.assert_integrity(g, res)
            gt = res.ground_truth_edge_ids()
            det = res.detectable_edge_ids()
            m_re, _, _, _, _ = harness.rule_engine_metrics(res.poisoned_graph, gt)
            entry = {"seed": seed, "integrity_problems": probs,
                     "requested_ops": 20, "ground_truth_positives": len(gt),
                     "detectable_positives": len(det),
                     "rule_engine": m_re.to_dict()}
            try:
                m_gs, info = harness.graphsage_eval(res.poisoned_graph, gt, seed=seed, epochs=80)
                entry["graphsage"] = m_gs.to_dict()
                entry["graphsage"]["best_threshold"] = info["best_threshold"]
            except Exception:
                entry["graphsage_error"] = traceback.format_exc()
            per_seed.append(entry)
            print(f"  {dataset} seed {seed}: RE f1 {m_re.f1:.4f}", flush=True)
        except Exception:
            print("  FAIL seed", seed, flush=True)
            traceback.print_exc()

    rec["synthetic_post_collection_poisoning"] = per_seed
    rec["runtime_sec"] = time.time() - t0
    json.dump(rec, open(OUT / f"{dataset}_{n_edges or 'full'}.json", "w"), indent=2)
    return rec


if __name__ == "__main__":
    ds = sys.argv[1]
    ne = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(ds, ne)
