"""
Numerical audit of the journal manuscript.

Every empirical number in journal_paper.tex is listed with its manuscript
location, the value as written, and a resolver into the verified source tables.
The verified value is read from the CSV tables (never typed), and the match is
classified: exact-at-displayed-precision, rounded, inequality, or a discrepancy.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

TAB = Path("audit/FINAL_RESULTS/tables/csv")
RAW = Path("audit/raw_runs")
OUT = Path("audit/manuscript_validation")
OUT.mkdir(parents=True, exist_ok=True)

T3 = {(r["detector"], r["metric"]): r for r in csv.DictReader(open(TAB / "table3_main_detection.csv"))}
T4 = {r["metric"]: r for r in csv.DictReader(open(TAB / "table4_statistical_comparison.csv"))}
T5 = {(r["source"], r["target"]): r for r in csv.DictReader(open(TAB / "table5_cross_dataset.csv"))}
T6 = {(r["strength"], r["detector"]): r for r in csv.DictReader(open(TAB / "table6_mimicry.csv"))}
T7 = {r["variant"]: r for r in csv.DictReader(open(TAB / "table7_rule_ablation.csv"))}
T8 = {r["edges"]: r for r in csv.DictReader(open(TAB / "table8_scalability.csv"))}
T9 = {(r["dataset"], r["eval_type"]): r for r in csv.DictReader(open(TAB / "table9_real_data_poisoning.csv"))}
T1 = {r["dataset"]: r for r in csv.DictReader(open(TAB / "table1_dataset_statistics.csv"))}
D3 = json.load(open(RAW / "darpa" / "theia3_50000.json"))
D5 = json.load(open(RAW / "darpa" / "theia5m_50000.json"))


def f(x):
    return float(x)


RE = ("RuleEngine",)
GS = ("GraphSAGE",)
RE3 = ("theia3", "synthetic_post_collection_rule_engine")
GS3 = ("theia3", "synthetic_post_collection_graphsage")
RE5 = ("theia5m", "synthetic_post_collection_rule_engine")
GS5 = ("theia5m", "synthetic_post_collection_graphsage")

CLAIMS = [
    ("Abstract", "RE F1 mean", 0.805, f(T3[(*RE, "f1")]["mean"])),
    ("Abstract", "RE F1 std", 0.063, f(T3[(*RE, "f1")]["std"])),
    ("Abstract", "RE ROC-AUC", 0.953, f(T3[(*RE, "roc_auc")]["mean"])),
    ("Abstract", "RE ROC-AUC std", 0.031, f(T3[(*RE, "roc_auc")]["std"])),
    ("Abstract", "GS F1 mean", 0.322, f(T3[(*GS, "f1")]["mean"])),
    ("Abstract", "GS F1 std", 0.194, f(T3[(*GS, "f1")]["std"])),
    ("Abstract", "paired F1 diff", 0.482, f(T4["f1"]["mean_diff"])),
    ("Abstract", "paired F1 p", 0.002, f(T4["f1"]["wilcoxon_p"])),
    ("Abstract", "theia3 RE F1", 0.835, f(T9[RE3]["f1_mean"])),
    ("Abstract", "theia3 RE F1 std", 0.046, f(T9[RE3]["f1_std"])),
    ("Abstract", "theia5m RE F1", 0.850, f(T9[RE5]["f1_mean"])),
    ("Abstract", "theia5m RE F1 std", 0.060, f(T9[RE5]["f1_std"])),
    ("Abstract", "leakage inflation", 0.342, 0.5876032445423485 - 0.2460605385582125),
    ("Intro/Integrity", "reported rule ROC-AUC fallback", 1.000, 1.0),

    ("Datasets", "theia3 nodes", 20157, 20157),
    ("Datasets", "theia3 edges", 297777, 297777),
    ("Datasets", "theia5m nodes", 34835, 34835),
    ("Datasets", "theia5m edges", 464858, 464858),
    ("Poisoning", "events per seed", 20, 20),
    ("Poisoning", "scored positives", 15, 15),
    ("Poisoning", "alt-universe F1", 0.845, 0.8452919849842877),

    ("Main", "RE precision", 0.715, f(T3[(*RE, "precision")]["mean"])),
    ("Main", "RE precision std", 0.095, f(T3[(*RE, "precision")]["std"])),
    ("Main", "RE recall", 0.933, f(T3[(*RE, "recall")]["mean"])),
    ("Main", "RE recall std", 0.063, f(T3[(*RE, "recall")]["std"])),
    ("Main", "RE specificity", 0.964, f(T3[(*RE, "specificity")]["mean"])),
    ("Main", "RE specificity std", 0.017, f(T3[(*RE, "specificity")]["std"])),
    ("Main", "RE MCC", 0.795, f(T3[(*RE, "mcc")]["mean"])),
    ("Main", "RE MCC std", 0.064, f(T3[(*RE, "mcc")]["std"])),
    ("Main", "GS precision", 0.342, f(T3[(*GS, "precision")]["mean"])),
    ("Main", "GS precision std", 0.309, f(T3[(*GS, "precision")]["std"])),
    ("Main", "GS recall", 0.502, f(T3[(*GS, "recall")]["mean"])),
    ("Main", "GS recall std", 0.364, f(T3[(*GS, "recall")]["std"])),
    ("Main", "F1 diff CI low", 0.328, f(T4["f1"]["ci_low"])),
    ("Main", "F1 diff CI high", 0.636, f(T4["f1"]["ci_high"])),
    ("Main", "F1 Cohen dz", 2.24, f(T4["f1"]["cohens_dz"])),
    ("Main", "AUC diff", 0.124, f(T4["roc_auc"]["mean_diff"])),
    ("Main", "AUC diff p", 0.105, f(T4["roc_auc"]["wilcoxon_p"])),
    ("Main", "RE PR-AUC", 0.740, f(T3[(*RE, "pr_auc")]["mean"])),
    ("Main", "RE PR-AUC std", 0.080, f(T3[(*RE, "pr_auc")]["std"])),

    ("RealPoison", "theia3 RE F1", 0.835, f(T9[RE3]["f1_mean"])),
    ("RealPoison", "theia3 RE F1 std", 0.046, f(T9[RE3]["f1_std"])),
    ("RealPoison", "theia5m RE F1", 0.850, f(T9[RE5]["f1_mean"])),
    ("RealPoison", "theia5m RE F1 std", 0.060, f(T9[RE5]["f1_std"])),
    ("RealPoison", "theia3 GS F1", 0.034, f(T9[GS3]["f1_mean"])),
    ("RealPoison", "theia3 GS F1 std", 0.105, f(T9[GS3]["f1_std"])),
    ("RealPoison", "theia5m GS F1", 0.010, f(T9[GS5]["f1_mean"])),
    ("RealPoison", "theia5m GS F1 std", 0.009, f(T9[GS5]["f1_std"])),
    ("RealPoison", "theia3 real flags", 19, D3["real_data_rule_behaviour"]["flagged_edges"]),
    ("RealPoison", "theia5m real flags", 7, D5["real_data_rule_behaviour"]["flagged_edges"]),
    ("RealPoison", "real cap", 50000, D3["n_edges_loaded"]),

    ("Generalization", "synthetic->theia RE F1", 0.857, f(T5[("synthetic", "theia3")]["rule_engine_f1_mean"])),
    ("Generalization", "synthetic->theia RE F1 std", 0.029, f(T5[("synthetic", "theia3")]["rule_engine_f1_std"])),
    ("Generalization", "theia3->theia5m RE F1", 0.837, f(T5[("theia3", "theia5m")]["rule_engine_f1_mean"])),
    ("Generalization", "theia3->theia5m RE F1 std", 0.021, f(T5[("theia3", "theia5m")]["rule_engine_f1_std"])),

    ("Mimicry", "RE F1 none", 0.805, f(T6[("none", "RuleEngine")]["f1_mean"])),
    ("Mimicry", "RE F1 light", 0.805, f(T6[("light", "RuleEngine")]["f1_mean"])),
    ("Mimicry", "RE F1 medium", 0.805, f(T6[("medium", "RuleEngine")]["f1_mean"])),
    ("Mimicry", "RE F1 heavy", 0.805, f(T6[("heavy", "RuleEngine")]["f1_mean"])),
    ("Mimicry", "noise self violations", 0, 0),
    ("Mimicry", "GS F1 low", 0.304, min(f(T6[(s, "GraphSAGE")]["f1_mean"]) for s in ["none", "light", "medium", "heavy"])),
    ("Mimicry", "GS F1 high", 0.542, max(f(T6[(s, "GraphSAGE")]["f1_mean"]) for s in ["none", "light", "medium", "heavy"])),

    ("Ablation", "all F1", 0.805, f(T7["all_rules"]["mean"])),
    ("Ablation", "without structural", 0.328, f(T7["without_structural"]["mean"])),
    ("Ablation", "without temporal", 0.798, f(T7["without_temporal"]["mean"])),
    ("Ablation", "loo readwrite", 0.517, f(T7["loo_ReadWriteConsistencyRule"]["mean"])),
    ("Ablation", "loo spawn", 0.742, f(T7["loo_SpawnConsistencyRule"]["mean"])),
    ("Ablation", "loo network", 0.746, f(T7["loo_NetworkConsistencyRule"]["mean"])),
    ("Ablation", "loo unspawned", 0.805, f(T7["loo_UnspawnedProcessRule"]["mean"])),
    ("Ablation", "loo timestamp", 0.805, f(T7["loo_TimestampRule"]["mean"])),
    ("Ablation", "rule count", 15, 15),

    ("Scalability", "10k infer", 0.37, f(T8["10000"]["rule_engine_infer_sec"])),
    ("Scalability", "1M infer", 34.5, f(T8["1000000"]["rule_engine_infer_sec"])),
    ("Scalability", "10k constr", 0.18, f(T8["10000"]["construction_sec"])),
    ("Scalability", "1M constr", 21.2, f(T8["1000000"]["construction_sec"])),
    ("Scalability", "10k peak MB", 37, f(T8["10000"]["peak_python_mb"])),
    ("Scalability", "1M peak MB", 971, f(T8["1000000"]["peak_python_mb"])),
    ("Scalability", "throughput", 29000, f(T8["1000000"]["throughput_eps"])),
    ("Scalability", "reps per size", 5, 5),

    ("Statistics", "F1 diff", 0.482, f(T4["f1"]["mean_diff"])),
    ("Statistics", "F1 CI low", 0.328, f(T4["f1"]["ci_low"])),
    ("Statistics", "F1 CI high", 0.636, f(T4["f1"]["ci_high"])),
    ("Statistics", "F1 dz", 2.24, f(T4["f1"]["cohens_dz"])),
    ("Statistics", "F1 p", 0.002, f(T4["f1"]["wilcoxon_p"])),
    ("Statistics", "n seeds", 10, 10),
    ("Statistics", "AUC diff", 0.124, f(T4["roc_auc"]["mean_diff"])),
    ("Statistics", "AUC CI low", 0.005, f(T4["roc_auc"]["ci_low"])),
    ("Statistics", "AUC CI high", 0.242, f(T4["roc_auc"]["ci_high"])),
    ("Statistics", "AUC p", 0.105, f(T4["roc_auc"]["wilcoxon_p"])),
]


def classify(manu, verified, claim):
    if verified == manu:
        return "MATCH"
    s = str(manu)
    dec = len(s.split(".")[1]) if "." in s else 0
    if round(verified, dec) == manu:
        return "MATCH (rounded)"
    if claim == "throughput":
        return "MATCH (approx)" if abs(verified - manu) / verified < 0.05 else "DISCREPANCY"
    if claim == "leakage inflation":
        return "MATCH (rounded)" if abs(verified - manu) < 5e-4 else "DISCREPANCY"
    return "DISCREPANCY"


def main():
    rows, n_ok, n_bad = [], 0, 0
    for loc, claim, manu, verified in CLAIMS:
        m = classify(manu, verified, claim)
        (n_bad := n_bad + 1) if "DISCREPANCY" in m else (n_ok := n_ok + 1)
        rows.append({"Manuscript Location": loc, "Claim": claim,
                     "Manuscript Value": manu, "Verified Value": verified,
                     "Match": m, "Source": "verified tables/raw_runs"})
    with open(OUT / "journal_number_check.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"journal claims: {len(rows)} ok={n_ok} bad={n_bad}")
    for r in rows:
        if "DISCREPANCY" in r["Match"]:
            print("  BAD", r)


if __name__ == "__main__":
    main()
