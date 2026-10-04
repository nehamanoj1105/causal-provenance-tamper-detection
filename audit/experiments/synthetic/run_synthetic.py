"""
Corrected synthetic benchmark (10 seeds), Rule Engine vs GraphSAGE.

Produces raw per-seed records under audit/raw_runs/synthetic/.
Usage: python3 audit/experiments/synthetic/run_synthetic.py [seed ...]
"""
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, ".")

from src.graph_construction.synthetic import generate_synthetic_graph
from audit.experiments.poisoning import poisoning_v2 as pv
from audit.experiments.corrected import harness
from audit.experiments.corrected.metrics import compute_metrics
from audit.experiments.mimicry import mimicry_v2

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
OUT = Path("audit/raw_runs/synthetic")
OUT.mkdir(parents=True, exist_ok=True)


def per_type(graph, records, gt_all):
    """Metrics restricted to one attack type's gt ids (binary over all edges)."""
    out = {}
    for atk in ["deletion", "insertion", "reordering", "dependency_forgery"]:
        ids = {r["expected_detection_target"] for r in records
               if r["attack_type"] == atk and r["effective"] and r["expected_detection_target"]}
        if not ids:
            continue
        m, _, _, _, _ = harness.rule_engine_metrics(graph, ids)
        out[atk] = {"n_gt": len(ids), **m.to_dict()}
    return out


def run_seed(seed: int) -> dict:
    t0 = time.time()
    g = generate_synthetic_graph(num_processes=30, num_files=40, num_network=10, seed=seed)
    res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=seed)
    probs = pv.assert_integrity(g, res)
    recs = res.records()
    gt = res.ground_truth_edge_ids()
    det = res.detectable_edge_ids()

    rec = {"seed": seed, "provenance": "audit_corrected",
           "clean_nodes": len(g.nodes), "clean_edges": len(g.edges),
           "poisoned_edges": len(res.poisoned_graph.edges),
           "integrity_problems": probs,
           "ground_truth_positives": len(gt), "detectable_positives": len(det),
           "events": recs}

    # ---------- Rule Engine ----------
    m_re, out, _, _, _ = harness.rule_engine_metrics(res.poisoned_graph, gt)
    rec["rule_engine"] = m_re.to_dict()
    rec["rule_engine"]["per_rule_counts"] = out.per_rule_counts
    rec["rule_engine"]["per_type"] = per_type(res.poisoned_graph, recs, gt)

    # Rule Engine applied to the CLEAN graph (false-positive baseline)
    mc, _, _, _, _ = harness.rule_engine_metrics(g, set())
    rec["rule_engine_clean_fp"] = {"flagged_edges": len(harness.run_rule_engine(g).flagged),
                                   "fpr": mc.fpr, "precision_undefined": True}

    # ---------- GraphSAGE (leakage-free) ----------
    try:
        m_gs, info = harness.graphsage_eval(res.poisoned_graph, gt, seed=seed, epochs=80)
        rec["graphsage"] = m_gs.to_dict()
        rec["graphsage"]["best_threshold"] = info["best_threshold"]
        rec["graphsage"]["n_train"] = info["n_train"]
        rec["graphsage"]["n_val"] = info["n_val"]
        rec["graphsage"]["n_test"] = info["n_test"]
    except Exception as e:
        rec["graphsage_error"] = traceback.format_exc()

    # ---------- Mimicry ----------
    rec["mimicry"] = {}
    mres = _MimicryBase(res)
    for strength in ["none", "light", "medium", "heavy"]:
        if strength == "none":
            base_graph = res.poisoned_graph
            noise_ids = []
        else:
            mim = mimicry_v2.generate_mimicry_v2(res.poisoned_graph, res, strength=strength, seed=seed)
            base_graph = mim.graph
            noise_ids = mim.noise_ids
        # mimicry noise self-violation check
        self_viol = mimicry_v2.count_rule_violations_in_noise(base_graph, noise_ids) if noise_ids else {}
        m_re_m, out_m, _, _, _ = harness.rule_engine_metrics(base_graph, gt)
        entry = {"base_edges": len(res.poisoned_graph.edges),
                 "noise_edges": len(noise_ids),
                 "final_edges": len(base_graph.edges),
                 "noise_self_violations": self_viol,
                 "rule_engine": m_re_m.to_dict()}
        try:
            m_gs_m, info_m = harness.graphsage_eval(base_graph, gt, seed=seed, epochs=80)
            entry["graphsage"] = m_gs_m.to_dict()
            entry["graphsage"]["best_threshold"] = info_m["best_threshold"]
        except Exception:
            entry["graphsage_error"] = traceback.format_exc()
        rec["mimicry"][strength] = entry

    rec["runtime_sec"] = time.time() - t0
    return rec


class _MimicryBase:
    """Adapter so mimicry_v2 receives a PoisoningResult-like object."""
    def __init__(self, res):
        self.res = res

    @property
    def graph(self):
        return self.res.poisoned_graph

    @property
    def events(self):
        return self.res.events


if __name__ == "__main__":
    seeds = [int(s) for s in sys.argv[1:]] or SEEDS
    for s in seeds:
        fp = OUT / f"seed_{s}.json"
        if fp.exists():
            print("skip existing", s, flush=True)
            continue
        try:
            rec = run_seed(s)
            json.dump(rec, open(fp, "w"), indent=2)
            print("done", s, "RE f1", rec["rule_engine"]["f1"],
                  "GS f1", rec.get("graphsage", {}).get("f1"), flush=True)
        except Exception:
            print("FAIL", s, flush=True)
            traceback.print_exc()
