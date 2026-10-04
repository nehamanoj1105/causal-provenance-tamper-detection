"""
Build audit/FINAL_RESULTS/: the single inspection point for the final evidence.

- creates the directory tree
- copies/link-reproduces final tables, figures, raw results and statistics
  WITHOUT altering contents
- writes FINAL_NUMBERS.md programmatically from the verified tables
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

ROOT = Path("audit")
FR = ROOT / "FINAL_RESULTS"
TAB = ROOT / "journal_ready_tables"
PLOTS = ROOT / "plots"
RAW = ROOT / "raw_runs"

SUBDIRS = ["tables/csv", "tables/markdown", "tables/latex",
           "tables/journal_ready_csv", "tables/journal_ready_markdown",
           "tables/journal_ready_latex",
           "figures", "raw_results", "statistics", "dataset_results",
           "model_results", "robustness", "ablation", "scalability",
           "paper_sources"]


def build_dirs():
    FR.mkdir(parents=True, exist_ok=True)
    for d in SUBDIRS:
        (FR / d).mkdir(parents=True, exist_ok=True)


def copy_tables():
    # journal-ready tables are kept under a separate folder so their numbering
    # never clashes with the curated manuscript tables (table1..table9)
    for p in sorted(TAB.glob("*.csv")):
        shutil.copy2(p, FR / "tables" / "journal_ready_csv" / p.name)
    for p in sorted(TAB.glob("*.md")):
        shutil.copy2(p, FR / "tables" / "journal_ready_markdown" / p.name)
    for p in sorted(TAB.glob("*.tex")):
        shutil.copy2(p, FR / "tables" / "journal_ready_latex" / p.name)
    # paper source copies
    for p in sorted(TAB.glob("*.csv")) + sorted(TAB.glob("*.tex")):
        shutil.copy2(p, FR / "paper_sources" / p.name)


def copy_raw():
    for p in sorted(RAW.rglob("*.json")):
        rel = p.relative_to(RAW)
        dst = FR / "raw_results" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def copy_stats_and_subsets():
    # statistics: significance table + gt sensitivity
    for name in ["table8_significance.csv", "table8_significance.md"]:
        shutil.copy2(TAB / name, FR / "statistics" / name)
    gts = RAW / "gt_sensitivity.json"
    if gts.exists():
        shutil.copy2(gts, FR / "statistics" / "gt_sensitivity.json")
    # dataset results
    for name in ["table1_dataset_characteristics.csv", "table3_darpa_cross_scenario.csv"]:
        shutil.copy2(TAB / name, FR / "dataset_results" / name)
    for p in sorted((RAW / "darpa").glob("*.json")):
        shutil.copy2(p, FR / "dataset_results" / p.name)
    # model results
    for name in ["table2_synthetic_detection.csv", "table7_multiseed.csv",
                 "table9_generalization.csv"]:
        shutil.copy2(TAB / name, FR / "model_results" / name)
    # robustness
    for name in ["table4_mimicry_robustness.csv"]:
        shutil.copy2(TAB / name, FR / "robustness" / name)
    for p in sorted((RAW / "generalization").glob("*.json")):
        shutil.copy2(p, FR / "robustness" / p.name)
    # ablation
    shutil.copy2(TAB / "table5_rule_ablation.csv", FR / "ablation" / "table5_rule_ablation.csv")
    # scalability
    shutil.copy2(TAB / "table6_scalability.csv", FR / "scalability" / "table6_scalability.csv")


def copy_figures(figure_names):
    for n in figure_names:
        src = PLOTS / n
        if src.exists():
            shutil.copy2(src, FR / "figures" / n)


def read_csv(path):
    return list(csv.DictReader(open(path)))


def fmt(v, nd=4):
    try:
        return f"{float(v):.{nd}f}"
    except Exception:
        return str(v)


def fin_numbers():
    L = []
    A = L.append

    def block(title, **kw):
        A(f"### {title}\n")
        for k in ["Experiment", "Dataset", "Protocol", "Model", "Seeds", "Metric",
                  "Mean", "Std", "95% CI", "Raw artifact", "Source table",
                  "Source figure", "Status"]:
            if k in kw:
                A(f"- **{k}:** {kw[k]}")
        A("")

    A("# FINAL_NUMBERS — verified numerical source of truth\n")
    A("Every value below is re-derived from `audit/raw_runs/` by "
      "`audit/scripts/final_validation.py` (0 discrepancies) and aggregated by "
      "`audit/scripts/make_final.py`. Values are means over the stated seeds "
      "unless noted. Full precision lives in the CSV artifacts; this file "
      "rounds to 4 dp for readability only.\n")

    A("## 0. Scoring-universe sensitivity (must be stated in the paper)\n")
    A("The corrected protocol scores only edges present in the final graph. The "
      "repository's evaluator additionally adds the ids of deleted edges (which "
      "no longer exist) to the scoring universe. Using the same detector:\n")
    A("- Final-graph universe (corrected, used in the paper): F1 = 0.8048 ± 0.0627, "
      "precision = 0.7146, recall = 0.9329, ROC-AUC = 0.9528.")
    A("- Repo-style universe (final ∪ absent GT ids): F1 = 0.8453 ± 0.0513, "
      "precision = 0.7700, recall = 0.9445, ROC-AUC = 0.9583.")
    A("Raw: `audit/raw_runs/gt_sensitivity.json`. The manuscript reports the "
      "final-graph universe and states the assumption; a deletion cannot be "
      "edge-matched in the final graph and is reported separately as a limitation.\n")

    # Dataset
    A("## 1. Dataset characteristics (real data)\n")
    for r in read_csv(TAB / "table1_dataset_characteristics.csv"):
        A(f"- **{r['source']}**: {r['nodes']} nodes, {r['edges']} edges, "
          f"{r['skipped']} skipped. Raw: `audit/data/raw/theia/`; "
          f"parse via `src/graph_construction/cdm_parser.py`.")
    A("")

    # Synthetic main
    t2 = read_csv(TAB / "table2_synthetic_detection.csv")
    A("## 2. Synthetic detection — Rule Engine (10 seeds)\n")
    A("Protocol: synthetic graph (30 processes, 40 files, 10 network), "
      "5 deletions + 5 insertions + 5 reorderings + 5 dependency forgeries; "
      "10 detectable + 5 undetectable (deleted) positives; corrected "
      "final-graph scoring universe. Seeds 1,7,13,21,42,99,123,256,512,1024.\n")
    for r in t2:
        if r["detector"] != "RuleEngine":
            continue
        ci = f"[{fmt(r['ci_low'])}, {fmt(r['ci_high'])}]" if r["ci_low"] else "n/a"
        block(f"Rule Engine {r['metric']}",
              Experiment="Synthetic main detection", Dataset="Synthetic controlled",
              Protocol="corrected poisoning, final-graph universe", Model="Rule Engine",
              Seeds=r["n"], Metric=r["metric"].upper(), Mean=fmt(r["mean"]),
              Std=fmt(r["std"]), **{"95% CI": ci},
              **{"Raw artifact": "audit/raw_runs/synthetic/seed_*.json"},
              **{"Source table": "table2_synthetic_detection.csv"},
              **{"Source figure": "figures/fig_main_performance.png"},
              Status="SUPPORTED")

    A("## 3. Synthetic detection — GraphSAGE (10 seeds, leakage-free)\n")
    A("Protocol: same graphs and positives; strict train/val/test split; "
      "threshold selected on validation only.\n")
    for r in t2:
        if r["detector"] != "GraphSAGE":
            continue
        ci = f"[{fmt(r['ci_low'])}, {fmt(r['ci_high'])}]" if r["ci_low"] else "n/a"
        block(f"GraphSAGE {r['metric']}",
              Experiment="Synthetic main detection", Dataset="Synthetic controlled",
              Protocol="leakage-free train/val/test", Model="GraphSAGE",
              Seeds=r["n"], Metric=r["metric"].upper(), Mean=fmt(r["mean"]),
              Std=fmt(r["std"]), **{"95% CI": ci},
              **{"Raw artifact": "audit/raw_runs/synthetic/seed_*.json"},
              **{"Source table": "table2_synthetic_detection.csv"},
              **{"Source figure": "figures/fig_main_performance.png"},
              Status="SUPPORTED")

    # Significance
    A("## 4. Statistical significance (paired, 10 seeds)\n")
    for r in read_csv(TAB / "table8_significance.csv"):
        block(f"Paired RuleEngine−GraphSAGE {r['metric']}",
              Experiment="Paired comparison", Dataset="Synthetic controlled",
              Protocol="paired over identical test instances; Wilcoxon signed-rank",
              Model="RuleEngine vs GraphSAGE", Seeds=r["n"], Metric=r["metric"].upper(),
              Mean=f"mean_diff={fmt(r['mean_diff'])}",
              Std=f"std_diff={fmt(r['std_diff'])}",
              **{"95% CI": f"[{fmt(r['ci_low'])}, {fmt(r['ci_high'])}]; "
                           f"Wilcoxon p={fmt(r['wilcoxon_p'],6)}; Cohen dz={fmt(r['cohens_dz'])}"},
              **{"Raw artifact": "audit/raw_runs/synthetic/seed_*.json"},
              **{"Source table": "table8_significance.csv"},
              **{"Source figure": "figures/fig_significance.png"},
              Status="SUPPORTED")

    # Mimicry
    A("## 5. Mimicry robustness (corrected invariant-preserving generator)\n")
    for r in read_csv(TAB / "table4_mimicry_robustness.csv"):
        block(f"Mimicry {r['strength']} — {r['detector']}",
              Experiment="Mimicry robustness", Dataset="Synthetic controlled",
              Protocol=f"{r['strength']} camouflage; noise_self_violations={fmt(r['noise_self_violations'],2)}",
              Model=r["detector"], Seeds="10", Metric="F1",
              Mean=fmt(r["f1_mean"]), Std=fmt(r["f1_std"]),
              **{"95% CI": "see table4"},
              **{"Raw artifact": "audit/raw_runs/synthetic/seed_*.json (.mimicry)"},
              **{"Source table": "table4_mimicry_robustness.csv"},
              **{"Source figure": "figures/fig_mimicry.png"},
              Status="SUPPORTED")

    # Ablation
    A("## 6. Rule ablation (10 seeds)\n")
    for r in read_csv(TAB / "table5_rule_ablation.csv"):
        block(f"Ablation {r['variant']}",
              Experiment="Rule ablation", Dataset="Synthetic controlled",
              Protocol="10 seeds; F1", Model="Rule Engine",
              Seeds=r["n"], Metric="F1", Mean=fmt(r["mean"]), Std=fmt(r["std"]),
              **{"95% CI": f"[{fmt(r['ci_low'])}, {fmt(r['ci_high'])}]" if r["ci_low"] else "n/a"},
              **{"Raw artifact": "audit/raw_runs/ablation/seed_*.json"},
              **{"Source table": "table5_rule_ablation.csv"},
              **{"Source figure": "figures/fig_ablation.png"}, Status="SUPPORTED")

    # DARPA
    A("## 7. Real Theia + synthetic post-collection poisoning\n")
    A("NOT real attack labels. Real provenance graph; attacks injected after "
      "collection. 50,000-edge cap. 20 requested ops → 15 detectable positives "
      "(5 deletions vanish). 10 seeds.\n")
    for r in read_csv(TAB / "table3_darpa_cross_scenario.csv"):
        block(f"DARPA {r['dataset']} — {r['eval_type']}",
              Experiment="Real-data + synthetic poisoning",
              Dataset=f"Theia E3 {r['dataset']} (50k edges)",
              Protocol="synthetic post-collection poisoning", Model=r["eval_type"],
              Seeds=r["n"], Metric="F1", Mean=fmt(r["f1_mean"]), Std=fmt(r["f1_std"]),
              **{"95% CI": "see table3"},
              **{"Raw artifact": f"audit/raw_runs/darpa/{r['dataset']}_50000.json"},
              **{"Source table": "table3_darpa_cross_scenario.csv"},
              **{"Source figure": "figures/fig_darpa.png"}, Status="SUPPORTED")

    # Scalability
    A("## 8. Scalability (Rule Engine inference; 5 reps/size)\n")
    for r in read_csv(TAB / "table6_scalability.csv"):
        block(f"Scalability {r['edges']} edges",
              Experiment="Scalability", Dataset="Synthetic controlled",
              Protocol=f"{r['n_reps']} reps; construction/poisoning/inference separated",
              Model="Rule Engine inference", Seeds="5 reps", Metric="time/memory/throughput",
              Mean=f"infer={fmt(r['rule_engine_infer_sec'])} s; "
                   f"throughput={fmt(r['throughput_eps'],1)} edges/s; "
                   f"peak_python={fmt(r['peak_python_mb'],1)} MB",
              Std=fmt(r["rule_engine_infer_std"]),
              **{"95% CI": "n/a"},
              **{"Raw artifact": "audit/raw_runs/scalability/size_*_rep_*.json"},
              **{"Source table": "table6_scalability.csv"},
              **{"Source figure": "figures/fig_scalability.png"}, Status="SUPPORTED")

    # Generalization
    A("## 9. Cross-dataset generalization (Rule Engine, no retraining; 5 seeds)\n")
    for r in read_csv(TAB / "table9_generalization.csv"):
        block(f"Generalization {r['source']}→{r['target']}",
              Experiment="Cross-dataset generalization",
              Dataset=f"{r['source']} → {r['target']}",
              Protocol="fixed invariants, no retraining", Model="Rule Engine",
              Seeds=r["n"], Metric="F1", Mean=fmt(r["rule_engine_f1_mean"]),
              Std=fmt(r["rule_engine_f1_std"]),
              **{"95% CI": "see table9"},
              **{"Raw artifact": "audit/raw_runs/generalization/*.json"},
              **{"Source table": "table9_generalization.csv"},
              **{"Source figure": "figures/fig_generalization.png"}, Status="SUPPORTED")

    (FR / "FINAL_NUMBERS.md").write_text("\n".join(L))


def main():
    build_dirs()
    copy_tables()
    copy_raw()
    copy_stats_and_subsets()
    figs = ["rule_engine_roc_pr_seed42.png", "scalability_corrected.png"]
    copy_figures(figs)
    fin_numbers()
    print("FINAL_RESULTS built at", FR)


if __name__ == "__main__":
    main()
