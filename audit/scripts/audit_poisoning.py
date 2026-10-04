"""
Poisoning ground-truth audit (Phase 7).

For every attack type, inject poisoning with the repo's own code and measure:
  - requested attacks, successful attacks
  - ground-truth positives (events recorded)
  - detectable positives (GT edge ids that some rule flags)
  - undetectable positives (GT edge ids no rule flags)
  - duplicate IDs, missing IDs (GT ids absent from the final graph)
  - false positives caused by construction

Also records the aliasing bug: reorder/forgery mutate shared edge objects so the
"clean" input graph is modified in place.

Writes audit/raw_runs/poisoning_audit.json (full precision).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.detection.poisoning_injection import (
    inject_poisoning,
    targeted_deletion,
    targeted_dependency_forgery,
    targeted_insertion,
    targeted_reordering,
)
from src.detection.rule_engine import default_rule_engine
from src.eval.evaluator import Evaluator
from src.graph_construction.synthetic import generate_synthetic_graph

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
INTENSITY = 5
ATTACKS = [
    "random_deletion",
    "random_insertion",
    "random_reordering",
    "random_dependency_forgery",
    "targeted_deletion",
    "targeted_insertion",
    "targeted_reordering",
    "targeted_dependency_forgery",
]


def run_attack(graph, attack, seed, intensity):
    target = list(graph.nodes.keys())[0] if graph.nodes else "node_0"
    if attack == "random_deletion":
        return inject_poisoning(graph, num_deletions=intensity, num_insertions=0, num_reorderings=0, num_forgeries=0, seed=seed)
    if attack == "random_insertion":
        return inject_poisoning(graph, num_deletions=0, num_insertions=intensity, num_reorderings=0, num_forgeries=0, seed=seed)
    if attack == "random_reordering":
        return inject_poisoning(graph, num_deletions=0, num_insertions=0, num_reorderings=intensity, num_forgeries=0, seed=seed)
    if attack == "random_dependency_forgery":
        return inject_poisoning(graph, num_deletions=0, num_insertions=0, num_reorderings=0, num_forgeries=intensity, seed=seed)
    if attack == "targeted_deletion":
        return targeted_deletion(graph, target_node=target, max_edges=intensity, seed=seed)
    if attack == "targeted_insertion":
        return targeted_insertion(graph, target_node=target, max_insertions=intensity, seed=seed)
    if attack == "targeted_reordering":
        return targeted_reordering(graph, target_node=target, max_swaps=intensity, seed=seed)
    if attack == "targeted_dependency_forgery":
        return targeted_dependency_forgery(graph, target_node=target, max_edges=intensity, seed=seed)
    raise ValueError(attack)


def main():
    out = {"intensity_per_type": INTENSITY, "seeds": SEEDS, "attacks": {}}

    for attack in ATTACKS:
        per_seed = []
        for seed in SEEDS:
            graph = generate_synthetic_graph(num_processes=30, num_files=40, num_network=10, seed=seed)
            clean_edge_objs = {e.edge_id: e for e in graph.edges}
            orig_ts = {e.edge_id: e.timestamp for e in graph.edges}
            orig_src = {e.edge_id: e.source_id for e in graph.edges}

            poison_res = run_attack(graph, attack, seed, INTENSITY)
            final_ids = [e.edge_id for e in poison_res.graph.edges]
            final_ids_set = set(final_ids)
            gt_ids = [ev.edge_id for ev in poison_res.events]
            gt_set = set(gt_ids)

            engine = default_rule_engine()
            rule_results = engine.run(poison_res.graph)
            flagged = set()
            for r in rule_results:
                for v in r.violations:
                    if v.edge_id:
                        flagged.add(v.edge_id)

            aliased = sum(
                1
                for eid, e in clean_edge_objs.items()
                if eid in orig_ts and (e.timestamp != orig_ts[eid] or e.source_id != orig_src[eid])
            )

            ev = Evaluator().evaluate(
                ground_truth=poison_res,
                detected_violations=rule_results,
                graph=poison_res.graph,
                attack_type=attack,
                seed=seed,
            )

            entry = {
                "seed": seed,
                "requested": INTENSITY,
                "successful_events": len(poison_res.events),
                "gt_positive_ids": gt_ids,
                "gt_positive_count": len(gt_ids),
                "unique_gt_ids": len(gt_set),
                "duplicate_gt_ids": len(gt_ids) - len(gt_set),
                "gt_ids_absent_from_final_graph": sorted(gt_set - final_ids_set),
                "gt_ids_present_in_final_graph": sorted(gt_set & final_ids_set),
                "duplicate_final_edge_ids": len(final_ids) - len(final_ids_set),
                "detectable_positives": sorted(gt_set & flagged),
                "undetectable_positives": sorted(gt_set - flagged),
                "detected_count": len(flagged),
                "tp": ev.confusion_matrix.tp,
                "fp": ev.confusion_matrix.fp,
                "tn": ev.confusion_matrix.tn,
                "fn": ev.confusion_matrix.fn,
                "precision": ev.metrics.precision,
                "recall": ev.metrics.recall,
                "f1": ev.metrics.f1,
                "input_graph_edges_mutated_in_place": aliased,
                "clean_edges": len(clean_edge_objs),
                "final_edges": len(final_ids),
                "gt_events_by_type": {},
            }
            for e in poison_res.events:
                entry["gt_events_by_type"][e.poisoning_type.value] = (
                    entry["gt_events_by_type"].get(e.poisoning_type.value, 0) + 1
                )
            per_seed.append(entry)

        agg = {}
        for key in ["successful_events", "gt_positive_count", "unique_gt_ids", "duplicate_gt_ids",
                    "duplicate_final_edge_ids", "detected_count", "tp", "fp", "tn", "fn",
                    "input_graph_edges_mutated_in_place", "final_edges"]:
            vals = [s[key] for s in per_seed]
            agg[key + "_mean"] = sum(vals) / len(vals)
        agg["undetectable_positives_total"] = sum(len(s["undetectable_positives"]) for s in per_seed)
        agg["detectable_positives_total"] = sum(len(s["detectable_positives"]) for s in per_seed)
        agg["gt_absent_total"] = sum(len(s["gt_ids_absent_from_final_graph"]) for s in per_seed)
        for m in ["precision", "recall", "f1"]:
            vals = [s[m] for s in per_seed]
            agg[m + "_mean"] = sum(vals) / len(vals)
        out["attacks"][attack] = {"per_seed": per_seed, "aggregate": agg}
        print(f"{attack:32s} requested={INTENSITY} events={agg['successful_events_mean']:.1f} "
              f"gt_absent={agg['gt_absent_total']} detectable={agg['detectable_positives_total']} "
              f"undetectable={agg['undetectable_positives_total']} aliased={agg['input_graph_edges_mutated_in_place_mean']:.1f} "
              f"P={agg['precision_mean']:.3f} R={agg['recall_mean']:.3f}")

    outdir = ROOT / "audit" / "raw_runs"
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "poisoning_audit.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nWrote", outdir / "poisoning_audit.json")


if __name__ == "__main__":
    main()
