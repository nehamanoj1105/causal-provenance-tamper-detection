"""
Generate the final manuscript tables (spec Part 5 numbering) from verified data.

Writes CSV, Markdown and LaTeX into audit/FINAL_RESULTS/tables/{csv,markdown,latex}.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path("audit")
FR = ROOT / "FINAL_RESULTS"
SRC = ROOT / "journal_ready_tables"
RAW = ROOT / "raw_runs"


def rows(name):
    return list(csv.DictReader(open(SRC / f"{name}.csv")))


def write_table(name, rows_, fields, caption, label):
    for sub, ext in [("csv", "csv"), ("markdown", "md"), ("latex", "tex")]:
        (FR / "tables" / sub).mkdir(parents=True, exist_ok=True)
    with open(FR / "tables" / "csv" / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows_)
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for r in rows_:
        lines.append("| " + " | ".join(str(r.get(k, "")) for k in fields) + " |")
    (FR / "tables" / "markdown" / f"{name}.md").write_text("\n".join(lines) + "\n")
    cols = "l" + "r" * (len(fields) - 1)
    tex = ["\\begin{table}[t]", "\\centering", f"\\caption{{{caption}}}",
           f"\\label{{{label}}}", f"\\begin{{tabular}}{{{cols}}}", "\\hline",
           " & ".join(f.replace("_", "\\_") for f in fields) + " \\\\", "\\hline"]
    for r in rows_:
        def c(v):
            try:
                return f"{float(v):.4f}"
            except Exception:
                return str(v)
        tex.append(" & ".join(c(r.get(k, "")) for k in fields) + " \\\\")
    tex += ["\\hline", "\\end{tabular}", "\\end{table}"]
    (FR / "tables" / "latex" / f"{name}.tex").write_text("\n".join(tex) + "\n")


def table1():
    r = rows("table1_dataset_characteristics")
    out = []
    for x in r:
        out.append({"dataset": x["source"], "nodes": x["nodes"], "edges": x["edges"],
                    "status": "obtained & parsed"})
    for name, exp in [("Theia E3 scenario 1r", "408,320 nodes / 9,295,127 edges"),
                      ("Theia E3 scenario 6r", "1,123,475 nodes / 18,206,475 edges")]:
        out.append({"dataset": name, "nodes": "unavailable", "edges": "unavailable",
                    "status": "not obtained (Drive quota); expected " + exp})
    write_table("table1_dataset_statistics", out,
                ["dataset", "nodes", "edges", "status"],
                "Provenance datasets used and their availability.", "tab:datasets")


def table2():
    cfg = [
        ["Synthetic main detection", "Synthetic (30 proc, 40 file, 10 net)",
         "5 del + 5 ins + 5 reord + 5 forgery", "10", "Rule Engine / GraphSAGE",
         "final-graph (10 detectable + 5 undetectable)"],
        ["Real Theia + poisoning", "Theia E3 3 / 5m, 50k-edge cap",
         "20 ops (15 detectable)", "10", "Rule Engine / GraphSAGE", "final-graph"],
        ["Mimicry robustness", "Synthetic", "5+5+5+5 poison + camouflage",
         "10", "Rule Engine / GraphSAGE", "final-graph"],
        ["Rule ablation", "Synthetic", "same as main", "10", "Rule Engine", "final-graph"],
        ["Generalization", "synthetic↔Theia", "soft graph only", "5",
         "Rule Engine / GraphSAGE", "final-graph"],
        ["Scalability", "Synthetic 10k–1M", "none", "5 reps", "Rule Engine", "n/a"],
    ]
    out = [{"experiment": a, "dataset": b, "attacks": c, "seeds": d,
            "detectors": e, "positive_universe": f} for a, b, c, d, e, f in cfg]
    write_table("table2_experimental_protocol", out,
                ["experiment", "dataset", "attacks", "seeds", "detectors", "positive_universe"],
                "Experimental protocol for every reported experiment.", "tab:protocol")


def table3():
    t2 = rows("table2_synthetic_detection")
    out = []
    for r in t2:
        out.append({"detector": r["detector"], "metric": r["metric"],
                    "mean": r["mean"], "std": r["std"],
                    "ci_low": r["ci_low"], "ci_high": r["ci_high"], "n": r["n"]})
    write_table("table3_main_detection", out,
                ["detector", "metric", "mean", "std", "ci_low", "ci_high", "n"],
                "Main detection on synthetic controlled poisoning, 10 seeds "
                "(mean, sample std, 95% CI).", "tab:main")


def table4():
    out = rows("table8_significance")
    write_table("table4_statistical_comparison", out,
                ["metric", "n", "mean_diff", "median_diff", "std_diff", "ci_low",
                 "ci_high", "cohens_dz", "wilcoxon_stat", "wilcoxon_p"],
                "Paired RuleEngine−GraphSAGE comparison over identical test "
                "instances (10 seeds).", "tab:significance")


def table5():
    out = rows("table9_generalization")
    write_table("table5_cross_dataset", out,
                ["source", "target", "n", "rule_engine_f1_mean", "rule_engine_f1_std",
                 "graphsage_own_model_f1_mean", "graphsage_own_model_f1_std"],
                "Cross-dataset generalization (5 seeds).", "tab:generalization")


def table6():
    out = rows("table4_mimicry_robustness")
    write_table("table6_mimicry", out,
                ["strength", "detector", "base_edges", "mimicry_edges", "final_edges",
                 "noise_self_violations", "precision_mean", "recall_mean", "f1_mean",
                 "f1_std", "roc_auc_mean", "pr_auc_mean"],
                "Robustness to invariant-preserving mimicry (10 seeds).", "tab:mimicry")


def table7():
    out = rows("table5_rule_ablation")
    write_table("table7_rule_ablation", out,
                ["variant", "n", "mean", "std", "median", "min", "max", "ci_low", "ci_high"],
                "Rule-group and leave-one-rule-out ablation (10 seeds).", "tab:ablation")


def table8():
    out = rows("table6_scalability")
    write_table("table8_scalability", out,
                ["edges", "n_reps", "construction_sec", "poisoning_sec",
                 "rule_engine_infer_sec", "rule_engine_infer_std", "end_to_end_sec",
                 "peak_python_mb", "rss_delta_mb", "throughput_eps"],
                "Scalability of graph construction, poisoning and Rule Engine "
                "inference (5 repetitions per size).", "tab:scalability")


def table9():
    out = rows("table3_darpa_cross_scenario")
    write_table("table9_real_data_poisoning", out,
                ["dataset", "eval_type", "edges", "truncated", "n", "f1_mean", "f1_std",
                 "precision_mean", "recall_mean", "roc_auc_mean"],
                "Real Theia provenance with synthetic post-collection poisoning "
                "(10 seeds). Not real attack labels.", "tab:realpoison")


def main():
    table1(); table2(); table3(); table4(); table5(); table6(); table7(); table8(); table9()
    print("manuscript tables written")


if __name__ == "__main__":
    main()
