"""
Rule Engine continuous-score audit (Phase 6).

The paper reports Rule Engine ROC-AUC = 1.0000 under heavy mimicry.  The rule
engine is deterministic and only emits a binary flag per edge.  This script:

  1. Verifies that src.eval.metrics.MetricResult has NO roc_auc field, so the
     value reported by src/eval/robustness.py comes from getattr(m,'roc_auc', ...)
     defaulting to 1.0.
  2. Builds the ONLY legitimate continuous edge-level score the rules expose:
     number of distinct rule violations per edge (0,1,2,...), from run_all_checks.
  3. Computes ROC-AUC / PR-AUC from that score, plus the binary thresholded
     ROC-AUC (a step function, still reportable but degenerate).
  4. Repeats across the 10 audit seeds and mimicry strengths.

Writes audit/raw_runs/rule_score_audit.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sklearn.metrics import average_precision_score, roc_auc_score

from src.detection.mimicry_attack import inject_mimicry_attack
from src.detection.poisoning_injection import inject_poisoning
from src.detection.rule_based import run_all_checks
from src.detection.rule_engine import default_rule_engine
from src.eval.metrics import MetricResult
from src.graph_construction.synthetic import generate_synthetic_graph

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
STRENGTHS = ["none", "light", "medium", "heavy"]
INTENSITY = 5


def edge_scores(graph, gt_ids):
    """Continuous score = number of distinct rule violations on the edge."""
    violations = run_all_checks(graph)
    counts = {}
    for v in violations:
        if v.edge_id:
            counts[v.edge_id] = counts.get(v.edge_id, 0) + 1
    edge_ids = [e.edge_id for e in graph.edges]
    y_true = [1 if eid in gt_ids else 0 for eid in edge_ids]
    y_score = [float(counts.get(eid, 0)) for eid in edge_ids]
    return np.array(y_true), np.array(y_score), counts


def main():
    out = {
        "metric_result_has_roc_auc_field": hasattr(MetricResult(), "roc_auc"),
        "metric_result_fields": list(MetricResult().__dataclass_fields__),
        "robustness_roc_default": "getattr(m, 'roc_auc', 1.0 if m.f1 > 0 else 0.5) -> constant 1.0 whenever any violation exists",
        "seeds": SEEDS,
        "results": {},
    }

    for strength in STRENGTHS:
        rows = []
        for seed in SEEDS:
            graph = generate_synthetic_graph(num_processes=40, num_files=50, num_network=15, seed=seed)
            base = inject_poisoning(graph, INTENSITY, INTENSITY, INTENSITY, INTENSITY, seed=seed)
            gt_ids = {ev.edge_id for ev in base.events}

            if strength == "none":
                camouflaged = base.graph
            else:
                camouflaged = inject_mimicry_attack(
                    graph, base_poisoning=base, strength=strength, intensity=INTENSITY, seed=seed
                ).graph

            y_true, y_score, counts = edge_scores(camouflaged, gt_ids)
            engine = default_rule_engine()
            rr = engine.run(camouflaged)
            flagged = {v.edge_id for r in rr for v in r.violations if v.edge_id}
            y_bin = np.array([1 if e.edge_id in flagged else 0 for e in camouflaged.edges])

            distinct_scores = len(np.unique(y_score))
            if len(np.unique(y_true)) < 2 or distinct_scores < 2:
                roc_count = None
                pr_count = None
            else:
                roc_count = float(roc_auc_score(y_true, y_score))
                pr_count = float(average_precision_score(y_true, y_score))

            if len(np.unique(y_true)) < 2 or len(np.unique(y_bin)) < 2:
                roc_bin = None
            else:
                roc_bin = float(roc_auc_score(y_true, y_bin))

            rows.append({
                "seed": seed,
                "edges": len(camouflaged.edges),
                "gt_positives": int(y_true.sum()),
                "distinct_violation_counts": distinct_scores,
                "max_violation_count": int(y_score.max()) if len(y_score) else 0,
                "edges_flagged": int(y_bin.sum()),
                "roc_auc_count_score": roc_count,
                "pr_auc_count_score": pr_count,
                "roc_auc_binary_flag": roc_bin,
                "paper_reported_roc_auc": 1.0,
            })
        out["results"][strength] = rows
        valid = [r["roc_auc_count_score"] for r in rows if r["roc_auc_count_score"] is not None]
        print(f"{strength:7s} count-score ROC-AUC mean={np.mean(valid) if valid else float('nan'):.4f} "
              f"n_valid={len(valid)}/{len(rows)}  binary-flag ROC-AUC mean="
              f"{np.mean([r['roc_auc_binary_flag'] for r in rows if r['roc_auc_binary_flag'] is not None]):.4f}")

    outdir = ROOT / "audit" / "raw_runs"
    with open(outdir / "rule_score_audit.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nWrote", outdir / "rule_score_audit.json")


if __name__ == "__main__":
    main()
