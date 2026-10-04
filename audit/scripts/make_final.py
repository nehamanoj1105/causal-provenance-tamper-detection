"""
Build the final audit deliverables from the corrected raw runs.

Outputs:
  audit/final_result_reconciliation.csv
  audit/journal_ready_tables/*.{csv,md,tex}
  audit/plots/*.png
  (final_audit_report.md is written separately / composed here)
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")

ROOT = Path("audit")
RAW = ROOT / "raw_runs"
TAB = ROOT / "journal_ready_tables"
PLOTS = ROOT / "plots"
TAB.mkdir(parents=True, exist_ok=True)
PLOTS.mkdir(parents=True, exist_ok=True)

METRICS = ["precision", "recall", "f1", "accuracy", "balanced_accuracy",
           "mcc", "fpr", "fnr", "specificity", "roc_auc", "pr_auc"]


def load(pattern):
    return [json.load(open(p)) for p in sorted(Path(".").glob(str(pattern)))]


def summ(vals):
    arr = np.array([v for v in vals if v is not None], dtype=float)
    n = len(arr)
    if n == 0:
        return dict(n=0, mean="", std="", median="", min="", max="", ci_low="", ci_high="")
    if n == 1:
        return dict(n=1, mean=float(arr[0]), std=0.0, median=float(arr[0]),
                    min=float(arr[0]), max=float(arr[0]), ci_low="", ci_high="")
    m = float(np.mean(arr)); s = float(np.std(arr, ddof=1))
    try:
        from scipy import stats
        tc = float(stats.t.ppf(0.975, df=n - 1))
    except Exception:
        tc = 1.96
    return dict(n=n, mean=m, std=s, median=float(np.median(arr)),
                min=float(np.min(arr)), max=float(np.max(arr)),
                ci_low=m - tc * s / math.sqrt(n), ci_high=m + tc * s / math.sqrt(n))


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def md(rows, fields):
    out = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(k, "")) for k in fields) + " |")
    return "\n".join(out) + "\n"


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.4f}"
    return v


def tex(rows, fields, caption="", label=""):
    cols = "l" + "r" * (len(fields) - 1)
    out = ["\\begin{table}[htbp]", "\\centering", f"\\caption{{{caption}}}",
           f"\\label{{{label}}}", f"\\begin{{tabular}}{{{cols}}}", "\\hline",
           " & ".join(fields) + " \\\\", "\\hline"]
    for r in rows:
        out.append(" & ".join(str(_fmt(r.get(k, ""))) for k in fields) + " \\\\")
    out += ["\\hline", "\\end{tabular}", "\\end{table}"]
    return "\n".join(out) + "\n"


def table(name, rows, fields, caption="", label=""):
    write_csv(TAB / f"{name}.csv", rows, fields)
    (TAB / f"{name}.md").write_text(md(rows, fields))
    (TAB / f"{name}.tex").write_text(tex(rows, fields, caption, label))


def synthetic_tables():
    recs = [r for r in load(RAW / "synthetic" / "seed_*.json") if "seed" in r]
    recs.sort(key=lambda r: r["seed"])
    rows = []
    for det, key in [("RuleEngine", "rule_engine"), ("GraphSAGE", "graphsage")]:
        for m in METRICS:
            s = summ([r.get(key, {}).get(m) for r in recs])
            rows.append({"detector": det, "metric": m, **s})
    fields = ["detector", "metric", "n", "mean", "std", "median", "min", "max", "ci_low", "ci_high"]
    table("table2_synthetic_detection", rows, fields, "Synthetic edge-poisoning detection, 10 seeds (mean/std/median/min/max/95% CI).", "tab:synthetic")
    table("table7_multiseed", rows, fields, "Multi-seed mean/std/median/min/max, 10 seeds.", "tab:multiseed")
    return recs


def mimicry_tables(recs):
    rows = []
    for strength in ["none", "light", "medium", "heavy"]:
        for det, label in [("rule_engine", "RuleEngine"), ("graphsage", "GraphSAGE")]:
            d = [r["mimicry"][strength] for r in recs if strength in r.get("mimicry", {})]
            rows.append({
                "strength": strength, "detector": label,
                "base_edges": summ([x["base_edges"] for x in d])["mean"],
                "mimicry_edges": summ([x["noise_edges"] for x in d])["mean"],
                "final_edges": summ([x["final_edges"] for x in d])["mean"],
                "noise_self_violations": summ([float(sum(x["noise_self_violations"].values())) for x in d])["mean"],
                "precision_mean": summ([x.get(det, {}).get("precision") for x in d])["mean"],
                "recall_mean": summ([x.get(det, {}).get("recall") for x in d])["mean"],
                "f1_mean": summ([x.get(det, {}).get("f1") for x in d])["mean"],
                "f1_std": summ([x.get(det, {}).get("f1") for x in d])["std"],
                "roc_auc_mean": summ([x.get(det, {}).get("roc_auc") for x in d])["mean"],
                "pr_auc_mean": summ([x.get(det, {}).get("pr_auc") for x in d])["mean"],
            })
    fields = ["strength", "detector", "base_edges", "mimicry_edges", "final_edges",
              "noise_self_violations", "precision_mean", "recall_mean", "f1_mean",
              "f1_std", "roc_auc_mean", "pr_auc_mean"]
    table("table4_mimicry_robustness", rows, fields, "Mimicry robustness with label-free, invariant-preserving camouflage.", "tab:mimicry")
    return rows


def ablation_tables():
    recs = load(RAW / "ablation" / "seed_*.json")
    if not recs:
        return []
    variants = sorted(recs[0]["variants"].keys())
    rows = []
    for v in variants:
        s = summ([r["variants"][v]["metrics"]["f1"] for r in recs if v in r["variants"]])
        rows.append({"variant": v, **s})
    fields = ["variant", "n", "mean", "std", "median", "min", "max", "ci_low", "ci_high"]
    table("table5_rule_ablation", rows, fields, "Rule-group and leave-one-rule-out ablation, 10 seeds.", "tab:ablation")
    return rows


def darpa_tables():
    rows = []
    for ds in ["theia3", "theia5m"]:
        for p in sorted((RAW / "darpa").glob(f"{ds}_*.json")):
            r = json.load(open(p))
            seeds = r["synthetic_post_collection_poisoning"]
            for det in ["rule_engine", "graphsage"]:
                f1s = [e[det]["f1"] for e in seeds if det in e]
                if not f1s:
                    continue
                rows.append({
                    "dataset": ds, "eval_type": f"synthetic_post_collection_{det}",
                    "edges": r["graph_edges"], "truncated": r["truncated"],
                    "n": len(f1s),
                    "f1_mean": summ(f1s)["mean"], "f1_std": summ(f1s)["std"],
                    "precision_mean": summ([e[det]["precision"] for e in seeds if det in e])["mean"],
                    "recall_mean": summ([e[det]["recall"] for e in seeds if det in e])["mean"],
                    "roc_auc_mean": summ([e[det]["roc_auc"] for e in seeds if det in e])["mean"],
                })
    fields = ["dataset", "eval_type", "edges", "truncated", "n", "f1_mean", "f1_std",
              "precision_mean", "recall_mean", "roc_auc_mean"]
    table("table3_darpa_cross_scenario", rows, fields, "Real Theia (50k-edge cap) with synthetic post-collection poisoning.", "tab:darpa")
    return rows


def scalability_tables():
    recs = load(RAW / "scalability" / "size_*.json")
    if not recs:
        return []
    by = {}
    for r in recs:
        by.setdefault(r["edges"], []).append(r)
    rows = []
    for size in sorted(by):
        rs = by[size]
        rows.append({
            "edges": size, "n_reps": len(rs),
            "construction_sec": summ([x["construction_sec"] for x in rs])["mean"],
            "poisoning_sec": summ([x["poisoning_sec"] for x in rs])["mean"],
            "rule_engine_infer_sec": summ([x["rule_engine_infer_sec"] for x in rs])["mean"],
            "rule_engine_infer_std": summ([x["rule_engine_infer_sec"] for x in rs])["std"],
            "end_to_end_sec": summ([x["end_to_end_sec"] for x in rs])["mean"],
            "peak_python_mb": summ([x["peak_python_mb"] for x in rs])["mean"],
            "rss_delta_mb": summ([x["rss_delta_mb"] for x in rs])["mean"],
            "throughput_eps": summ([x["rule_engine_throughput_eps"] for x in rs])["mean"],
        })
    fields = ["edges", "n_reps", "construction_sec", "poisoning_sec",
              "rule_engine_infer_sec", "rule_engine_infer_std", "end_to_end_sec",
              "peak_python_mb", "rss_delta_mb", "throughput_eps"]
    table("table6_scalability", rows, fields, "Scalability: separate construction/poisoning/detection phases, 5 reps.", "tab:scalability")
    return rows


def generalization_tables():
    recs = load(RAW / "generalization" / "*.json")
    if not recs:
        return []
    by = {}
    for r in recs:
        by.setdefault((r["source"], r["target"]), []).append(r)
    rows = []
    for (src, tgt), rs in sorted(by.items()):
        re_f1 = [x["rule_engine_target"]["f1"] for x in rs]
        gs_f1 = [x["graphsage_target_own_model"]["f1"] for x in rs
                 if "graphsage_target_own_model" in x]
        rows.append({
            "source": src, "target": tgt, "n": len(rs),
            "rule_engine_f1_mean": summ(re_f1)["mean"],
            "rule_engine_f1_std": summ(re_f1)["std"],
            "graphsage_own_model_f1_mean": summ(gs_f1)["mean"] if gs_f1 else "",
            "graphsage_own_model_f1_std": summ(gs_f1)["std"] if gs_f1 else "",
        })
    fields = ["source", "target", "n", "rule_engine_f1_mean", "rule_engine_f1_std",
              "graphsage_own_model_f1_mean", "graphsage_own_model_f1_std"]
    table("table9_generalization", rows, fields,
          "Cross-dataset generalization, 5 seeds per pair.", "tab:generalization")
    return rows


def stats_table(recs):
    recs = [r for r in recs if "graphsage" in r]
    rows = []
    for metric in ["f1", "roc_auc"]:
        a = np.array([r["rule_engine"][metric] for r in recs], float)
        b = np.array([r["graphsage"][metric] for r in recs], float)
        d = a - b
        n = len(d)
        sd = float(np.std(d, ddof=1))
        try:
            from scipy import stats
            tc = float(stats.t.ppf(0.975, df=n - 1))
            stat, p = stats.wilcoxon(a, b)
        except Exception:
            tc, stat, p = 1.96, None, None
        rows.append({
            "metric": metric, "n": n, "mean_diff": float(np.mean(d)),
            "median_diff": float(np.median(d)),
            "std_diff": sd,
            "ci_low": float(np.mean(d)) - tc * sd / math.sqrt(n),
            "ci_high": float(np.mean(d)) + tc * sd / math.sqrt(n),
            "cohens_dz": float(np.mean(d) / sd) if sd else "",
            "wilcoxon_stat": float(stat) if stat is not None else "",
            "wilcoxon_p": float(p) if p is not None else "",
        })
    fields = ["metric", "n", "mean_diff", "median_diff", "std_diff", "ci_low",
              "ci_high", "cohens_dz", "wilcoxon_stat", "wilcoxon_p"]
    table("table8_significance", rows, fields, "Paired RuleEngine vs GraphSAGE differences, 10 seeds.", "tab:significance")
    return rows


def dataset_table():
    manifest = ROOT / "parsing" / "theia_validation.json"
    rows = []
    for ds, label in [("theia3", "DARPA TC E3 Theia (scenario 3)"),
                      ("theia5m", "DARPA TC E3 Theia (scenario 5m)")]:
        fp = ROOT / "parsing" / f"{ds}_manifest.json"
        if fp.exists():
            m = json.load(open(fp))
            rows.append({"source": label, "nodes": m.get("nodes"),
                         "edges": m.get("edges"),
                         "skipped": m.get("skipped_records", 0),
                         "parse_sec": m.get("parse_seconds")})
    fields = ["source", "nodes", "edges", "skipped", "parse_sec"]
    table("table1_dataset_characteristics", rows, fields, "Real DARPA TC E3 Theia parsed dataset characteristics.", "tab:datasets")
    return rows


def plots(recs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, precision_recall_curve
    sys.path.insert(0, ".")
    from src.graph_construction.synthetic import generate_synthetic_graph
    from audit.experiments.poisoning import poisoning_v2 as pv
    from audit.experiments.corrected import harness
    g = generate_synthetic_graph(30, 40, 10, seed=42)
    res = pv.inject_poisoning_v2(g, 5, 5, 5, 5, seed=42)
    gt = res.ground_truth_edge_ids()
    m, out, yt, ys, ids = harness.rule_engine_metrics(res.poisoned_graph, gt)
    fpr, tpr, _ = roc_curve(yt, ys)
    prec, rec, _ = precision_recall_curve(yt, ys)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    ax[0].plot(fpr, tpr, lw=2); ax[0].plot([0, 1], [0, 1], "--", color="grey")
    ax[0].set_title(f"Rule Engine ROC (AUC={m.roc_auc:.4f})")
    ax[0].set_xlabel("FPR"); ax[0].set_ylabel("TPR")
    ax[1].plot(rec, prec, lw=2)
    ax[1].set_title(f"Rule Engine PR (AP={m.pr_auc:.4f})")
    ax[1].set_xlabel("Recall"); ax[1].set_ylabel("Precision")
    fig.tight_layout(); fig.savefig(PLOTS / "rule_engine_roc_pr_seed42.png", dpi=150)
    plt.close(fig)

    scal = load(RAW / "scalability" / "size_*.json")
    if scal:
        by = {}
        for r in scal:
            by.setdefault(r["edges"], []).append(r)
        xs = sorted(by)
        fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
        ax[0].plot(xs, [np.mean([x["rule_engine_infer_sec"] for x in by[s]]) for s in xs], "o-")
        ax[0].set_xscale("log"); ax[0].set_yscale("log")
        ax[0].set_title("Rule Engine inference time"); ax[0].set_xlabel("edges"); ax[0].set_ylabel("s")
        ax[1].plot(xs, [np.mean([x["peak_python_mb"] for x in by[s]]) for s in xs], "o-")
        ax[1].set_xscale("log"); ax[1].set_title("Peak Python allocation")
        ax[1].set_xlabel("edges"); ax[1].set_ylabel("MB")
        ax[2].plot(xs, [np.mean([x["rule_engine_throughput_eps"] for x in by[s]]) for s in xs], "o-")
        ax[2].set_xscale("log"); ax[2].set_yscale("log")
        ax[2].set_title("Throughput"); ax[2].set_xlabel("edges"); ax[2].set_ylabel("edges/s")
        fig.tight_layout(); fig.savefig(PLOTS / "scalability_corrected.png", dpi=150)
        plt.close(fig)


def reconciliation(recs, mimic, abl, darpa, scal, stats):
    rows = []

    def add(exp, paper, orig, aud, repro, issue, notes):
        numeric = (isinstance(paper, (int, float)) and isinstance(aud, (int, float)))
        diff = (aud - paper) if numeric else ""
        rd = ((aud - paper) / paper) if (numeric and paper) else ""
        rows.append({"experiment": exp, "paper_value": paper,
                     "original_reproduction": orig, "audited_value": aud,
                     "difference": diff, "relative_difference": rd,
                     "reproducible": repro, "methodology_issue": issue, "notes": notes})

    # --- synthetic single-seed 42 (committed results/evaluation.csv) ---
    add("Synthetic RE Precision (seed 42, committed)", 0.8125, 0.8125, 0.7146, "yes",
        "none", "single-seed committed value repro at its own protocol; seed-42 corrected RE precision=0.7146")
    add("Synthetic RE Recall (seed 42, committed)", 0.65, 0.65, 0.9329, "yes",
        "none", "seed-42 corrected")
    add("Synthetic RE F1 (seed 42, committed)", 0.7222222222222222, 0.7222222222222222, 0.8485, "yes",
        "none", "seed-42 corrected (different GT definition: detectable vs all)")
    # --- multi-seed ---
    re_f1 = [r["rule_engine"]["f1"] for r in recs]
    add("Synthetic RE multi-seed F1 mean (committed as 0.7222+-0.0)", 0.7222,
        0.7921, summ(re_f1)["mean"], "no",
        "committed '10-seed' stat is a single seed with std 0",
        f"reproduced committed protocol mean=0.7921; corrected protocol mean={summ(re_f1)['mean']:.4f}")
    gs_f1 = [r["graphsage"]["f1"] for r in recs]
    add("Synthetic GraphSAGE F1 (committed 0.5600)", 0.5600, 0.5600, summ(gs_f1)["mean"], "no",
        "committed value from train-on-test + threshold-on-test protocol",
        f"leakage-free protocol mean={summ(gs_f1)['mean']:.4f}")
    # --- mimicry RE ---
    for strength in ["none", "light", "medium", "heavy"]:
        d = [r["mimicry"][strength] for r in recs if strength in r.get("mimicry", {})]
        f1 = summ([x["rule_engine"].get("f1") for x in d])
        add(f"Mimicry {strength} RE F1 (committed)", None, None, f1["mean"], "no",
            "committed values drop with noise because camouflage injected invariant-violating edges",
            f"corrected benign camouflage: mean={f1['mean']:.4f} std={f1['std']:.4f}")
    # --- Rule Engine ROC-AUC ---
    re_roc = summ([r["rule_engine"]["roc_auc"] for r in recs])
    add("Rule Engine ROC-AUC under mimicry (paper 1.0000)", 1.0, 1.0, re_roc["mean"], "no",
        "committed 1.0 is a hard-coded fallback, not a computed AUC",
        f"independently computed continuous-score ROC-AUC mean={re_roc['mean']:.4f} "
        f"std={re_roc['std']:.4f} (range {re_roc['min']:.4f}-{re_roc['max']:.4f})")
    # --- DARPA ---
    if darpa:
        for r in darpa:
            add(f"DARPA {r['dataset']} {r['eval_type']} F1", None, None,
                r.get("f1_mean", ""), "no",
                "committed DARPA tables derive from synthetic fallback when data absent",
                f"real Theia edges={r.get('edges')} truncated={r.get('truncated')}; "
                f"synthetic post-collection poisoning only")
    # --- stats ---
    for s in stats:
        add(f"Paired RE-GS {s['metric']} difference", None, None, s["mean_diff"], "n/a",
            "no paper paired test reported", f"Wilcoxon p={s['wilcoxon_p']}")
    fields = ["experiment", "paper_value", "original_reproduction", "audited_value",
              "difference", "relative_difference", "reproducible", "methodology_issue", "notes"]
    write_csv(ROOT / "final_result_reconciliation.csv", rows, fields)
    return rows


if __name__ == "__main__":
    recs = synthetic_tables()
    mimic = mimicry_tables(recs)
    abl = ablation_tables()
    darpa = darpa_tables()
    scal = scalability_tables()
    gen = generalization_tables()
    stats = stats_table(recs)
    dataset_table()
    try:
        plots(recs)
    except Exception as e:
        print("plot error", e)
    recon = reconciliation(recs, mimic, abl, darpa, scal, stats)
    print("reconciliation rows:", len(recon))
    print("tables written to", TAB)
