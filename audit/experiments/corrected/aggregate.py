"""Aggregate raw per-seed runs into multi-seed statistics and paired tests."""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

from audit.experiments.corrected.metrics import summarize, paired_stats

METRIC_KEYS = ["precision", "recall", "f1", "accuracy", "balanced_accuracy",
               "mcc", "fpr", "fnr", "specificity", "roc_auc", "pr_auc"]


def load_seeds(directory: Path) -> list[dict]:
    recs = []
    for fp in sorted(directory.glob("seed_*.json")):
        recs.append(json.load(open(fp)))
    recs.sort(key=lambda r: r["seed"])
    return recs


def collect(recs, detector, metrics=METRIC_KEYS):
    return {k: [r.get(detector, {}).get(k) for r in recs] for k in metrics}


def summarize_detector(recs, detector, metrics=METRIC_KEYS):
    data = collect(recs, detector, metrics)
    return {k: summarize([v for v in data[k] if v is not None]) for k in metrics}


def full_report(directory: Path):
    recs = load_seeds(directory)
    out = {
        "n_seeds": len(recs),
        "seeds": [r["seed"] for r in recs],
        "rule_engine": summarize_detector(recs, "rule_engine"),
        "graphsage": summarize_detector(recs, "graphsage"),
    }
    # paired F1 and ROC-AUC
    re_f1 = [r["rule_engine"]["f1"] for r in recs]
    gs_f1 = [r["graphsage"]["f1"] for r in recs if "graphsage" in r]
    re_f1b = [r["rule_engine"]["f1"] for r in recs if "graphsage" in r]
    out["paired_f1"] = paired_stats(re_f1b, gs_f1)
    re_r = [r["rule_engine"]["roc_auc"] for r in recs if "graphsage" in r]
    gs_r = [r["graphsage"]["roc_auc"] for r in recs if "graphsage" in r]
    if all(v is not None for v in re_r + gs_r):
        out["paired_roc_auc"] = paired_stats(re_r, gs_r)
    out["per_seed"] = [
        {"seed": r["seed"],
         "re_f1": r["rule_engine"]["f1"],
         "gs_f1": r.get("graphsage", {}).get("f1"),
         "re_roc": r["rule_engine"].get("roc_auc"),
         "gs_roc": r.get("graphsage", {}).get("roc_auc")}
        for r in recs
    ]
    return out


if __name__ == "__main__":
    import sys
    d = Path(sys.argv[1])
    rep = full_report(d)
    print(json.dumps(rep, indent=2))
