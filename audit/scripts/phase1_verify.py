"""
Phase 1 verification engine.

Recomputes every reported quantity directly from the raw artifacts in
audit/raw_runs/ and writes a full-precision machine-readable summary. Nothing is
typed by hand; nothing is copied from an earlier report. Aggregation uses the
project's own definitions (sample std ddof=1, t-based 95% CI, paired t CI,
Wilcoxon signed-rank, Cohen's dz).

Outputs:
  audit/FINAL_RESEARCH_REPORT/verified_numbers.json   (full precision)
  audit/FINAL_RESEARCH_REPORT/verified_numbers.csv    (full precision)
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

RR = Path("audit/raw_runs")
OUT = Path("audit/FINAL_RESEARCH_REPORT")
OUT.mkdir(parents=True, exist_ok=True)

METRICS = ["precision", "recall", "f1", "accuracy", "balanced_accuracy", "mcc",
           "fpr", "fnr", "specificity", "roc_auc", "pr_auc"]
SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]


def summ(vals):
    arr = np.asarray([v for v in vals if v is not None], dtype=float)
    n = len(arr)
    if n == 0:
        return dict(n=0)
    m = float(np.mean(arr))
    if n == 1:
        return dict(n=1, mean=m, std=0.0, median=m, min=m, max=m,
                    ci95_low=None, ci95_high=None)
    s = float(np.std(arr, ddof=1))
    se = s / math.sqrt(n)
    tc = float(stats.t.ppf(0.975, df=n - 1))
    return dict(n=n, mean=m, std=s, median=float(np.median(arr)),
                min=float(np.min(arr)), max=float(np.max(arr)),
                ci95_low=m - tc * se, ci95_high=m + tc * se)


def paired(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); d = a - b; n = len(d)
    out = {"n": n, "mean_diff": float(np.mean(d)), "median_diff": float(np.median(d))}
    if n >= 2:
        sd = float(np.std(d, ddof=1)); se = sd / math.sqrt(n)
        tc = float(stats.t.ppf(0.975, df=n - 1))
        out["std_diff"] = sd
        out["ci95_low"] = float(np.mean(d) - tc * se)
        out["ci95_high"] = float(np.mean(d) + tc * se)
        out["cohens_dz"] = float(np.mean(d) / sd) if sd > 0 else 0.0
        stat, p = stats.wilcoxon(a, b, zero_method="wilcox")
        out["wilcoxon_stat"] = float(stat); out["wilcoxon_p"] = float(p)
    return out


def load_glob(pattern):
    return [json.load(open(p)) for p in sorted(Path(".").glob(pattern))]


V = {}   # verified numbers, nested
SRC = {}  # claim -> raw source path(s)


def rec(section, key, value, source):
    V.setdefault(section, {})[key] = value
    SRC[f"{section}.{key}"] = source


def main():
    # ---------------------------------------------------------------- synthetic
    syn = load_glob("audit/raw_runs/synthetic/seed_*.json")
    assert len(syn) == 10, len(syn)
    rec("synthetic", "n_seeds", len(syn), "raw_runs/synthetic/seed_*.json")
    for model, key in [("rule_engine", "RuleEngine"), ("graphsage", "GraphSAGE")]:
        for m in METRICS:
            vals = [r[model][m] for r in syn if m in r[model]]
            rec("synthetic", f"{key}.{m}", summ(vals),
                f"raw_runs/synthetic/seed_*.json::[{model}][{m}]")
    rec("synthetic", "RE_f1_per_seed",
        [r["rule_engine"]["f1"] for r in syn], "raw_runs/synthetic/seed_*.json")
    rec("synthetic", "GS_f1_per_seed",
        [r["graphsage"]["f1"] for r in syn], "raw_runs/synthetic/seed_*.json")
    # paired
    rec("synthetic", "paired_f1", paired([r["rule_engine"]["f1"] for r in syn],
                                         [r["graphsage"]["f1"] for r in syn]),
        "raw_runs/synthetic/seed_*.json")
    rec("synthetic", "paired_roc_auc",
        paired([r["rule_engine"]["roc_auc"] for r in syn],
               [r["graphsage"]["roc_auc"] for r in syn]),
        "raw_runs/synthetic/seed_*.json")
    # graph sizes / poisoning per seed
    rec("synthetic", "clean_nodes", summ([r["clean_nodes"] for r in syn]), "raw")
    rec("synthetic", "clean_edges", summ([r["clean_edges"] for r in syn]), "raw")
    rec("synthetic", "poisoned_edges", summ([r["poisoned_edges"] for r in syn]), "raw")
    rec("synthetic", "ground_truth_positives", summ([r["ground_truth_positives"] for r in syn]), "raw")
    rec("synthetic", "detectable_positives", summ([r["detectable_positives"] for r in syn]), "raw")
    rec("synthetic", "events_per_seed", summ([len(r["events"]) for r in syn]), "raw")
    rec("synthetic", "RE_clean_flagged_edges",
        summ([r["rule_engine_clean_fp"]["flagged_edges"] for r in syn]), "raw")
    rec("synthetic", "RE_clean_fpr",
        summ([r["rule_engine_clean_fp"]["fpr"] for r in syn]), "raw")

    # ------------------------------------------------------------------ mimicry
    mim = {}
    for strength in ["none", "light", "medium", "heavy"]:
        for model, key in [("rule_engine", "RuleEngine"), ("graphsage", "GraphSAGE")]:
            vals = [r["mimicry"][strength][model] for r in syn]
            for m in ["precision", "recall", "f1", "roc_auc", "pr_auc"]:
                rec("mimicry", f"{strength}.{key}.{m}", summ([v[m] for v in vals]),
                    f"raw_runs/synthetic/seed_*.json::mimicry.{strength}.{model}.{m}")
        base = [r["mimicry"][strength]["base_edges"] for r in syn]
        noise = [r["mimicry"][strength]["noise_edges"] for r in syn]
        final = [r["mimicry"][strength]["final_edges"] for r in syn]
        rec("mimicry", f"{strength}.base_edges", summ(base), "raw")
        rec("mimicry", f"{strength}.noise_edges", summ(noise), "raw")
        rec("mimicry", f"{strength}.final_edges", summ(final), "raw")
        nsv = [sum(r["mimicry"][strength]["noise_self_violations"].values())
               if isinstance(r["mimicry"][strength]["noise_self_violations"], dict)
               else 0 for r in syn]
        rec("mimicry", f"{strength}.noise_self_violations", summ(nsv), "raw")

    # ----------------------------------------------------------------- ablation
    # Authoritative source: audit/raw_runs/ablation/seed_*.json (corrected
    # harness: continuous severity-weighted score, corrected ground truth).
    # NOTE: audit/raw_runs/ablation_multiseed.json is the repo's own ablation
    # (different rule grouping) and DISAGREES; it is recorded separately as a
    # documented discrepancy and is NOT used in the manuscripts.
    abl_recs = load_glob("audit/raw_runs/ablation/seed_*.json")
    rec("ablation", "source_authoritative", "raw_runs/ablation/seed_*.json",
        "audit/experiments/ablation/run_ablation.py")
    rec("ablation", "n_seeds", len(abl_recs), "raw_runs/ablation/seed_*.json")
    rec("ablation", "seeds",
        sorted(r["seed"] for r in abl_recs), "raw_runs/ablation/seed_*.json")
    variants = sorted(abl_recs[0]["variants"].keys())
    for v in variants:
        for m in ["precision", "recall", "f1", "accuracy", "balanced_accuracy",
                  "mcc", "roc_auc", "pr_auc"]:
            vals = [r["variants"][v]["metrics"][m] for r in abl_recs
                    if v in r["variants"] and m in r["variants"][v]["metrics"]]
            if vals:
                rec("ablation", f"{v}.{m}", summ(vals),
                    f"raw_runs/ablation/seed_*.json::variants[{v}].metrics[{m}]")
    # repo-protocol ablation for discrepancy documentation
    repo_abl = json.load(open(RR / "ablation_multiseed.json"))
    for variant, agg in repo_abl["aggregate"].items():
        f1 = agg.get("f1", {})
        if isinstance(f1, dict):
            rec("ablation_repo_protocol", variant, f1,
                "raw_runs/ablation_multiseed.json::aggregate (repo protocol; NOT used)")

    # ----------------------------------------------------------- generalization
    gen_rows = []
    for p in sorted((RR / "generalization").glob("*.json")):
        g = json.load(open(p))
        gen_rows.append(g)
    for src, tgt in [("synthetic", "theia3"), ("theia3", "theia5m"), ("theia5m", "theia3")]:
        subset = [g for g in gen_rows if g["source"] == src and g["target"] == tgt]
        if not subset:
            continue
        rec("generalization", f"{src}->{tgt}.n", len(subset), "raw_runs/generalization/*.json")
        for m in ["precision", "recall", "f1", "roc_auc", "pr_auc"]:
            rec("generalization", f"{src}->{tgt}.RE.{m}",
                summ([g["rule_engine_target"][m] for g in subset]),
                f"raw_runs/generalization/{src}__{tgt}__*.json")
            rec("generalization", f"{src}->{tgt}.GS.{m}",
                summ([g["graphsage_target_own_model"][m] for g in subset]),
                f"raw_runs/generalization/{src}__{tgt}__*.json")

    # --------------------------------------------------------------- real Theia
    for scen in ["theia3", "theia5m"]:
        d = json.load(open(RR / "darpa" / f"{scen}_50000.json"))
        rec("real_theia", f"{scen}.source_csv", d["source_csv"], f"raw_runs/darpa/{scen}_50000.json")
        rec("real_theia", f"{scen}.provenance", d["provenance"], "raw")
        rec("real_theia", f"{scen}.truncated", d["truncated"], "raw")
        rec("real_theia", f"{scen}.n_edges_loaded", d["n_edges_loaded"], "raw")
        rec("real_theia", f"{scen}.n_nodes_loaded", d["n_nodes_loaded"], "raw")
        rec("real_theia", f"{scen}.graph_nodes", d["graph_nodes"], "raw")
        rec("real_theia", f"{scen}.graph_edges", d["graph_edges"], "raw")
        rdb = d["real_data_rule_behaviour"]
        rec("real_theia", f"{scen}.flagged_edges", rdb["flagged_edges"], "raw")
        rec("real_theia", f"{scen}.flag_rate", rdb["flag_rate"], "raw")
        rec("real_theia", f"{scen}.per_rule_counts", rdb["per_rule_counts"], "raw")
        sp = d["synthetic_post_collection_poisoning"]
        for model, key in [("rule_engine", "RuleEngine"), ("graphsage", "GraphSAGE")]:
            for m in ["precision", "recall", "f1", "roc_auc", "pr_auc"]:
                rec("real_theia", f"{scen}.{key}.{m}",
                    summ([r[model][m] for r in sp]), f"raw_runs/darpa/{scen}_50000.json::sp")
        rec("real_theia", f"{scen}.requested_ops", summ([r["requested_ops"] for r in sp]), "raw")
        rec("real_theia", f"{scen}.ground_truth_positives", summ([r["ground_truth_positives"] for r in sp]), "raw")
        rec("real_theia", f"{scen}.detectable_positives", summ([r["detectable_positives"] for r in sp]), "raw")
        rec("real_theia", f"{scen}.integrity_problems", sum(len(r["integrity_problems"]) for r in sp), "raw")

    # -------------------------------------------------------------- scalability
    scal = {}
    for p in (RR / "scalability").glob("size_*_rep_*.json"):
        s = json.load(open(p))
        scal.setdefault(s["target_edges"], []).append(s)
    for size in sorted(scal):
        reps = scal[size]
        rec("scalability", f"{size}.n_reps", len(reps), "raw_runs/scalability/*.json")
        for m in ["construction_sec", "poisoning_sec", "rule_engine_infer_sec",
                  "evaluation_sec", "end_to_end_sec", "peak_python_mb",
                  "rss_delta_mb", "rule_engine_throughput_eps", "nodes", "edges"]:
            rec("scalability", f"{size}.{m}", summ([r[m] for r in reps]),
                f"raw_runs/scalability/size_{size}_rep_*.json")

    # ------------------------------------------------------------------ leakage
    d = json.load(open(RR / "corrected_multiseed.json"))
    leaky = d["original_leaky"]
    clean = d["per_seed"]
    rec("leakage", "protocol_clean", d["protocol"], "raw_runs/corrected_multiseed.json")
    rec("leakage", "epochs", d["epochs"], "raw")
    rec("leakage", "lr", d["lr"], "raw")
    rec("leakage", "hidden", d["hidden"], "raw")
    for m in ["precision", "recall", "f1", "roc_auc", "pr_auc", "mcc"]:
        rec("leakage", f"leaky_GS.{m}", summ([x[m] for x in leaky]),
            "raw_runs/corrected_multiseed.json::original_leaky")
        rec("leakage", f"clean_GS.{m}", summ([x["graphsage_clean"][m] for x in clean]),
            "raw_runs/corrected_multiseed.json::per_seed[].graphsage_clean")
        rec("leakage", f"clean_RE.{m}", summ([x["rule_engine"][m] for x in clean]),
            "raw_runs/corrected_multiseed.json::per_seed[].rule_engine")
    rec("leakage", "f1_inflation",
        float(np.mean([x["f1"] for x in leaky]) - np.mean([x["graphsage_clean"]["f1"] for x in clean])),
        "derived: leaky_GS.f1.mean - clean_GS.f1.mean")
    rec("leakage", "paired_stats", d["paired_stats"], "raw_runs/corrected_multiseed.json::paired_stats")

    # -------------------------------------------------- scoring-universe sensitivity
    gts = json.load(open(RR / "gt_sensitivity.json"))
    for k, st in gts["summary"].items():
        rec("scoring_universe", k, st, "raw_runs/gt_sensitivity.json::summary")
    rec("scoring_universe", "per_seed", gts["per_seed"], "raw_runs/gt_sensitivity.json::per_seed")

    # ------------------------------------------------------------- poisoning audit
    pa = json.load(open(RR / "poisoning_audit.json"))
    rec("poisoning", "intensity_per_type", pa["intensity_per_type"], "raw_runs/poisoning_audit.json")
    for atk, v in pa["attacks"].items():
        agg = {}
        for key in ["requested", "successful_events", "gt_positive_count",
                    "unique_gt_ids", "duplicate_gt_ids", "duplicate_final_edge_ids"]:
            vals = [p.get(key, 0) for p in v["per_seed"]]
            agg[key] = summ(vals)
        absent = [len(p.get("gt_ids_absent_from_final_graph", [])) for p in v["per_seed"]]
        agg["gt_ids_absent_from_final_graph"] = summ(absent)
        rec("poisoning", atk, agg, "raw_runs/poisoning_audit.json::attacks")

    # --------------------------------------------------------------- mimicry audit
    ma = json.load(open(RR / "mimicry_audit.json"))
    for strength, v in ma["strengths"].items():
        agg = {}
        for key in ["base_edges", "noise_edges", "final_edges",
                    "mimicry_edges_flagged_by_rules", "mimicry_edges_benign_count",
                    "mimicry_edges_with_leaky_attributes", "detector_positives",
                    "gt_positives", "tp", "fp", "fn", "precision", "recall", "f1"]:
            vals = [p.get(key, 0) for p in v["per_seed"]]
            agg[key] = summ(vals)
        rec("mimicry_audit", strength, agg, "raw_runs/mimicry_audit.json::strengths")

    # -------------------------------------------------------- rule score audit
    if (RR / "rule_score_audit.json").exists():
        rs = json.load(open(RR / "rule_score_audit.json"))
        rec("rule_score", "metric_result_has_roc_auc_field",
            rs["metric_result_has_roc_auc_field"], "raw_runs/rule_score_audit.json")
        rec("rule_score", "robustness_roc_default", rs["robustness_roc_default"],
            "raw_runs/rule_score_audit.json")
        for strength, rows in rs["results"].items():
            if not rows:
                continue
            for key in ["roc_auc_count_score", "pr_auc_count_score",
                        "roc_auc_binary_flag", "paper_reported_roc_auc",
                        "edges_flagged", "edges", "gt_positives"]:
                vals = [r[key] for r in rows if key in r]
                if vals:
                    rec("rule_score", f"{strength}.{key}", summ(vals),
                        f"raw_runs/rule_score_audit.json::results[{strength}][{key}]")

    # ------------------------------------------------- per-rule statistics (synthetic)
    per_rule = {}
    for r in syn:
        for rule, cnt in r["rule_engine"]["per_rule_counts"].items():
            per_rule.setdefault(rule, []).append(cnt)
    for rule, counts in per_rule.items():
        rec("rule_statistics", f"{rule}.violations", summ(counts),
            "raw_runs/synthetic/seed_*.json::rule_engine.per_rule_counts")

    # ------------------------------------------------------------------- write
    with open(OUT / "verified_numbers.json", "w") as fh:
        json.dump(V, fh, indent=2, default=str)

    rows = []
    def walk(prefix, obj):
        if isinstance(obj, dict) and "mean" in obj and "n" in obj:
            rows.append({"claim": prefix, "n": obj.get("n"), "mean": obj.get("mean"),
                         "std": obj.get("std"), "median": obj.get("median"),
                         "min": obj.get("min"), "max": obj.get("max"),
                         "ci95_low": obj.get("ci95_low"), "ci95_high": obj.get("ci95_high"),
                         "source": SRC.get(prefix, "")})
        elif isinstance(obj, dict):
            for k, v in obj.items():
                walk(f"{prefix}.{k}" if prefix else k, v)
    walk("", V)
    with open(OUT / "verified_numbers.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["claim", "n", "mean", "std", "median",
                                           "min", "max", "ci95_low", "ci95_high", "source"])
        w.writeheader(); w.writerows(rows)

    print(f"verified claims written: {len(rows)}")
    print(f"sections: {list(V.keys())}")


if __name__ == "__main__":
    main()
