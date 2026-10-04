"""
Rule-group and leave-one-rule-out ablation, across 10 seeds.

Rule groups (by implemented invariant):
  structural : type/topology well-formedness (duplicate, spawn/exec/rw/net/
               delete consistency, self-loop, missing node)
  temporal   : ordering invariants (timestamp validity, parent-child order,
               process-activity order, sequence gap, sequence monotonicity)
  semantic   : lineage/meaning invariants (unspawned-process detection)
"""
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, ".")

from src.graph_construction.synthetic import generate_synthetic_graph
from src.detection import rule_engine as re_mod
from audit.experiments.poisoning import poisoning_v2 as pv
from audit.experiments.corrected.metrics import compute_metrics

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
OUT = Path("audit/raw_runs/ablation")
OUT.mkdir(parents=True, exist_ok=True)

ALL_RULES = [
    "DuplicateEdgeRule", "DuplicateEventRule", "SpawnConsistencyRule",
    "ExecutionConsistencyRule", "ReadWriteConsistencyRule", "NetworkConsistencyRule",
    "DeleteConsistencyRule", "SelfLoopRule", "MissingNodeRule", "TimestampRule",
    "UnspawnedProcessRule", "SequenceGapRule", "ParentChildTemporalRule",
    "ProcessActivityTemporalRule", "SequenceMonotonicityRule",
]
GROUPS = {
    "structural": ["DuplicateEdgeRule", "DuplicateEventRule", "SpawnConsistencyRule",
                   "ExecutionConsistencyRule", "ReadWriteConsistencyRule",
                   "NetworkConsistencyRule", "DeleteConsistencyRule", "SelfLoopRule",
                   "MissingNodeRule"],
    "temporal": ["TimestampRule", "SequenceGapRule", "ParentChildTemporalRule",
                 "ProcessActivityTemporalRule", "SequenceMonotonicityRule"],
    "semantic": ["UnspawnedProcessRule"],
}
SEVERITY = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}


def engine_for(rules: list[str]):
    instances = []
    for name in rules:
        cls = getattr(re_mod, name)
        instances.append(cls())
    return re_mod.RuleEngine(instances)


def run_variant(graph, gt_ids, rules):
    engine = engine_for(rules)
    results = engine.run(graph)
    incident = {}
    for e in graph.edges:
        incident.setdefault(e.source_id, []).append(e.edge_id)
        incident.setdefault(e.target_id, []).append(e.edge_id)
    score = {}
    for r in results:
        for v in r.violations:
            w = SEVERITY.get(getattr(v, "severity", "LOW"), 1.0)
            tgts = []
            if getattr(v, "edge_id", None):
                tgts.append(str(v.edge_id))
            elif getattr(v, "node_id", None):
                tgts.extend(incident.get(str(v.node_id), []))
            for t in tgts:
                score[t] = score.get(t, 0.0) + w
    all_ids = [e.edge_id for e in graph.edges]
    y_true = [1 if i in gt_ids else 0 for i in all_ids]
    y_score = [score.get(i, 0.0) for i in all_ids]
    y_pred = [1 if s > 0 else 0 for s in y_score]
    m = compute_metrics(y_true, y_pred, y_score=y_score)
    return m.to_dict(), {r.rule: len(r.violations) for r in results}


def main():
    for seed in SEEDS:
        fp = OUT / f"seed_{seed}.json"
        if fp.exists():
            print("skip", seed, flush=True)
            continue
        try:
            g = generate_synthetic_graph(num_processes=30, num_files=40, num_network=10, seed=seed)
            res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=seed)
            gt = res.ground_truth_edge_ids()
            rec = {"seed": seed, "variants": {}}

            variants = {"all_rules": ALL_RULES}
            for grp, members in GROUPS.items():
                variants[f"without_{grp}"] = [r for r in ALL_RULES if r not in members]
            for r in ALL_RULES:
                variants[f"loo_{r}"] = [x for x in ALL_RULES if x != r]
            for name, rules in variants.items():
                m, counts = run_variant(res.poisoned_graph, gt, rules)
                rec["variants"][name] = {"n_rules": len(rules), "metrics": m,
                                         "per_rule_counts": counts}
            json.dump(rec, open(fp, "w"), indent=2)
            print("done", seed, "all f1", rec["variants"]["all_rules"]["metrics"]["f1"], flush=True)
        except Exception:
            traceback.print_exc()


if __name__ == "__main__":
    main()
