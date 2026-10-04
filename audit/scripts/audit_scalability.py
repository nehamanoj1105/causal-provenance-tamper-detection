"""
Scalability audit (Phase 11).

For each graph size and each of >=5 independent repetitions, measure separately:
  graph construction time, poisoning time, detector time, evaluation time,
  end-to-end time, RSS memory, peak Python allocation, throughput.

GraphSAGE is split into TRAINING time and INFERENCE time so the two are never
compared as if equivalent (the repo's scalability module reports inference only,
yet the paper text compares it to rule-engine inference).

Writes audit/raw_runs/scalability_audit.json and .csv.
"""
from __future__ import annotations

import csv
import gc
import json
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import torch
import torch.nn as nn
import torch.optim as optim

from src.detection.poisoning_injection import inject_poisoning
from src.detection.rule_engine import default_rule_engine
from src.eval.evaluator import Evaluator
from src.graph_construction.synthetic import generate_synthetic_graph
from src.ml.dataset import provenance_to_pyg_data
from src.ml.graphsage import GraphSAGEForTamperDetection
from src.ml.utils import get_device, set_seed

SCALES = [10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
REPS = 5
INTENSITY = 5
TRAIN_EPOCHS = 3


def rss_mb():
    return psutil.Process().memory_info().rss / (1024 * 1024)


def make_graph(n):
    procs = max(10, n // 20)
    files = max(10, n // 10)
    net = max(5, procs // 5)
    return generate_synthetic_graph(num_processes=procs, num_files=files, num_network=net,
                                    target_edges=n, seed=42)


def main():
    out = {"scales": SCALES, "reps": REPS, "intensity": INTENSITY,
           "graphsage_train_epochs": TRAIN_EPOCHS, "per_size": {}}

    for n in SCALES:
        reps = []
        for rep in range(REPS):
            seed = 42 + rep
            gc.collect()
            t0 = time.time()
            graph = make_graph(n)
            t_construct = time.time() - t0

            t0 = time.time()
            poison = inject_poisoning(graph, INTENSITY, INTENSITY, INTENSITY, INTENSITY, seed=seed)
            t_poison = time.time() - t0

            # --- Rule engine detector ---
            gc.collect()
            tracemalloc.start()
            rss_before = rss_mb()
            t0 = time.time()
            engine = default_rule_engine()
            rr = engine.run(poison.graph)
            t_re_detector = time.time() - t0
            t0 = time.time()
            ev = Evaluator().evaluate(ground_truth=poison, detected_violations=rr, graph=poison.graph)
            t_re_eval = time.time() - t0
            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            rss_after = rss_mb()
            re_peak = max(peak_bytes / (1024 * 1024), rss_after - rss_before)

            # --- GraphSAGE inference ---
            set_seed(seed)
            device = get_device()
            pyg = provenance_to_pyg_data(poison.graph, poisoning_result=poison)
            model = GraphSAGEForTamperDetection(in_channels=pyg.x.size(1), hidden_channels=64).to(device)
            model.eval()
            gc.collect()
            tracemalloc.start()
            rss_before = rss_mb()
            t0 = time.time()
            with torch.no_grad():
                _, logits, _ = model(pyg.x.to(device), pyg.edge_index.to(device))
                probs = torch.sigmoid(logits).cpu().numpy()
                preds = (probs >= 0.5).astype(int)
            t_gs_infer = time.time() - t0
            edge_id_map = getattr(pyg, "edge_id_map", {})
            flagged = {edge_id_map[i] for i, p in enumerate(preds) if p == 1 and i in edge_id_map}
            t0 = time.time()
            Evaluator().evaluate(ground_truth=poison, detected_violations=flagged, graph=poison.graph)
            t_gs_eval = time.time() - t0
            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            rss_after = rss_mb()
            gs_peak = max(peak_bytes / (1024 * 1024), rss_after - rss_before)

            # --- GraphSAGE training (few epochs, reported separately) ---
            set_seed(seed)
            tmodel = GraphSAGEForTamperDetection(in_channels=pyg.x.size(1), hidden_channels=64).to(device)
            npos = float((pyg.edge_label == 1).sum().item())
            nneg = float((pyg.edge_label == 0).sum().item())
            crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([nneg / max(1.0, npos)], device=device))
            opt = optim.Adam(tmodel.parameters(), lr=0.01, weight_decay=1e-4)
            t_train_start = time.time()
            for _ in range(TRAIN_EPOCHS):
                tmodel.train(); opt.zero_grad()
                _, lg, _ = tmodel(pyg.x.to(device), pyg.edge_index.to(device))
                loss = crit(lg, pyg.edge_label.to(device))
                loss.backward(); opt.step()
            t_gs_train_total = time.time() - t_train_start
            t_gs_train_epoch = t_gs_train_total / TRAIN_EPOCHS

            reps.append({
                "rep": rep, "seed": seed,
                "nodes": len(graph.nodes), "edges": len(graph.edges),
                "t_construct": t_construct, "t_poison": t_poison,
                "re_detector": t_re_detector, "re_eval": t_re_eval,
                "re_total": t_construct + t_poison + t_re_detector + t_re_eval,
                "re_rss_mb": rss_after, "re_peak_mb": re_peak,
                "re_throughput_eps": len(poison.graph.edges) / t_re_detector if t_re_detector > 0 else 0.0,
                "gs_infer": t_gs_infer, "gs_eval": t_gs_eval,
                "gs_total": t_construct + t_poison + t_gs_infer + t_gs_eval,
                "gs_rss_mb": rss_after, "gs_peak_mb": gs_peak,
                "gs_throughput_eps": len(poison.graph.edges) / t_gs_infer if t_gs_infer > 0 else 0.0,
                "gs_train_total": t_gs_train_total, "gs_train_epoch": t_gs_train_epoch,
            })
            del graph, poison, pyg, model, tmodel, rr, ev
            gc.collect()

        keys = [k for k in reps[0] if k not in ("rep", "seed")]
        agg = {}
        for k in keys:
            vals = np.array([r[k] for r in reps], dtype=float)
            agg[k] = {"mean": float(vals.mean()), "std": float(vals.std(ddof=1)),
                      "median": float(np.median(vals)), "min": float(vals.min()), "max": float(vals.max())}
        out["per_size"][n] = {"reps": reps, "aggregate": agg}
        print(f"n={n:>9,}  RE det={agg['re_detector']['mean']:.4f}s ({agg['re_throughput_eps']['mean']:,.0f} eps) "
              f"| GS infer={agg['gs_infer']['mean']:.4f}s | GS train/epoch={agg['gs_train_epoch']['mean']:.3f}s "
              f"| peak RE={agg['re_peak_mb']['mean']:.1f}MB GS={agg['gs_peak_mb']['mean']:.1f}MB")

    outdir = ROOT / "audit" / "raw_runs"
    with open(outdir / "scalability_audit.json", "w") as f:
        json.dump(out, f, indent=2)

    with open(outdir / "scalability_audit.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["edges", "detector", "metric", "mean", "std", "median", "min", "max"])
        for n, d in out["per_size"].items():
            for k, v in d["aggregate"].items():
                w.writerow([n, k, k, v["mean"], v["std"], v["median"], v["min"], v["max"]])
    print("\nWrote", outdir / "scalability_audit.json")


if __name__ == "__main__":
    main()
