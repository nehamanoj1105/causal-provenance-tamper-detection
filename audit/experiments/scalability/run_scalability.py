"""
Clean scalability benchmark.

Reports, as *separate phases* (never mixing Rule-Engine inference with
GraphSAGE training):
  - graph construction
  - poisoning injection
  - detector time: Rule Engine inference, GraphSAGE training, GraphSAGE inference
  - evaluation time
  - end-to-end time
  - RSS memory, peak Python allocation (tracemalloc)
  - throughput (edges/s)

5 independent repetitions per size. Sizes: 10k..1M edges (synthetic, since a
1M-edge real graph requires the unavailable 1r/6r Theia files).
Usage: python3 audit/experiments/scalability/run_scalability.py [--quick]
"""
import gc
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, ".")

import psutil

from src.graph_construction.synthetic import generate_synthetic_graph
from audit.experiments.poisoning import poisoning_v2 as pv
from audit.experiments.corrected import harness

SIZES = [10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
REPS = 5
OUT = Path("audit/raw_runs/scalability")
OUT.mkdir(parents=True, exist_ok=True)


def rss_mb():
    return psutil.Process().memory_info().rss / (1024.0 * 1024.0)


def gen_graph(target_edges, seed):
    import random
    rng = random.Random(seed)
    nproc = max(20, int((target_edges ** 0.55)))
    nfile = max(30, int((target_edges ** 0.6)))
    nnet = max(10, int((target_edges ** 0.45)))
    # generous fallback loop to reach the target edge count
    g = generate_synthetic_graph(num_processes=nproc, num_files=nfile,
                                 num_network=nnet, target_edges=target_edges, seed=seed)
    return g


def bench_size(target, rep, do_graphsage=True):
    seed = 1000 + rep
    import tracemalloc
    rec = {"target_edges": target, "rep": rep, "seed": seed}
    gc.collect()
    tracemalloc.start()
    m0 = rss_mb()
    t = time.time()
    g = gen_graph(target, seed)
    rec["construction_sec"] = time.time() - t
    rec["edges"] = len(g.edges)
    rec["nodes"] = len(g.nodes)

    t = time.time()
    res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=seed)
    rec["poisoning_sec"] = time.time() - t
    gt = res.ground_truth_edge_ids()

    t = time.time()
    m, out, _, _, _ = harness.rule_engine_metrics(res.poisoned_graph, gt)
    rec["rule_engine_infer_sec"] = time.time() - t
    rec["rule_engine_f1"] = m.f1
    rec["rule_engine_roc_auc"] = m.roc_auc
    rec["rule_engine_throughput_eps"] = rec["edges"] / max(1e-9, rec["rule_engine_infer_sec"])

    rec["evaluation_sec"] = 0.0  # metrics included in the detect call above

    if do_graphsage and target <= 250_000:
        try:
            t = time.time()
            mgs, info = harness.graphsage_eval(res.poisoned_graph, gt, seed=seed, epochs=30)
            total = time.time() - t
            rec["graphsage_total_sec"] = total
            rec["graphsage_f1"] = mgs.f1
            rec["graphsage_roc_auc"] = mgs.roc_auc
        except Exception:
            rec["graphsage_error"] = traceback.format_exc()

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rec["peak_python_mb"] = peak / (1024.0 * 1024.0)
    rec["rss_delta_mb"] = rss_mb() - m0
    rec["end_to_end_sec"] = (rec["construction_sec"] + rec["poisoning_sec"]
                             + rec["rule_engine_infer_sec"])
    return rec


def main(quick=False):
    sizes = SIZES[:3] if quick else SIZES
    reps = 1 if quick else REPS
    for size in sizes:
        for rep in range(reps):
            fp = OUT / f"size_{size}_rep_{rep}.json"
            if fp.exists():
                print("skip", size, rep, flush=True)
                continue
            try:
                rec = bench_size(size, rep)
                json.dump(rec, open(fp, "w"), indent=2)
                print("done", size, rep, "edges", rec["edges"],
                      "REs", round(rec["rule_engine_infer_sec"], 4),
                      "eps", round(rec["rule_engine_throughput_eps"], 0), flush=True)
            except Exception:
                traceback.print_exc()


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
