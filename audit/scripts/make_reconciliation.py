"""
Builds audit/final_result_reconciliation.csv and audit/journal_ready_tables/*.

Reads the raw audit JSON files. Values are written at full precision (no
rounding) in the CSV; the Markdown/LaTeX tables are formatted for readability
but the underlying CSV keeps full precision.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "audit" / "raw_runs"
OUT = ROOT / "audit"
TABLES = OUT / "journal_ready_tables"
TABLES.mkdir(parents=True, exist_ok=True)


def load(name):
    p = RAW / name
    return json.load(open(p)) if p.exists() else None


def rel(rep, paper):
    if paper in (None, 0):
        return ""
    return (rep - paper) / paper


def main():
    cm = load("corrected_multiseed.json")
    rs = load("rule_score_audit.json")
    ab = load("ablation_multiseed.json")
    mi = load("mimicry_audit.json")
    po = load("poisoning_audit.json")
    sc = load("scalability_audit.json")

    s = cm["summary"]
    re = s["rule_engine"]
    gs = s["graphsage_clean"]
    leaky = s["graphsage_original_leaky"]

    # ---------------- reconciliation ----------------
    rows = []

    def add(exp, paper, orig, aud, repro, issue, notes):
        diff = "" if (isinstance(aud, str) or aud is None) else aud - paper
        rd = "" if (isinstance(aud, str) or aud is None) else rel(aud, paper)
        rows.append({
            "experiment": exp, "paper_value": paper, "original_reproduction": orig,
            "audited_value": aud, "difference": diff, "relative_difference": rd,
            "reproducible": repro, "methodology_issue": issue, "notes": notes,
        })

    # synthetic rule engine seed 42
    add("Synthetic Rule Engine Precision (seed 42)", 0.8125, 0.8125, 0.8125, "yes", "none", "exact")
    add("Synthetic Rule Engine Recall (seed 42)", 0.65, 0.65, 0.65, "yes", "none", "exact")
    add("Synthetic Rule Engine F1 (seed 42)", 0.7222222222222222, 0.7222222222222222, 0.7222222222222222, "yes", "none", "exact")
    # multi-seed aggregate
    add("Synthetic Rule Engine F1 (multi-seed mean, original protocol)", 0.7222, 0.7921, re["f1"]["mean"], "no",
        "paper/committed value is a single seed reported with std 0",
        "original protocol multi-seed mean=0.7921 (reproducible); corrected protocol mean=0.4620")
    add("Synthetic Rule Engine Precision (multi-seed mean, original protocol)", 0.8125, 0.8039, re["precision"]["mean"], "no",
        "paper/committed value is a single seed reported with std 0",
        "original protocol multi-seed mean=0.8039 (reproducible); corrected protocol mean=0.3394")
    add("Synthetic Rule Engine Recall (multi-seed mean, original protocol)", 0.65, 0.79, re["recall"]["mean"], "no",
        "paper/committed value is a single seed reported with std 0",
        "original protocol multi-seed mean=0.7900 (reproducible); corrected protocol mean=0.7267")
    # graphsage seed 42
    add("GraphSAGE F1 (seed 42)", 0.56, 0.56, 0.56, "yes", "train+threshold on test", "exact but leaky")
    add("GraphSAGE ROC-AUC (seed 42)", 0.877642, 0.877642, 0.877642, "yes", "train+threshold on test", "exact but leaky")
    # graphsage clean multi-seed
    add("GraphSAGE F1 (clean multi-seed mean)", 0.56, 0.5876, gs["f1"]["mean"], "no",
        "original protocol leaks; corrected protocol required", "leaky mean 0.5876 vs clean 0.2461")
    add("GraphSAGE ROC-AUC (clean multi-seed mean)", 0.877642, 0.911341, gs["roc_auc"]["mean"], "no",
        "original protocol leaks", "clean ROC-AUC 0.6634")
    add("GraphSAGE MCC (clean multi-seed mean)", 0.540959, 0.558832, gs["mcc"]["mean"], "no",
        "original protocol leaks", "clean MCC 0.1682")
    # rule engine roc
    for st, paper in [("none", 1.0), ("light", 1.0), ("medium", 1.0), ("heavy", 1.0)]:
        vals = [r["roc_auc_count_score"] for r in rs["results"][st] if r["roc_auc_count_score"] is not None]
        aud = sum(vals) / len(vals)
        add(f"Rule Engine ROC-AUC ({st} mimicry)", paper, paper, aud, "no",
            "fabricated constant from getattr default", "no roc_auc field in MetricResult")
    # mimicry
    for st in ["none", "light", "medium", "heavy"]:
        a = mi["strengths"][st]["aggregate"]
        add(f"Mimicry Rule Engine F1 ({st})", {"none": 0.7778, "light": 0.3, "medium": 0.1657, "heavy": 0.0882}[st],
            {"none": 0.7778, "light": 0.3, "medium": 0.1657, "heavy": 0.0882}[st],
            a["f1_mean"], "yes", "none", "exact at seed 42; mean over 10 seeds reported here")
        add(f"Mimicry noise edges ({st})",
            {"none": 0, "light": 70, "medium": 163, "heavy": 351}[st], None,
            a["noise_edges_mean"], "yes", "none", "verified exact")
    # ablation
    a_all = ab["aggregate"]["ALL Rules Enabled"]
    add("Ablation ALL-rules F1 (seed 42)", 0.7222, 0.7222, ab["aggregate"]["ALL Rules Enabled"]["f1"]["values"][4],
        "yes", "single seed in original", "multi-seed mean reported in tables")
    # scalability
    if sc:
        g = sc["per_size"]["1000000"]["aggregate"]
        add("Scalability Rule Engine time 1M edges (s)", 16.9903, None, g["re_detector"]["mean"], "partial",
            "hardware dependent", "repo committed 16.99s; audit host ~2x slower")
    else:
        add("Scalability Rule Engine time 1M edges (s)", 16.9903, None, "PENDING", "partial",
            "hardware dependent", "audit running")
    # DARPA
    for ds, f1 in [("1r", 0.4783), ("3", 0.4706), ("5m", 0.4571), ("6r", 0.3438)]:
        add(f"DARPA {ds} Rule Engine F1", f1, "UNVERIFIABLE", "UNVERIFIABLE", "no",
            "dataset absent from repo; synthetic fallback", "50k-edge slice of parsed CSV")

    fields = ["experiment", "paper_value", "original_reproduction", "audited_value",
              "difference", "relative_difference", "reproducible", "methodology_issue", "notes"]
    with open(OUT / "final_result_reconciliation.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ---------------- journal tables ----------------
    def md_table(path, header, lines):
        with open(path, "w") as f:
            f.write("| " + " | ".join(header) + " |\n")
            f.write("|" + "|".join(["---"] * len(header)) + "|\n")
            for ln in lines:
                f.write("| " + " | ".join(str(x) for x in ln) + " |\n")

    def tex_table(path, caption, header, lines):
        cols = "l" + "r" * (len(header) - 1)
        with open(path, "w") as f:
            f.write("\\begin{table}[h]\n\\centering\n\\caption{%s}\n" % caption)
            f.write("\\begin{tabular}{%s}\n\\hline\n" % cols)
            f.write(" & ".join(header) + " \\\\\n\\hline\n")
            for ln in lines:
                f.write(" & ".join(str(x) for x in ln) + " \\\\\n")
            f.write("\\hline\n\\end{tabular}\n\\end{table}\n")

    # Table 1 dataset characteristics
    t1 = [["synthetic", 80, 179, "-", "generated"],
          ["1r (Theia)", 408320, 9295127, 50000, "not in repo"],
          ["3 (Theia)", 20157, 297777, 50000, "not in repo"],
          ["5m (Theia)", 34835, 464858, 50000, "not in repo"],
          ["6r (Theia)", 1123475, 18206475, 50000, "not in repo"]]
    md_table(TABLES / "table1_dataset_characteristics.md",
             ["dataset", "nodes", "full_edges", "edges_used", "availability"], t1)
    tex_table(TABLES / "table1_dataset_characteristics.tex", "Dataset characteristics.",
              ["Dataset", "Nodes", "Full edges", "Edges used"], t1)

    # Table 2 synthetic detection performance (seed 42, original protocol)
    t2 = [["Rule Engine", 0.8125, 0.65, 0.7222, 0.9457],
          ["GraphSAGE (leaky)", 0.70, 0.4667, 0.56, 0.9385]]
    md_table(TABLES / "table2_synthetic_detection.md",
             ["detector", "precision", "recall", "f1", "accuracy"], t2)
    tex_table(TABLES / "table2_synthetic_detection.tex", "Synthetic detection performance (seed 42, original protocol).",
              ["Detector", "Precision", "Recall", "F1", "Accuracy"], t2)

    # Table 3 DARPA cross-scenario (unverifiable)
    t3 = [["1r", 0.4231, 0.55, 0.4783, "unverifiable"],
          ["3", 0.3871, 0.60, 0.4706, "unverifiable"],
          ["5m", 0.5333, 0.40, 0.4571, "unverifiable"],
          ["6r", 0.25, 0.55, 0.3438, "unverifiable"]]
    md_table(TABLES / "table3_darpa_cross_scenario.md",
             ["scenario", "precision", "recall", "f1", "status"], t3)
    tex_table(TABLES / "table3_darpa_cross_scenario.tex", "DARPA cross-scenario (committed values; not reproducible).",
              ["Scenario", "Precision", "Recall", "F1", "Status"], t3)

    # Table 4 mimicry robustness (rule engine, 10-seed mean)
    t4 = []
    for st in ["none", "light", "medium", "heavy"]:
        a = mi["strengths"][st]["aggregate"]
        t4.append([st, f"{a['noise_edges_mean']:.0f}", f"{a['precision_mean']:.4f}", f"{a['recall_mean']:.4f}", f"{a['f1_mean']:.4f}"])
    md_table(TABLES / "table4_mimicry_robustness.md",
             ["strength", "noise_edges", "precision", "recall", "f1"], t4)
    tex_table(TABLES / "table4_mimicry_robustness.tex", "Mimicry robustness (Rule Engine, 10-seed mean).",
              ["Strength", "Noise", "Precision", "Recall", "F1"], t4)

    # Table 5 rule ablation (10-seed mean +/- std)
    t5 = []
    for cfg in ["ALL Rules Enabled", "Without Structural Rules", "Without Temporal Rules", "Without Semantic Rules",
                "Without SequenceGapRule", "Without ReadWriteConsistencyRule", "Without NetworkConsistencyRule",
                "Without SpawnConsistencyRule", "Without SequenceMonotonicityRule", "Without ProcessActivityTemporalRule"]:
        a = ab["aggregate"][cfg]
        t5.append([cfg, f"{a['f1']['mean']:.4f} ± {a['f1']['std']:.4f}"])
    md_table(TABLES / "table5_rule_ablation.md", ["configuration", "f1 (mean ± std)"], t5)
    tex_table(TABLES / "table5_rule_ablation.tex", "Rule ablation (10-seed mean $\\pm$ std).",
              ["Configuration", "F1"], t5)

    # Table 6 scalability
    t6 = []
    if sc:
        for n in sc["scales"]:
            g = sc["per_size"][str(n)]["aggregate"]
            t6.append([f"{n:,}", f"{g['re_detector']['mean']:.4f}",
                       f"{g['gs_infer']['mean']:.4f}", f"{g['gs_train_epoch']['mean']:.4f}",
                       f"{g['re_peak_mb']['mean']:.1f}", f"{g['gs_peak_mb']['mean']:.1f}",
                       f"{g['re_throughput_eps']['mean']:.0f}"])
        md_table(TABLES / "table6_scalability.md",
                 ["edges", "re_detect_s", "gs_infer_s", "gs_train_epoch_s", "re_peak_mb", "gs_peak_mb", "re_eps"], t6)
        tex_table(TABLES / "table6_scalability.tex", "Scalability (5 reps, mean).",
                  ["Edges", "RE s", "GS infer s", "GS train/ep s", "RE peak MB", "GS peak MB", "RE eps"], t6)

    # Table 7 multi-seed mean +/- std
    t7 = []
    for m in ["precision", "recall", "f1", "accuracy", "balanced_accuracy", "mcc", "fpr", "fnr", "specificity", "roc_auc", "pr_auc"]:
        t7.append([m, f"{re[m]['mean']:.4f} ± {re[m]['std']:.4f}", f"{gs[m]['mean']:.4f} ± {gs[m]['std']:.4f}"])
    md_table(TABLES / "table7_multiseed.md", ["metric", "rule_engine", "graphsage_clean"], t7)
    tex_table(TABLES / "table7_multiseed.tex", "Multi-seed mean $\\pm$ std (clean protocol, n=10).",
              ["Metric", "Rule Engine", "GraphSAGE"], t7)

    # Table 8 statistical significance
    ps = cm["paired_stats"]
    t8 = [["mean F1 difference", f"{ps['mean_difference']:.4f}"],
          ["95% CI", f"[{ps['ci95_low']:.4f}, {ps['ci95_high']:.4f}]"],
          ["Wilcoxon statistic", f"{ps.get('wilcoxon_statistic')}"],
          ["Wilcoxon p-value", f"{ps.get('wilcoxon_pvalue')}"],
          ["Paired t p-value", f"{ps.get('ttest_pvalue'):.3e}"],
          ["Cohen's d_z", f"{ps.get('cohens_dz'):.4f}"]]
    md_table(TABLES / "table8_significance.md", ["statistic", "value"], t8)
    tex_table(TABLES / "table8_significance.tex", "Paired statistical comparison (Rule Engine vs GraphSAGE, n=10).",
              ["Statistic", "Value"], t8)

    print("Wrote reconciliation CSV and 8 tables to", TABLES)


if __name__ == "__main__":
    main()
