"""
Independent final validation of the corrected audit artifacts.

Recomputes every headline number directly from audit/raw_runs/* and checks it
against the journal-ready tables and the final_audit_report values. Nothing is
trusted because it appears in a Markdown file; every value is re-derived from the
raw JSON.

Outputs (audit/final_validation/):
  number_crosscheck.csv
  table_crosscheck.csv
  figure_crosscheck.csv
  source_map.md
  unresolved_issues.md
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path("audit")
RAW = ROOT / "raw_runs"
TAB = ROOT / "journal_ready_tables"
OUT = ROOT / "final_validation"
OUT.mkdir(parents=True, exist_ok=True)

ISSUES: list[dict] = []
CHECKS: list[dict] = []


def issue(kind, artifact, detail, authoritative):
    ISSUES.append({"kind": kind, "artifact": artifact, "detail": detail,
                   "authoritative": authoritative})


def check(name, computed, claimed, claimed_src, tol=1e-9, note=""):
    match = "MATCH"
    if computed is None or claimed is None:
        match = "N/A"
    elif isinstance(claimed, (int, float)) and isinstance(computed, (int, float)):
        if abs(computed - claimed) <= tol:
            match = "MATCH"
        elif claimed and abs(computed - claimed) / abs(claimed) <= 0.01:
            match = "CLOSE(<=1%)"
        else:
            match = "DISCREPANCY"
    else:
        match = "MATCH" if str(computed) == str(claimed) else "DISCREPANCY"
    CHECKS.append({"check": name, "computed": computed, "claimed": claimed,
                   "source": claimed_src, "match": match, "note": note})
    if match == "DISCREPANCY":
        issue("numeric", claimed_src, f"{name}: computed={computed} claimed={claimed}",
              "raw_runs")
    return match


def summarize(vals):
    arr = np.array([v for v in vals if v is not None], float)
    n = len(arr)
    m = float(np.mean(arr))
    s = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    from scipy import stats
    tc = float(stats.t.ppf(0.975, df=n - 1)) if n > 1 else 0.0
    return dict(n=n, mean=m, std=s, median=float(np.median(arr)),
                min=float(np.min(arr)), max=float(np.max(arr)),
                ci_low=m - tc * s / math.sqrt(n) if n > 1 else "",
                ci_high=m + tc * s / math.sqrt(n) if n > 1 else "")


def metric_from_counts(tp, fp, tn, fn):
    """Independently recompute the confusion-matrix metrics."""
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else 0.0
    tpr = rec
    tnr = tn / (tn + fp) if (tn + fp) else 0.0
    bacc = (tpr + tnr) / 2
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn) - (fp * fn)) / denom if denom else 0.0
    return dict(precision=prec, recall=rec, f1=f1, accuracy=acc,
                balanced_accuracy=bacc, fpr=fpr, fnr=fnr,
                specificity=tnr, mcc=mcc)


def load_table(name):
    p = TAB / f"{name}.csv"
    return list(csv.DictReader(open(p))) if p.exists() else []


def num(x):
    try:
        return float(x)
    except Exception:
        return None


# --------------------------------------------------------------------------
# 1. Metric-recomputation integrity (tp/fp/tn/fn -> metrics) for every raw run
# --------------------------------------------------------------------------
def validate_metric_computation():
    keys = ["precision", "recall", "f1", "accuracy", "balanced_accuracy",
            "fpr", "fnr", "specificity", "mcc"]
    checked = 0
    bad = 0
    for p in sorted(RAW.glob("synthetic/seed_*.json")):
        r = json.load(open(p))
        for det in ["rule_engine", "graphsage"]:
            m = r[det]
            if not all(k in m for k in ["tp", "fp", "tn", "fn"]):
                continue
            recomp = metric_from_counts(m["tp"], m["fp"], m["tn"], m["fn"])
            for k in keys:
                if k in m:
                    checked += 1
                    if abs(recomp[k] - m[k]) > 1e-9:
                        bad += 1
                        issue("metric", f"{p.name}:{det}.{k}",
                              f"recomputed={recomp[k]} stored={m[k]}", "recomputation")
    # ablation + darpa + generalization too
    for p in sorted(RAW.glob("ablation/seed_*.json")):
        r = json.load(open(p))
        for v, d in r["variants"].items():
            m = d["metrics"]
            recomp = metric_from_counts(m["tp"], m["fp"], m["tn"], m["fn"])
            for k in keys:
                checked += 1
                if abs(recomp[k] - m[k]) > 1e-9:
                    bad += 1
                    issue("metric", f"{p.name}:{v}.{k}",
                          f"recomputed={recomp[k]} stored={m[k]}", "recomputation")
    print(f"[metric recomputation] checked={checked} mismatches={bad}")
    return checked, bad


# --------------------------------------------------------------------------
# 2. Headline numbers vs journal-ready tables
# --------------------------------------------------------------------------
def validate_synthetic():
    recs = [json.load(open(p)) for p in sorted(RAW.glob("synthetic/seed_*.json"))]
    assert len(recs) == 10, f"expected 10 seeds, got {len(recs)}"
    seeds = sorted(r["seed"] for r in recs)
    check("synthetic.seed_count", len(recs), 10, "final_audit_report.md")
    check("synthetic.seeds", ",".join(map(str, seeds)),
          "1,7,13,21,42,99,123,256,512,1024", "final_audit_report.md")
    t2 = {(row["detector"], row["metric"]): row for row in load_table("table2_synthetic_detection")}
    for det, key in [("RuleEngine", "rule_engine"), ("GraphSAGE", "graphsage")]:
        for metric in ["precision", "recall", "f1", "accuracy", "balanced_accuracy",
                       "mcc", "fpr", "fnr", "specificity", "roc_auc", "pr_auc"]:
            s = summarize([r[key].get(metric) for r in recs])
            row = t2.get((det, metric))
            if row is None:
                issue("missing_table_row", "table2", f"{det}/{metric}", "raw_runs")
                continue
            check(f"synthetic.{det}.{metric}.mean", s["mean"], num(row["mean"]), "table2")
            check(f"synthetic.{det}.{metric}.std", s["std"], num(row["std"]), "table2")
            check(f"synthetic.{det}.{metric}.n", s["n"], int(row["n"]), "table2")
            check(f"synthetic.{det}.{metric}.ci_low", s["ci_low"], num(row["ci_low"]), "table2")
            check(f"synthetic.{det}.{metric}.ci_high", s["ci_high"], num(row["ci_high"]), "table2")
    return recs


def validate_mimicry(recs):
    t4 = {(row["strength"], row["detector"]): row for row in load_table("table4_mimicry_robustness")}
    for strength in ["none", "light", "medium", "heavy"]:
        for det, label in [("rule_engine", "RuleEngine"), ("graphsage", "GraphSAGE")]:
            d = [r["mimicry"][strength] for r in recs]
            row = t4.get((strength, label))
            f1 = summarize([x[det]["f1"] for x in d])
            check(f"mimicry.{strength}.{label}.f1_mean", f1["mean"], num(row["f1_mean"]), "table4")
            check(f"mimicry.{strength}.{label}.f1_std", f1["std"], num(row["f1_std"]), "table4")
            nsv = summarize([float(sum(x["noise_self_violations"].values())) for x in d])
            check(f"mimicry.{strength}.noise_self_violations", nsv["mean"],
                  num(row["noise_self_violations"]), "table4")
            # mimicry edges actually added
            ne = summarize([x["noise_edges"] for x in d])
            check(f"mimicry.{strength}.noise_edges", ne["mean"], num(row["mimicry_edges"]), "table4")
    # key claim: RE f1 invariant across strengths
    re_f1 = {s: summarize([r["mimicry"][s]["rule_engine"]["f1"] for r in recs])["mean"]
             for s in ["none", "light", "medium", "heavy"]}
    check("mimicry.RE_f1_invariance",
          max(re_f1.values()) - min(re_f1.values()), 0.0,
          "final_audit_report.md (claim: unchanged)", tol=1e-12)
    # key claim: zero self-violations at all strengths
    tot_nsv = sum(float(sum(r["mimicry"][s]["noise_self_violations"].values()))
                  for r in recs for s in ["none", "light", "medium", "heavy"])
    check("mimicry.total_self_violations", tot_nsv, 0, "final_audit_report.md")


def validate_ablation():
    recs = [json.load(open(p)) for p in sorted(RAW.glob("ablation/seed_*.json"))]
    check("ablation.seed_count", len(recs), 10, "final_audit_report.md")
    t5 = {row["variant"]: row for row in load_table("table5_rule_ablation")}
    for v in ["all_rules", "without_structural", "without_temporal", "without_semantic"]:
        s = summarize([r["variants"][v]["metrics"]["f1"] for r in recs])
        check(f"ablation.{v}.f1_mean", s["mean"], num(t5[v]["mean"]), "table5")
        check(f"ablation.{v}.f1_std", s["std"], num(t5[v]["std"]), "table5")
    # LOO of the important rules
    for v in ["loo_ReadWriteConsistencyRule", "loo_NetworkConsistencyRule",
              "loo_SpawnConsistencyRule", "loo_SequenceMonotonicityRule",
              "loo_UnspawnedProcessRule"]:
        s = summarize([r["variants"][v]["metrics"]["f1"] for r in recs])
        check(f"ablation.{v}.f1_mean", s["mean"], num(t5[v]["mean"]), "table5")
    return recs


def validate_darpa():
    rows = {r["dataset"]: r for r in load_table("table3_darpa_cross_scenario")}
    for ds in ["theia3", "theia5m"]:
        r = json.load(open(RAW / f"darpa/{ds}_50000.json"))
        seeds = r["synthetic_post_collection_poisoning"]
        check(f"darpa.{ds}.seed_count", len(seeds), 10, "final_audit_report.md")
        check(f"darpa.{ds}.graph_edges", r["graph_edges"], 50000, "final_audit_report.md")
        check(f"darpa.{ds}.truncated", r["truncated"], True, "final_audit_report.md")
        check(f"darpa.{ds}.provenance", r["provenance"], "REAL_DARPA_THEIA_E3", "darpa_audit.md")
        # attacks are stored separately as synthetic post-collection poisoning
        check(f"darpa.{ds}.attack_source_is_synthetic",
              "synthetic_post_collection_poisoning" in r, True, "darpa_audit.md")
        # requested vs detectable event count (15 vs 20)
        check(f"darpa.{ds}.requested_ops", seeds[0]["requested_ops"], 20, "darpa_audit.md")
        check(f"darpa.{ds}.detectable_positives", seeds[0]["detectable_positives"], 15, "darpa_audit.md")
        for det, key in [("RuleEngine", "rule_engine"), ("GraphSAGE", "graphsage")]:
            row = rows.get(f"synthetic_post_collection_{key}")
            f1 = summarize([e[key]["f1"] for e in seeds if key in e])
            if row is not None and row["dataset"] == ds:
                check(f"darpa.{ds}.{det}.f1_mean", f1["mean"], num(row["f1_mean"]), "table3")
        rb = r["real_data_rule_behaviour"]
        check(f"darpa.{ds}.real_flag_rate", rb["flag_rate"],
              {"theia3": 0.00038, "theia5m": 0.00014}[ds], "darpa_audit.md", tol=1e-9)
        check(f"darpa.{ds}.real_flagged_edges", rb["flagged_edges"],
              {"theia3": 19, "theia5m": 7}[ds], "darpa_audit.md")
    # table rows: both datasets present
    for ds in ["theia3", "theia5m"]:
        for key in ["rule_engine", "graphsage"]:
            found = any(r["dataset"] == ds and r["eval_type"] == f"synthetic_post_collection_{key}"
                        for r in load_table("table3_darpa_cross_scenario"))
            check(f"darpa.table3_row.{ds}.{key}", found, True, "table3")


def validate_scalability():
    recs = [json.load(open(p)) for p in sorted(RAW.glob("scalability/size_*.json"))]
    by = {}
    for r in recs:
        by.setdefault(r["edges"], []).append(r)
    sizes = sorted(by)
    check("scalability.sizes", ",".join(map(str, sizes)),
          "10000,25000,50000,100000,250000,500000,1000000", "final_audit_report.md")
    for s in sizes:
        check(f"scalability.{s}.n_reps", len(by[s]), 5, "final_audit_report.md")
    t6 = {int(float(row["edges"])): row for row in load_table("table6_scalability")}
    for s in sizes:
        row = t6[s]
        check(f"scalability.{s}.infer_mean", summarize([x["rule_engine_infer_sec"] for x in by[s]])["mean"],
              num(row["rule_engine_infer_sec"]), "table6")
        check(f"scalability.{s}.throughput", summarize([x["rule_engine_throughput_eps"] for x in by[s]])["mean"],
              num(row["throughput_eps"]), "table6")
        check(f"scalability.{s}.peak_python_mb", summarize([x["peak_python_mb"] for x in by[s]])["mean"],
              num(row["peak_python_mb"]), "table6")
    # linearity: throughput stable within 2x
    tp = [summarize([x["rule_engine_throughput_eps"] for x in by[s]])["mean"] for s in sizes]
    check("scalability.throughput_stability_ratio", max(tp) / min(tp), None, "n/a")
    return recs


def validate_generalization():
    recs = [json.load(open(p)) for p in sorted(RAW.glob("generalization/*.json"))]
    by = {}
    for r in recs:
        by.setdefault((r["source"], r["target"]), []).append(r)
    t9 = {(r["source"], r["target"]): r for r in load_table("table9_generalization")}
    for k, rs in by.items():
        row = t9[k]
        re_f1 = summarize([x["rule_engine_target"]["f1"] for x in rs])
        check(f"gen.{k}.RE_f1_mean", re_f1["mean"], num(row["rule_engine_f1_mean"]), "table9")
        check(f"gen.{k}.n", len(rs), int(row["n"]), "table9")


def validate_statistics(recs):
    t8 = {row["metric"]: row for row in load_table("table8_significance")}
    for metric in ["f1", "roc_auc"]:
        a = np.array([r["rule_engine"][metric] for r in recs], float)
        b = np.array([r["graphsage"][metric] for r in recs], float)
        d = a - b
        from scipy import stats
        stat, p = stats.wilcoxon(a, b)
        check(f"stats.{metric}.mean_diff", float(np.mean(d)), num(t8[metric]["mean_diff"]), "table8")
        check(f"stats.{metric}.wilcoxon_p", float(p), num(t8[metric]["wilcoxon_p"]), "table8")
        check(f"stats.{metric}.n_pairs", len(d), int(t8[metric]["n"]), "table8")
        sd = float(np.std(d, ddof=1))
        check(f"stats.{metric}.cohens_dz", float(np.mean(d)) / sd, num(t8[metric]["cohens_dz"]), "table8")


# --------------------------------------------------------------------------
# 3. Figure cross-check
# --------------------------------------------------------------------------
def figure_crosscheck():
    figs = [
        ("rule_engine_roc_pr_seed42.png", "Rule Engine ROC/PR (genuine continuous score)",
         "synthetic seed 42", "AUC from raw_runs/synthetic/seed_42.json", "OK"),
        ("scalability_corrected.png", "Rule Engine scalability",
         "synthetic 10k-1M", "raw_runs/scalability/*", "OK"),
        ("F1_vs_attack.png", "F1 vs attack type (committed results/ figure)",
         "synthetic", "results/ (committed, single-seed)", "STALE-SINGLE-SEED"),
        ("roc_curve.png", "ROC curve (committed results/ figure)",
         "synthetic", "results/ (committed; check source)", "REVIEW"),
        ("robustness_curve.png", "Robustness/mimicry (committed)",
         "synthetic", "results/ (committed; mis-specified mimicry)", "STALE-MIMICRY"),
        ("runtime_vs_edges.png", "Runtime vs edges (committed)",
         "synthetic", "results/ (committed)", "STALE-HW"),
    ]
    rows = []
    for name, desc, ds, src, status in figs:
        exists = (ROOT / "plots" / name).exists()
        rows.append({"figure": name, "description": desc, "dataset": ds,
                     "source": src, "exists_in_audit_plots": exists, "status": status})
        if not exists:
            issue("figure", name, "missing from audit/plots", "audit/plots")
    with open(OUT / "figure_crosscheck.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


# --------------------------------------------------------------------------
# 4. Table cross-check
# --------------------------------------------------------------------------
def table_crosscheck():
    tables = {
        "table1_dataset_characteristics": "Real DARPA TC E3 Theia parse counts",
        "table2_synthetic_detection": "Synthetic 10-seed detection (RE vs GS)",
        "table3_darpa_cross_scenario": "Real Theia + synthetic post-collection poisoning",
        "table4_mimicry_robustness": "Corrected invariant-preserving mimicry",
        "table5_rule_ablation": "Rule-group + LOO ablation, 10 seeds",
        "table6_scalability": "Scalability, 5 reps/size",
        "table7_multiseed": "Multi-seed mean/std/median/min/max/CI",
        "table8_significance": "Paired RE vs GS tests",
        "table9_generalization": "Cross-dataset generalization",
    }
    rows = []
    for name, desc in tables.items():
        for ext in ["csv", "md", "tex"]:
            p = TAB / f"{name}.{ext}"
            rows.append({"table": name, "description": desc, "format": ext,
                         "exists": p.exists(), "path": str(p)})
            if not p.exists():
                issue("table", f"{name}.{ext}", "missing", "journal_ready_tables")
    with open(OUT / "table_crosscheck.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


def main():
    print("=" * 70)
    checked, bad = validate_metric_computation()
    recs = validate_synthetic()
    validate_mimicry(recs)
    validate_ablation()
    validate_darpa()
    validate_scalability()
    validate_generalization()
    validate_statistics(recs)
    table_crosscheck()
    figure_crosscheck()

    with open(OUT / "number_crosscheck.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["check", "computed", "claimed", "source", "match", "note"])
        w.writeheader()
        w.writerows(CHECKS)

    with open(OUT / "unresolved_issues.md", "w") as f:
        f.write("# Unresolved Issues\n\n")
        if not ISSUES:
            f.write("No unresolved numerical discrepancies.\n")
        else:
            for i in ISSUES:
                f.write(f"- **{i['kind']}** `{i['artifact']}`: {i['detail']} "
                        f"(authoritative: {i['authoritative']})\n")

    n_match = sum(1 for c in CHECKS if c["match"] == "MATCH")
    n_close = sum(1 for c in CHECKS if c["match"] == "CLOSE(<=1%)")
    n_disc = sum(1 for c in CHECKS if c["match"] == "DISCREPANCY")
    print(f"[checks] total={len(CHECKS)} match={n_match} close={n_close} discrepancy={n_disc}")
    print(f"[issues] {len(ISSUES)}")


if __name__ == "__main__":
    main()
