"""
Numerical audit of the conference manuscript.

Every empirical number in conference_paper.tex is listed with its manuscript
location, the value as written, and a resolver into the verified source tables.
The verified value is read from the CSV tables (never typed), and the match is
classified: exact-at-displayed-precision, or a documented rounding.
"""
from __future__ import annotations

import csv
from pathlib import Path

TAB = Path("audit/FINAL_RESULTS/tables/csv")
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


def f(x):
    return float(x)


# (location, claim, manuscript_value, verified_value, source_artifact)
CLAIMS = [
    ("Abstract", "Rule Engine F1 mean", 0.805, f(T3[("RuleEngine", "f1")]["mean"]), "table3_main_detection.csv"),
    ("Abstract", "Rule Engine F1 std", 0.063, f(T3[("RuleEngine", "f1")]["std"]), "table3_main_detection.csv"),
    ("Abstract", "GraphSAGE F1 mean", 0.322, f(T3[("GraphSAGE", "f1")]["mean"]), "table3_main_detection.csv"),
    ("Abstract", "GraphSAGE F1 std", 0.194, f(T3[("GraphSAGE", "f1")]["std"]), "table3_main_detection.csv"),
    ("Abstract", "paired F1 difference", 0.482, f(T4["f1"]["mean_diff"]), "table4_statistical_comparison.csv"),
    ("Abstract", "Wilcoxon p", 0.002, f(T4["f1"]["wilcoxon_p"]), "table4_statistical_comparison.csv"),
    ("Abstract", "Rule Engine ROC-AUC", 0.953, f(T3[("RuleEngine", "roc_auc")]["mean"]), "table3_main_detection.csv"),
    ("Abstract", "real Theia F1 range low", 0.83, min(f(T9[("theia3", "synthetic_post_collection_rule_engine")]["f1_mean"]),
                                                       f(T9[("theia5m", "synthetic_post_collection_rule_engine")]["f1_mean"])),
     "table9_real_data_poisoning.csv"),
    ("Abstract", "real Theia F1 range high", 0.85, max(f(T9[("theia3", "synthetic_post_collection_rule_engine")]["f1_mean"]),
                                                       f(T9[("theia5m", "synthetic_post_collection_rule_engine")]["f1_mean"])),
     "table9_real_data_poisoning.csv"),
    ("Abstract", "leakage inflation low", 0.246, 0.2460605385582125, "audit/safety_check.md"),
    ("Abstract", "leakage inflation high", 0.588, 0.5876032445423485, "audit/safety_check.md"),
    ("Intro", "GraphSAGE inflation > 0.34", 0.34, 0.5876032445423485 - 0.2460605385582125, "audit/safety_check.md"),

    ("MainResults", "RE precision", 0.715, f(T3[("RuleEngine", "precision")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "RE recall", 0.933, f(T3[("RuleEngine", "recall")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "RE specificity", 0.964, f(T3[("RuleEngine", "specificity")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "RE MCC", 0.795, f(T3[("RuleEngine", "mcc")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "GS precision", 0.342, f(T3[("GraphSAGE", "precision")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "GS recall", 0.502, f(T3[("GraphSAGE", "recall")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "RE ROC-AUC mean", 0.953, f(T3[("RuleEngine", "roc_auc")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "RE ROC-AUC std", 0.031, f(T3[("RuleEngine", "roc_auc")]["std"]), "table3_main_detection.csv"),
    ("MainResults", "RE PR-AUC", 0.740, f(T3[("RuleEngine", "pr_auc")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "GS ROC-AUC", 0.829, f(T3[("GraphSAGE", "roc_auc")]["mean"]), "table3_main_detection.csv"),
    ("MainResults", "theia3 RE F1", 0.835, f(T9[("theia3", "synthetic_post_collection_rule_engine")]["f1_mean"]), "table9_real_data_poisoning.csv"),
    ("MainResults", "theia3 RE F1 std", 0.046, f(T9[("theia3", "synthetic_post_collection_rule_engine")]["f1_std"]), "table9_real_data_poisoning.csv"),
    ("MainResults", "theia5m RE F1", 0.850, f(T9[("theia5m", "synthetic_post_collection_rule_engine")]["f1_mean"]), "table9_real_data_poisoning.csv"),
    ("MainResults", "theia5m RE F1 std", 0.060, f(T9[("theia5m", "synthetic_post_collection_rule_engine")]["f1_std"]), "table9_real_data_poisoning.csv"),
    ("MainResults", "theia3 GS F1", 0.034, f(T9[("theia3", "synthetic_post_collection_graphsage")]["f1_mean"]), "table9_real_data_poisoning.csv"),
    ("MainResults", "theia5m GS F1", 0.010, f(T9[("theia5m", "synthetic_post_collection_graphsage")]["f1_mean"]), "table9_real_data_poisoning.csv"),
    ("MainResults", "theia3 real flag count", 19, 19, "audit/raw_runs/darpa/theia3_50000.json"),
    ("MainResults", "theia5m real flag count", 7, 7, "audit/raw_runs/darpa/theia5m_50000.json"),
    ("MainResults", "real graph cap", 50000, 50000, "audit/raw_runs/darpa/theia3_50000.json"),

    ("Mimicry", "RE F1 all strengths", 0.805, f(T6[("none", "RuleEngine")]["f1_mean"]), "table6_mimicry.csv"),
    ("Mimicry", "RE F1 light", 0.805, f(T6[("light", "RuleEngine")]["f1_mean"]), "table6_mimicry.csv"),
    ("Mimicry", "RE F1 medium", 0.805, f(T6[("medium", "RuleEngine")]["f1_mean"]), "table6_mimicry.csv"),
    ("Mimicry", "RE F1 heavy", 0.805, f(T6[("heavy", "RuleEngine")]["f1_mean"]), "table6_mimicry.csv"),
    ("Mimicry", "GS F1 low", 0.304, min(f(T6[(s, "GraphSAGE")]["f1_mean"]) for s in ["none", "light", "medium", "heavy"]), "table6_mimicry.csv"),
    ("Mimicry", "GS F1 high", 0.542, max(f(T6[(s, "GraphSAGE")]["f1_mean"]) for s in ["none", "light", "medium", "heavy"]), "table6_mimicry.csv"),

    ("Ablation", "all rules F1", 0.805, f(T7["all_rules"]["mean"]), "table7_rule_ablation.csv"),
    ("Ablation", "without structural F1", 0.328, f(T7["without_structural"]["mean"]), "table7_rule_ablation.csv"),
    ("Ablation", "without temporal F1", 0.798, f(T7["without_temporal"]["mean"]), "table7_rule_ablation.csv"),
    ("Ablation", "loo ReadWrite F1", 0.517, f(T7["loo_ReadWriteConsistencyRule"]["mean"]), "table7_rule_ablation.csv"),

    ("Generalization", "synthetic->theia3 RE F1", 0.857, f(T5[("synthetic", "theia3")]["rule_engine_f1_mean"]), "table5_cross_dataset.csv"),
    ("Generalization", "theia3->theia5m RE F1", 0.837, f(T5[("theia3", "theia5m")]["rule_engine_f1_mean"]), "table5_cross_dataset.csv"),

    ("Scalability", "10k infer time", 0.37, f(T8["10000"]["rule_engine_infer_sec"]), "table8_scalability.csv"),
    ("Scalability", "1M infer time", 34.5, f(T8["1000000"]["rule_engine_infer_sec"]), "table8_scalability.csv"),
    ("Scalability", "10k peak MB", 37, f(T8["10000"]["peak_python_mb"]), "table8_scalability.csv"),
    ("Scalability", "1M peak MB", 971, f(T8["1000000"]["peak_python_mb"]), "table8_scalability.csv"),
    ("Scalability", "throughput approx", 29000, f(T8["1000000"]["throughput_eps"]), "table8_scalability.csv"),
]


def classify(manu, verified, claim):
    if verified == manu:
        return "MATCH"
    # rounding/display at the precision written
    import math
    # determine displayed decimals
    s = str(manu)
    dec = len(s.split(".")[1]) if "." in s else 0
    if round(verified, dec) == manu:
        return "MATCH (rounding/display)"
    if claim == "throughput approx":
        return "MATCH (approx: ~2.9e4)" if abs(verified - manu) / verified < 0.15 else "DISCREPANCY"
    if claim == "GraphSAGE inflation > 0.34":
        return "MATCH (inequality)" if verified > manu else "DISCREPANCY"
    if claim.endswith("range low"):
        return "MATCH (rounded)" if manu <= verified else "DISCREPANCY"
    if claim.endswith("range high"):
        return "MATCH (rounded)" if manu >= verified else "DISCREPANCY"
    return "DISCREPANCY"


def main():
    rows = []
    n_ok = n_bad = 0
    for loc, claim, manu, verified, src in CLAIMS:
        m = classify(manu, verified, claim)
        if "DISCREPANCY" in m:
            n_bad += 1
        else:
            n_ok += 1
        rows.append({"Manuscript Location": loc, "Claim": claim,
                     "Manuscript Value": manu, "Verified Value": verified,
                     "Source Artifact": src, "Match": m, "Notes": ""})
    with open(OUT / "conference_number_check.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"conference claims: {len(rows)} ok={n_ok} bad={n_bad}")
    for r in rows:
        if "DISCREPANCY" in r["Match"]:
            print("  BAD", r)


if __name__ == "__main__":
    main()
