"""Generate audit plots (ROC/PR curves, scalability curves, mimicry curves)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RAW = ROOT / "audit" / "raw_runs"
PLOTS = ROOT / "audit" / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

from sklearn.metrics import precision_recall_curve, roc_curve

from src.detection.mimicry_attack import inject_mimicry_attack
from src.detection.poisoning_injection import inject_poisoning
from src.detection.rule_based import run_all_checks
from src.graph_construction.synthetic import generate_synthetic_graph


def rule_scores(graph, gt_ids):
    counts = {}
    for v in run_all_checks(graph):
        if v.edge_id:
            counts[v.edge_id] = counts.get(v.edge_id, 0) + 1
    y = np.array([1 if e.edge_id in gt_ids else 0 for e in graph.edges])
    sc = np.array([float(counts.get(e.edge_id, 0)) for e in graph.edges])
    return y, sc


def main():
    # ROC/PR for rule engine count score, seed 42, all strengths
    graph = generate_synthetic_graph(num_processes=40, num_files=50, num_network=15, seed=42)
    base = inject_poisoning(graph, 5, 5, 5, 5, seed=42)
    gt = {e.edge_id for e in base.events}

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for st in ["none", "light", "medium", "heavy"]:
        if st == "none":
            g = base.graph
        else:
            g = inject_mimicry_attack(graph, base_poisoning=base, strength=st, intensity=5, seed=42).graph
        y, sc = rule_scores(g, gt)
        if len(np.unique(y)) < 2:
            continue
        fpr, tpr, _ = roc_curve(y, sc)
        pr, rc, _ = precision_recall_curve(y, sc)
        from sklearn.metrics import auc
        axes[0].plot(fpr, tpr, label=f"{st} (AUC={auc(fpr,tpr):.3f})")
        axes[1].plot(rc, pr, label=f"{st}")
    axes[0].plot([0, 1], [0, 1], "k--", lw=1)
    axes[0].set_xlabel("FPR"); axes[0].set_ylabel("TPR"); axes[0].set_title("Rule Engine ROC (violation-count score)")
    axes[1].set_xlabel("Recall"); axes[1].set_ylabel("Precision"); axes[1].set_title("Rule Engine PR curve")
    for a in axes:
        a.grid(alpha=0.3); a.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "rule_engine_roc_pr.png", dpi=200)
    plt.close(fig)

    # scalability curves
    sc = json.load(open(RAW / "scalability_audit.json"))
    ns = sc["scales"]
    re_t = [sc["per_size"][str(n)]["aggregate"]["re_detector"]["mean"] for n in ns]
    re_ts = [sc["per_size"][str(n)]["aggregate"]["re_detector"]["std"] for n in ns]
    gs_t = [sc["per_size"][str(n)]["aggregate"]["gs_infer"]["mean"] for n in ns]
    gs_tr = [sc["per_size"][str(n)]["aggregate"]["gs_train_epoch"]["mean"] for n in ns]
    re_mem = [sc["per_size"][str(n)]["aggregate"]["re_peak_mb"]["mean"] for n in ns]
    gs_mem = [sc["per_size"][str(n)]["aggregate"]["gs_peak_mb"]["mean"] for n in ns]
    re_eps = [sc["per_size"][str(n)]["aggregate"]["re_throughput_eps"]["mean"] for n in ns]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    axes[0].errorbar(ns, re_t, yerr=re_ts, marker="o", label="Rule Engine detection")
    axes[0].plot(ns, gs_t, marker="s", ls="--", label="GraphSAGE inference")
    axes[0].plot(ns, gs_tr, marker="^", ls=":", label="GraphSAGE train / epoch")
    axes[0].set_xscale("log"); axes[0].set_yscale("log")
    axes[0].set_xlabel("edges"); axes[0].set_ylabel("seconds"); axes[0].set_title("Runtime vs graph size")
    axes[1].plot(ns, re_mem, marker="o", label="Rule Engine peak")
    axes[1].plot(ns, gs_mem, marker="s", ls="--", label="GraphSAGE peak")
    axes[1].set_xscale("log"); axes[1].set_yscale("log")
    axes[1].set_xlabel("edges"); axes[1].set_ylabel("MB"); axes[1].set_title("Peak memory vs graph size")
    axes[2].plot(ns, re_eps, marker="o", color="purple", label="Rule Engine")
    axes[2].set_xscale("log"); axes[2].set_xlabel("edges"); axes[2].set_ylabel("edges/sec")
    axes[2].set_title("Rule Engine throughput")
    for a in axes:
        a.grid(alpha=0.3, which="both"); a.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOTS / "scalability_curves.png", dpi=200)
    plt.close(fig)

    # mimicry curves (rule engine + graphsage from committed-style protocol)
    mi = json.load(open(RAW / "mimicry_audit.json"))
    labels = ["none", "light", "medium", "heavy"]
    f1s = [mi["strengths"][s]["aggregate"]["f1_mean"] for s in labels]
    precs = [mi["strengths"][s]["aggregate"]["precision_mean"] for s in labels]
    recs = [mi["strengths"][s]["aggregate"]["recall_mean"] for s in labels]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(labels, f1s, "o-", label="F1")
    ax.plot(labels, precs, "s--", label="Precision")
    ax.plot(labels, recs, "^:", label="Recall")
    ax.set_xlabel("Mimicry strength"); ax.set_ylabel("score")
    ax.set_title("Rule Engine under mimicry (10-seed mean)")
    ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(PLOTS / "mimicry_curves.png", dpi=200); plt.close(fig)

    print("Wrote plots to", PLOTS)


if __name__ == "__main__":
    main()
