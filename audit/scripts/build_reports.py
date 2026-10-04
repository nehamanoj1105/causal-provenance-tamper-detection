"""
Build journal-ready tables (CSV + Markdown + LaTeX) and plots from raw runs.

All raw values keep full float precision; rounding is applied only in the
presentation tables. Writes to audit/tables and audit/plots.
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")

ROOT = Path("audit")
RAW = ROOT / "raw_runs"
TAB = ROOT / "tables"
PLOTS = ROOT / "plots"
TAB.mkdir(parents=True, exist_ok=True)
PLOTS.mkdir(parents=True, exist_ok=True)

METRICS = ["precision", "recall", "f1", "accuracy", "balanced_accuracy",
           "mcc", "fpr", "fnr", "specificity", "roc_auc", "pr_auc"]


def summarize(vals):
    arr = np.array([v for v in vals if v is not None], dtype=float)
    if len(arr) == 0:
        return dict(n=0, mean=float("nan"), std=float("nan"), ci_low=float("nan"), ci_high=float("nan"))
    if len(arr) == 1:
        return dict(n=1, mean=float(arr[0]), std=0.0, ci_low=float("nan"), ci_high=float("nan"))
    m = float(np.mean(arr)); s = float(np.std(arr, ddof=1))
    try:
        from scipy import stats
        tc = float(stats.t.ppf(0.975, df=len(arr) - 1))
    except Exception:
        tc = 1.96
    return dict(n=len(arr), mean=m, std=s,
                ci_low=m - tc * s / math.sqrt(len(arr)),
                ci_high=m + tc * s / math.sqrt(len(arr)))


def _paired(a, b):
    a = np.array([x for x in a if x is not None], dtype=float)
    b = np.array([x for x in b if x is not None], dtype=float)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    d = a - b
    out = {"n": int(n), "mean_diff": float(np.mean(d)) if n else None,
           "median_diff": float(np.median(d)) if n else None}
    if n >= 2:
        sd = float(np.std(d, ddof=1))
        out["std_diff"] = sd
        if sd > 0:
            from scipy import stats
            tc = float(stats.t.ppf(0.975, df=n - 1))
            out["ci95_low"] = float(np.mean(d) - tc * sd / math.sqrt(n))
            out["ci95_high"] = float(np.mean(d) + tc * sd / math.sqrt(n))
            out["cohens_dz"] = float(np.mean(d) / sd)
            try:
                stat, p = stats.wilcoxon(a, b)
                out["wilcoxon_stat"] = float(stat); out["wilcoxon_p"] = float(p)
            except Exception:
                out["wilcoxon_stat"] = None; out["wilcoxon_p"] = None
        else:
            out.update(ci95_low=float(np.mean(d)), ci95_high=float(np.mean(d)),
                       cohens_dz=0.0, wilcoxon_stat=None, wilcoxon_p=None)
    return out


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def md_table(rows, fields):
    lines = ["| " + " | ".join(fields) + " |",
             "|" + "|".join(["---"] * len(fields)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in fields) + " |")
    return "\n".join(lines)


def latex_table(rows, fields, caption="", label=""):
    cols = "l" + "r" * (len(fields) - 1)
    out = [f"\\begin{{table}}[htbp]", "\\centering",
           f"\\caption{{{caption}}}", f"\\label{{{label}}}",
           f"\\begin{{tabular}}{{{cols}}}", "\\hline",
           " & ".join(fields) + " \\\\", "\\hline"]
    for r in rows:
        out.append(" & ".join(str(r.get(k, "")) for k in fields) + " \\\\")
    out += ["\\hline", "\\end{tabular}", "\\end{table}"]
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_dir(pattern):
    return [json.load(open(p)) for p in sorted(Path(".").glob(str(pattern)))]


def synthetic_tables():
    recs = load_dir(RAW / "synthetic" / "seed_*.json")
    recs = [r for r in recs if "seed" in r]
    recs.sort(key=lambda r: r["seed"])
    fields = ["detector", "metric"] + [k for k in ["mean", "std", "median", "min", "max", "ci95_low", "ci95_high", "n"]]
    rows = []
    for det, key in [("Rule Engine", "rule_engine"), ("GraphSAGE", "graphsage")]:
        for m in METRICS:
            s = summarize([r.get(key, {}).get(m) for r in recs])
            rows.append({"detector": det, "metric": m,
                         **{k: (None if s.get(k) is None else s[k]) for k in fields[2:]}})
    write_csv(TAB / "table2_synthetic_detection.csv", rows, fields)
    Path(TAB / "table2_synthetic_detection.md").write_text(md_table(
        [{k: (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]) for k in fields} for r in rows], fields))
    Path(TAB / "table2_synthetic_detection.tex").write_text(latex_table(
        [{k: (f"{r[k]:.4f}" if isinstance(r[k], float) else r[k]) for k in fields} for r in rows],
        fields, "Synthetic edge-poisoning detection, 10 seeds.", "tab:synthetic"))
    return recs


def mimicry_table():
    recs = load_dir(RAW / "synthetic" / "seed_*.json")
    rows = []
    for strength in ["none", "light", "medium", "heavy"]:
        for det in ["rule_engine", "graphsage"]:
            agg = {m: summarize([r["mimicry"][strength].get(det, {}).get(m) for r in recs
                                 if strength in r.get("mimicry", {})]) for m in METRICS}
            rows.append({"strength": strength, "detector": det,
                         "noise_edges_mean": summarize([r["mimicry"][strength]["noise_edges"] for r in recs
                                                        if strength in r.get("mimicry", {})])["mean"],
                         "noise_self_violations_mean": summarize(
                             [float(sum(r["mimicry"][strength]["noise_self_violations"].values()))
                              for r in recs if strength in r.get("mimicry", {})])["mean"],
                         "f1_mean": agg["f1"]["mean"], "f1_std": agg["f1"]["std"],
                         "precision_mean": agg["precision"]["mean"],
                         "recall_mean": agg["recall"]["mean"],
                         "roc_auc_mean": agg["roc_auc"]["mean"],
                         "pr_auc_mean": agg["pr_auc"]["mean"]})
    fields = ["strength", "detector", "noise_edges_mean", "noise_self_violations_mean",
              "precision_mean", "recall_mean", "f1_mean", "f1_std", "roc_auc_mean", "pr_auc_mean"]
    write_csv(TAB / "table4_mimicry.csv", rows, fields)
    Path(TAB / "table4_mimicry.md").write_text(md_table(rows, fields))
    return rows


def ablation_table():
    recs = load_dir(RAW / "ablation" / "seed_*.json")
    if not recs:
        return []
    variants = sorted(recs[0]["variants"].keys())
    rows = []
    for v in variants:
        f1s = [r["variants"][v]["metrics"]["f1"] for r in recs if v in r["variants"]]
        rocs = [r["variants"][v]["metrics"]["roc_auc"] for r in recs if v in r["variants"]]
        s = summarize(f1s); sr = summarize(rocs)
        rows.append({"variant": v, "f1_mean": s["mean"], "f1_std": s["std"],
                     "roc_auc_mean": sr["mean"], "roc_auc_std": sr["std"]})
    fields = ["variant", "f1_mean", "f1_std", "roc_auc_mean", "roc_auc_std"]
    write_csv(TAB / "table5_ablation.csv", rows, fields)
    Path(TAB / "table5_ablation.md").write_text(md_table(rows, fields))
    return rows


def darpa_table():
    rows = []
    for ds in ["theia3", "theia5m"]:
        for p in sorted(RAW.glob(f"darpa/{ds}_*.json")):
            r = json.load(open(p))
            rb = r["real_data_rule_behaviour"]
            rows.append({"dataset": ds, "edges_loaded": r["n_edges_loaded"],
                         "graph_edges": r["graph_edges"], "truncated": r["truncated"],
                         "real_flagged": rb["flagged_edges"],
                         "real_flag_rate": rb["flag_rate"],
                         "eval_type": "real_data_rule_behaviour"})
            seeds = r["synthetic_post_collection_poisoning"]
            for det in ["rule_engine", "graphsage"]:
                f1s = [e[det]["f1"] for e in seeds if det in e]
                rocs = [e[det]["roc_auc"] for e in seeds if det in e]
                if f1s:
                    rows.append({"dataset": ds, "eval_type": f"synthetic_post_collection::{det}",
                                 "f1_mean": summarize(f1s)["mean"], "f1_std": summarize(f1s)["std"],
                                 "roc_auc_mean": summarize(rocs)["mean"],
                                 "roc_auc_std": summarize(rocs)["std"],
                                 "n_seeds": len(f1s)})
    fields = ["dataset", "eval_type", "edges_loaded", "graph_edges", "truncated",
              "real_flagged", "real_flag_rate", "f1_mean", "f1_std", "roc_auc_mean",
              "roc_auc_std", "n_seeds"]
    write_csv(TAB / "table3_darpa.csv", rows, fields)
    Path(TAB / "table3_darpa.md").write_text(md_table(rows, fields))
    return rows


def scalability_table():
    recs = load_dir(RAW / "scalability" / "size_*.json")
    by_size = {}
    for r in recs:
        by_size.setdefault(r["edges"], []).append(r)
    rows = []
    for size in sorted(by_size):
        rs = by_size[size]
        def agg(key):
            return summarize([x.get(key) for x in rs])
        rows.append({"edges": size,
                     "construction_sec": agg("construction_sec")["mean"],
                     "poisoning_sec": agg("poisoning_sec")["mean"],
                     "rule_engine_infer_sec": agg("rule_engine_infer_sec")["mean"],
                     "end_to_end_sec": agg("end_to_end_sec")["mean"],
                     "peak_python_mb": agg("peak_python_mb")["mean"],
                     "rss_delta_mb": agg("rss_delta_mb")["mean"],
                     "threshold_eps": agg("rule_engine_throughput_eps")["mean"],
                     "graphsage_total_sec": agg("graphsage_total_sec")["mean"],
                     "n_reps": len(rs)})
    fields = ["edges", "construction_sec", "poisoning_sec", "rule_engine_infer_sec",
              "end_to_end_sec", "peak_python_mb", "rss_delta_mb", "threshold_eps",
              "graphsage_total_sec", "n_reps"]
    write_csv(TAB / "table6_scalability.csv", rows, fields)
    Path(TAB / "table6_scalability.md").write_text(md_table(rows, fields))
    return rows


def stats_table():
    recs = load_dir(RAW / "synthetic" / "seed_*.json")
    recs = [r for r in recs if "graphsage" in r]
    re_f1 = [r["rule_engine"]["f1"] for r in recs]
    gs_f1 = [r["graphsage"]["f1"] for r in recs]
    re_roc = [r["rule_engine"]["roc_auc"] for r in recs]
    gs_roc = [r["graphsage"]["roc_auc"] for r in recs]
    pf = _paired(re_f1, gs_f1)
    pr = _paired(re_roc, gs_roc)
    rows = [
        {"comparison": "RuleEngine_vs_GraphSAGE_F1", **pf},
        {"comparison": "RuleEngine_vs_GraphSAGE_ROC_AUC", **pr},
    ]
    fields = ["comparison", "n", "mean_diff", "std_diff", "ci95_low", "ci95_high",
              "cohens_dz", "wilcoxon_stat", "wilcoxon_p"]
    write_csv(TAB / "table8_statistics.csv", rows, fields)
    Path(TAB / "table8_statistics.md").write_text(md_table(rows, fields))
    return rows


def multiseed_table():
    recs = load_dir(RAW / "synthetic" / "seed_*.json")
    rows = []
    for m in METRICS:
        for det, key in [("RuleEngine", "rule_engine"), ("GraphSAGE", "graphsage")]:
            s = summarize([r.get(key, {}).get(m) for r in recs])
            rows.append({"detector": det, "metric": m, "mean": s["mean"], "std": s["std"],
                         "median": summarize([r.get(key, {}).get(m) for r in recs])["median"]
                         if False else None})
    # median computation
    for row in rows:
        vals = [r.get("rule_engine" if row["detector"] == "RuleEngine" else "graphsage", {}).get(row["metric"]) for r in recs]
        arr = np.array([v for v in vals if v is not None], dtype=float)
        row["median"] = float(np.median(arr)); row["min"] = float(np.min(arr)); row["max"] = float(np.max(arr))
    fields = ["detector", "metric", "mean", "std", "median", "min", "max"]
    write_csv(TAB / "table7_multiseed.csv", rows, fields)
    Path(TAB / "table7_multiseed.md").write_text(md_table(rows, fields))
    return rows


def plot_curves():
    """ROC and PR curves for Rule Engine (continuous score) on synthetic seed 42."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, precision_recall_curve
    p = RAW / "synthetic" / "seed_42.json"
    if not p.exists():
        return
    r = json.load(open(p))
    # recompute scores from graph
    import sys
    sys.path.insert(0, ".")
    from src.graph_construction.synthetic import generate_synthetic_graph
    from audit.experiments.poisoning import poisoning_v2 as pv
    from audit.experiments.corrected import harness
    g = generate_synthetic_graph(30, 40, 10, seed=42)
    res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=42)
    gt = res.ground_truth_edge_ids()
    m, out, y_true, y_score, ids = harness.rule_engine_metrics(res.poisoned_graph, gt)
    fpr, tpr, _ = roc_curve(y_true, y_score)
    prec, rec, _ = precision_recall_curve(y_true, y_score)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    ax[0].plot(fpr, tpr, lw=2)
    ax[0].plot([0, 1], [0, 1], "--", color="grey")
    ax[0].set_title(f"Rule Engine ROC (AUC={m.roc_auc:.4f})")
    ax[0].set_xlabel("FPR"); ax[0].set_ylabel("TPR")
    ax[1].plot(rec, prec, lw=2)
    ax[1].set_title(f"Rule Engine PR (AP={m.pr_auc:.4f})")
    ax[1].set_xlabel("Recall"); ax[1].set_ylabel("Precision")
    fig.tight_layout()
    fig.savefig(PLOTS / "rule_engine_roc_pr_seed42.png", dpi=150)
    plt.close(fig)


def plot_scalability():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    recs = load_dir(RAW / "scalability" / "size_*.json")
    if not recs:
        return
    by_size = {}
    for r in recs:
        by_size.setdefault(r["edges"], []).append(r)
    xs = sorted(by_size)
    def mean(key):
        return [np.mean([x.get(key, np.nan) for x in by_size[s]]) for s in xs]
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
    ax[0].plot(xs, mean("rule_engine_infer_sec"), "o-")
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_title("Rule Engine inference time"); ax[0].set_xlabel("edges"); ax[0].set_ylabel("s")
    ax[1].plot(xs, mean("peak_python_mb"), "o-")
    ax[1].set_xscale("log")
    ax[1].set_title("Peak Python allocation"); ax[1].set_xlabel("edges"); ax[1].set_ylabel("MB")
    ax[2].plot(xs, mean("rule_engine_throughput_eps"), "o-")
    ax[2].set_xscale("log"); ax[2].set_yscale("log")
    ax[2].set_title("Rule Engine throughput"); ax[2].set_xlabel("edges"); ax[2].set_ylabel("edges/s")
    fig.tight_layout()
    fig.savefig(PLOTS / "scalability.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    synthetic_tables()
    mimicry_table()
    ablation_table()
    darpa_table()
    scalability_table()
    stats_table()
    multiseed_table()
    try:
        plot_curves(); plot_scalability()
    except Exception as e:
        print("plot error", e)
    print("tables + plots written")
