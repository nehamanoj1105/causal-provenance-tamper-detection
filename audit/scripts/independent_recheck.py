"""
Independent in-memory reproduction check: re-run the corrected pipeline for a
few seeds and compare the freshly computed metrics against the stored raw runs.
This verifies determinism and that the stored raw runs were not edited.

Usage: python3 audit/scripts/independent_recheck.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from src.graph_construction.synthetic import generate_synthetic_graph
from audit.experiments.poisoning import poisoning_v2 as pv
from audit.experiments.corrected import harness

OUT = Path("audit/final_validation")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    seeds = [1, 42, 1024]
    rows = []
    for seed in seeds:
        stored = json.load(open(f"audit/raw_runs/synthetic/seed_{seed}.json"))
        g = generate_synthetic_graph(30, 40, 10, seed=seed)
        res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=seed)
        probs = pv.assert_integrity(g, res)
        m_re, _, _, _, _ = harness.rule_engine_metrics(res.poisoned_graph, res.ground_truth_edge_ids())
        m_gs, _ = harness.graphsage_eval(res.poisoned_graph, res.ground_truth_edge_ids(),
                                         seed=seed, epochs=80)
        fresh = {"re_f1": m_re.f1, "re_roc_auc": m_re.roc_auc, "re_precision": m_re.precision,
                 "re_recall": m_re.recall, "gs_f1": m_gs.f1, "gs_roc_auc": m_gs.roc_auc,
                 "integrity_problems": probs,
                 "poisoned_edges": len(res.poisoned_graph.edges)}
        st = {"re_f1": stored["rule_engine"]["f1"], "re_roc_auc": stored["rule_engine"]["roc_auc"],
              "re_precision": stored["rule_engine"]["precision"], "re_recall": stored["rule_engine"]["recall"],
              "gs_f1": stored["graphsage"]["f1"], "gs_roc_auc": stored["graphsage"]["roc_auc"],
              "integrity_problems": stored["integrity_problems"],
              "poisoned_edges": stored["poisoned_edges"]}
        ok = all(abs(fresh[k] - st[k]) < 1e-9 if isinstance(st[k], float) else fresh[k] == st[k]
                 for k in st)
        rows.append({"seed": seed, "deterministic_match": ok,
                     "re_f1_fresh": fresh["re_f1"], "re_f1_stored": st["re_f1"],
                     "gs_f1_fresh": fresh["gs_f1"], "gs_f1_stored": st["gs_f1"],
                     "integrity_problems": probs})
        print(f"seed {seed}: deterministic={ok} RE f1 {fresh['re_f1']:.6f} "
              f"GS f1 {fresh['gs_f1']:.6f}")
    json.dump(rows, open(OUT / "independent_recheck.json", "w"), indent=2)


if __name__ == "__main__":
    main()
