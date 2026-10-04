"""
Mimicry audit (Phase 9).

Verifies:
  - exact mimicry edge counts for none/light/medium/heavy
  - whether mimicry noise edges are truly benign under the rule definitions
  - whether mimicry edges carry attributes that leak the attack condition
  - base / poisoning / mimicry / final edge counts and detector vs ground truth

Writes audit/raw_runs/mimicry_audit.json and audit/raw_runs/mimicry_audit.csv.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.detection.mimicry_attack import inject_mimicry_attack
from src.detection.poisoning_injection import inject_poisoning
from src.detection.rule_engine import default_rule_engine
from src.graph_construction.synthetic import generate_synthetic_graph

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
STRENGTHS = ["none", "light", "medium", "heavy"]
INTENSITY = 5


def main():
    out = {"seeds": SEEDS, "intensity": INTENSITY, "strengths": {}}

    for strength in STRENGTHS:
        rows = []
        for seed in SEEDS:
            graph = generate_synthetic_graph(num_processes=40, num_files=50, num_network=15, seed=seed)
            base = inject_poisoning(graph, INTENSITY, INTENSITY, INTENSITY, INTENSITY, seed=seed)
            if strength == "none":
                res = inject_mimicry_attack(graph, base_poisoning=base, strength="light", seed=seed)
                # for 'none' the repo uses base_poisoning directly with 0 noise
                noise_ids = []
                camouflaged = base.graph
                num_noise = 0
            else:
                res = inject_mimicry_attack(graph, base_poisoning=base, strength=strength, intensity=INTENSITY, seed=seed)
                noise_ids = res.camouflaged_edge_ids
                camouflaged = res.graph
                num_noise = res.num_noise_edges

            noise_set = set(noise_ids)
            gt_ids = {ev.edge_id for ev in base.events}

            # Are mimicry edges flagged by any rule (i.e. NOT benign)?
            engine = default_rule_engine()
            rr = engine.run(camouflaged)
            flagged = {v.edge_id for r in rr for v in r.violations if v.edge_id}
            mimicry_flagged = sorted(noise_set & flagged)

            # Do mimicry edges carry leaky attributes?
            leaky_attrs = 0
            mimicry_objs = [e for e in camouflaged.edges if e.edge_id in noise_set]
            for e in mimicry_objs:
                if e.attributes and ("mimicry" in e.attributes or "op" in e.attributes):
                    leaky_attrs += 1

            # detector vs ground truth
            tp = len(gt_ids & flagged); fp = len(flagged - gt_ids); fn = len(gt_ids - flagged)
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            rec = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0

            rows.append({
                "seed": seed,
                "base_edges": len(graph.edges),
                "poison_events": len(base.events),
                "noise_edges": num_noise,
                "noise_requested_ratio": {"light": 0.3, "medium": 0.7, "heavy": 1.5, "none": 0.0}[strength],
                "expected_noise": {"light": max(10, int(len(graph.edges) * 0.3)),
                                   "medium": max(20, int(len(graph.edges) * 0.7)),
                                   "heavy": max(30, int(len(graph.edges) * 1.5)),
                                   "none": 0}[strength],
                "final_edges": len(camouflaged.edges),
                "mimicry_edges_flagged_by_rules": len(mimicry_flagged),
                "mimicry_edges_benign_count": num_noise - len(mimicry_flagged),
                "mimicry_edges_with_leaky_attributes": leaky_attrs,
                "detector_positives": len(flagged),
                "gt_positives": len(gt_ids),
                "tp": tp, "fp": fp, "fn": fn,
                "precision": prec, "recall": rec, "f1": f1,
            })
        out["strengths"][strength] = rows
        agg = {}
        for k in ["base_edges", "noise_edges", "expected_noise", "final_edges",
                  "mimicry_edges_flagged_by_rules", "mimicry_edges_benign_count",
                  "mimicry_edges_with_leaky_attributes", "detector_positives",
                  "gt_positives", "tp", "fp", "fn"]:
            agg[k + "_mean"] = float(np.mean([r[k] for r in rows]))
        for k in ["precision", "recall", "f1"]:
            agg[k + "_mean"] = float(np.mean([r[k] for r in rows]))
            agg[k + "_std"] = float(np.std([r[k] for r in rows], ddof=1))
        out["strengths"][strength] = {"per_seed": rows, "aggregate": agg}
        print(f"{strength:7s} base={agg['base_edges_mean']:.0f} noise={agg['noise_edges_mean']:.1f} "
              f"(expected {agg['expected_noise_mean']:.1f}) final={agg['final_edges_mean']:.1f} "
              f"noise_flagged={agg['mimicry_edges_flagged_by_rules_mean']:.1f} "
              f"leaky_attrs={agg['mimicry_edges_with_leaky_attributes_mean']:.1f} "
              f"P={agg['precision_mean']:.3f} R={agg['recall_mean']:.3f}")

    outdir = ROOT / "audit" / "raw_runs"
    with open(outdir / "mimicry_audit.json", "w") as f:
        json.dump(out, f, indent=2)

    with open(outdir / "mimicry_audit.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["strength", "seed", "base_edges", "noise_edges", "expected_noise", "final_edges",
                    "mimicry_edges_flagged_by_rules", "mimicry_edges_benign_count",
                    "mimicry_edges_with_leaky_attributes", "detector_positives", "gt_positives",
                    "tp", "fp", "fn", "precision", "recall", "f1"])
        for strength in STRENGTHS:
            for r in out["strengths"][strength]["per_seed"]:
                w.writerow([strength] + [r[k] for k in [
                    "seed", "base_edges", "noise_edges", "expected_noise", "final_edges",
                    "mimicry_edges_flagged_by_rules", "mimicry_edges_benign_count",
                    "mimicry_edges_with_leaky_attributes", "detector_positives", "gt_positives",
                    "tp", "fp", "fn", "precision", "recall", "f1"]])
    print("\nWrote", outdir / "mimicry_audit.json")


if __name__ == "__main__":
    main()
