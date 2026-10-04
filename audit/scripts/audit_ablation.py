"""
Ablation audit across multiple seeds (Phase 10).

Re-runs the repo ablation configs (all / without structural / temporal / semantic
and leave-one-rule-out) across 10 seeds on fresh attack instances, reporting
mean +/- std.  Uses the repo's own src.eval.ablation functions.

Writes audit/raw_runs/ablation_multiseed.json and .csv.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.detection.poisoning_injection import inject_poisoning
from src.eval.ablation import run_rule_ablation, run_per_rule_statistics
from src.graph_construction.synthetic import generate_synthetic_graph

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
INTENSITY = 5


def main():
    per_seed = {}
    for s in SEEDS:
        graph = generate_synthetic_graph(num_processes=30, num_files=40, num_network=10, seed=s)
        poison = inject_poisoning(graph, INTENSITY, INTENSITY, INTENSITY, INTENSITY, seed=s)
        res = run_rule_ablation(graph, poison)
        per_seed[s] = {r.config_name: {
            "num_rules": r.num_rules, "precision": r.precision, "recall": r.recall,
            "f1": r.f1, "accuracy": r.accuracy,
        } for r in res}

    configs = list(next(iter(per_seed.values())).keys())
    agg = {}
    for cfg in configs:
        agg[cfg] = {}
        for m in ["precision", "recall", "f1", "accuracy"]:
            vals = np.array([per_seed[s][cfg][m] for s in SEEDS], dtype=float)
            agg[cfg][m] = {
                "mean": float(vals.mean()),
                "std": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
                "median": float(np.median(vals)),
                "min": float(vals.min()),
                "max": float(vals.max()),
                "values": vals.tolist(),
            }
        agg[cfg]["num_rules"] = per_seed[SEEDS[0]][cfg]["num_rules"]

    out = {"seeds": SEEDS, "intensity": INTENSITY, "per_seed": per_seed, "aggregate": agg}
    outdir = ROOT / "audit" / "raw_runs"
    with open(outdir / "ablation_multiseed.json", "w") as f:
        json.dump(out, f, indent=2)

    with open(outdir / "ablation_multiseed.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["configuration", "num_rules", "precision_mean", "precision_std",
                    "recall_mean", "recall_std", "f1_mean", "f1_std",
                    "accuracy_mean", "accuracy_std"])
        for cfg in configs:
            a = agg[cfg]
            w.writerow([cfg, a["num_rules"],
                        a["precision"]["mean"], a["precision"]["std"],
                        a["recall"]["mean"], a["recall"]["std"],
                        a["f1"]["mean"], a["f1"]["std"],
                        a["accuracy"]["mean"], a["accuracy"]["std"]])

    for cfg in configs:
        a = agg[cfg]
        print(f"{cfg:38s} n={a['num_rules']:2d}  F1={a['f1']['mean']:.4f}+/-{a['f1']['std']:.4f}  "
              f"P={a['precision']['mean']:.4f}+/-{a['precision']['std']:.4f}  "
              f"R={a['recall']['mean']:.4f}+/-{a['recall']['std']:.4f}")

    # per-rule statistics aggregated over seeds
    rule_stats = {}
    for s in SEEDS:
        graph = generate_synthetic_graph(num_processes=30, num_files=40, num_network=10, seed=s)
        poison = inject_poisoning(graph, INTENSITY, INTENSITY, INTENSITY, INTENSITY, seed=s)
        for r in run_per_rule_statistics(graph, poison):
            rule_stats.setdefault(r.rule_name, {"violations": [], "tp": [], "fp": [], "fn": [],
                                                "precision": [], "recall": [], "category": r.category})
            d = rule_stats[r.rule_name]
            d["violations"].append(r.violations); d["tp"].append(r.tp); d["fp"].append(r.fp)
            d["fn"].append(r.fn); d["precision"].append(r.precision); d["recall"].append(r.recall)
    out["per_rule"] = {
        name: {k: (float(np.mean(v)) if isinstance(v, list) and v and isinstance(v[0], (int, float)) else v)
               for k, v in d.items() if k != "category"}
        for name, d in rule_stats.items()
    }
    with open(outdir / "ablation_multiseed.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nWrote", outdir / "ablation_multiseed.json")


if __name__ == "__main__":
    main()
