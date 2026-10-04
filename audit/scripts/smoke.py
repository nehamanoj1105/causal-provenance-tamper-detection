import sys
sys.path.insert(0, ".")
from src.graph_construction.synthetic import generate_synthetic_graph
from audit.experiments.poisoning import poisoning_v2 as pv
from audit.experiments.corrected import harness

g = generate_synthetic_graph(num_processes=30, num_files=40, num_network=10, seed=42)
res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=42)
probs = pv.assert_integrity(g, res)
print("integrity problems:", probs)
print("edges clean", len(g.edges), "poisoned", len(res.poisoned_graph.edges), "events", len(res.events))
gt = res.ground_truth_edge_ids()
det = res.detectable_edge_ids()
print("gt ids", len(gt), "detectable ids", len(det))
m, out, yt, ys, ids = harness.rule_engine_metrics(res.poisoned_graph, gt)
keys = ["tp", "fp", "tn", "fn", "precision", "recall", "f1", "roc_auc", "pr_auc"]
print("RE:", {k: m.to_dict()[k] for k in keys})
m2, info = harness.graphsage_eval(res.poisoned_graph, gt, seed=42, epochs=30)
print("GS:", {k: m2.to_dict()[k] for k in keys}, info["best_threshold"],
      info["n_train"], info["n_val"], info["n_test"])
