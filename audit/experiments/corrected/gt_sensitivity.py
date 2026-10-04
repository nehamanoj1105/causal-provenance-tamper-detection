"""
Ground-truth sensitivity: detectable-only vs all-events GT.

The repo scores against all 20 poisoning events, including 5 deletions whose
edges are absent from the final graph (detectable only via synthetic ID
reconstruction). The corrected edge-level protocol scores against the 15
positives that actually exist in the final graph and treats deletion as a
separate task. This script quantifies the difference so neither choice is
hidden.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from src.graph_construction.synthetic import generate_synthetic_graph
from audit.experiments.poisoning import poisoning_v2 as pv
from audit.experiments.corrected import harness
from audit.experiments.corrected.metrics import summarize

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
OUT = Path("audit/raw_runs/gt_sensitivity.json")


def metrics_with_universe(graph, gt_ids, universe_ids):
    """Score over an explicit universe (may include GT ids absent from graph)."""
    from audit.experiments.corrected.metrics import compute_metrics
    out = harness.run_rule_engine(graph)
    y_true = [1 if i in gt_ids else 0 for i in universe_ids]
    y_score = [out.edge_score.get(i, 0.0) for i in universe_ids]
    y_pred = [1 if i in out.flagged else 0 for i in universe_ids]
    return compute_metrics(y_true, y_pred, y_score=y_score)


def main():
    rows = []
    for seed in SEEDS:
        g = generate_synthetic_graph(30, 40, 10, seed=seed)
        res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=seed)
        gt_all = res.ground_truth_edge_ids()        # 20, includes absent deletions
        gt_det = res.detectable_edge_ids()          # 15, present in final graph
        graph_ids = [e.edge_id for e in res.poisoned_graph.edges]
        universe_final = graph_ids
        # repo-style universe: final graph ids union GT ids (incl. absent deletions)
        universe_repo = graph_ids + [i for i in sorted(gt_all) if i not in set(graph_ids)]

        m_final = metrics_with_universe(res.poisoned_graph, gt_all, universe_final)
        m_repo = metrics_with_universe(res.poisoned_graph, gt_all, universe_repo)
        m_det = metrics_with_universe(res.poisoned_graph, gt_det, universe_final)
        rows.append({"seed": seed,
                     "n_gt_all": len(gt_all), "n_gt_detectable": len(gt_det),
                     "n_universe_final": len(universe_final),
                     "n_universe_repo": len(universe_repo),
                     "f1_all": m_final.f1, "precision_all": m_final.precision,
                     "recall_all": m_final.recall, "roc_auc_all": m_final.roc_auc,
                     "f1_repo_universe": m_repo.f1, "precision_repo_universe": m_repo.precision,
                     "recall_repo_universe": m_repo.recall, "roc_auc_repo_universe": m_repo.roc_auc,
                     "f1_det": m_det.f1, "precision_det": m_det.precision,
                     "recall_det": m_det.recall, "roc_auc_det": m_det.roc_auc})
    summary = {
        "f1_all": summarize([r["f1_all"] for r in rows]),
        "f1_det": summarize([r["f1_det"] for r in rows]),
        "f1_repo_universe": summarize([r["f1_repo_universe"] for r in rows]),
        "precision_all": summarize([r["precision_all"] for r in rows]),
        "precision_det": summarize([r["precision_det"] for r in rows]),
        "precision_repo_universe": summarize([r["precision_repo_universe"] for r in rows]),
        "recall_all": summarize([r["recall_all"] for r in rows]),
        "recall_det": summarize([r["recall_det"] for r in rows]),
        "recall_repo_universe": summarize([r["recall_repo_universe"] for r in rows]),
        "roc_auc_all": summarize([r["roc_auc_all"] for r in rows]),
        "roc_auc_det": summarize([r["roc_auc_det"] for r in rows]),
        "roc_auc_repo_universe": summarize([r["roc_auc_repo_universe"] for r in rows]),
    }
    json.dump({"per_seed": rows, "summary": summary}, open(OUT, "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
