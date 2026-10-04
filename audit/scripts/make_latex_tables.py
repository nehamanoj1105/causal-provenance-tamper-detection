"""
Curated LaTeX tables for the manuscripts (booktabs), data pulled from the
verified CSV tables so no number is typed by hand.

Outputs final_manuscripts/{conference,journal}/tables/*.tex and
audit/FINAL_RESULTS/tables/latex/*.tex.
"""
from __future__ import annotations

import csv
from pathlib import Path

FR = Path("audit/FINAL_RESULTS")
CSV = FR / "tables" / "csv"
OUTS = [Path("final_manuscripts/conference/tables"),
        Path("final_manuscripts/journal/tables"),
        FR / "tables" / "latex"]


def rows(name):
    return list(csv.DictReader(open(CSV / f"{name}.csv")))


def f4(v):
    try:
        return f"{float(v):.4f}"
    except Exception:
        return str(v)


def f2(v):
    try:
        return f"{float(v):.2f}"
    except Exception:
        return str(v)


def f1(v):
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return str(v)


def wrap(name, body, caption, label):
    tex = ("\\begin{table*}[t]\n\\centering\n\\small\n"
           f"\\caption{{{caption}}}\n\\label{{{label}}}\n{body}\\end{{table*}}\n")
    for d in OUTS:
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.tex").write_text(tex)


def table1():
    r = rows("table1_dataset_statistics")
    body = ("\\begin{tabular}{lll}\n\\toprule\nDataset & Nodes & Edges \\\\\n\\midrule\n")
    for x in r:
        ds = x["dataset"].replace("&", "\\&")
        body += f"{ds} & {f1(x['nodes'])} & {f1(x['edges'])} \\\\\n"
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table1_dataset_statistics", body,
         "Provenance datasets used and their availability.", "tab:datasets")


def table2():
    r = rows("table2_experimental_protocol")
    body = ("\\begin{tabular}{p{2.6cm}p{2.6cm}p{3.2cm}cp{2.6cm}p{2.4cm}}\n\\toprule\n"
            "Experiment & Dataset & Attacks & Seeds & Detectors & Pos.\\ universe \\\\\n\\midrule\n")
    for x in r:
        body += (f"{x['experiment']} & {x['dataset']} & {x['attacks']} & "
                 f"{x['seeds']} & {x['detectors']} & {x['positive_universe']} \\\\\n")
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table2_experimental_protocol", body,
         "Experimental protocol for every reported experiment.", "tab:protocol")


def table3():
    r = rows("table3_main_detection")
    keep = ["precision", "recall", "f1", "balanced_accuracy", "mcc",
            "specificity", "roc_auc", "pr_auc"]
    disp = {"precision": "Precision", "recall": "Recall", "f1": "F1",
            "balanced_accuracy": "Bal.\\ accuracy", "mcc": "MCC",
            "specificity": "Specificity", "roc_auc": "ROC-AUC", "pr_auc": "PR-AUC"}
    re = {x["metric"]: x for x in r if x["detector"] == "RuleEngine"}
    gs = {x["metric"]: x for x in r if x["detector"] == "GraphSAGE"}
    body = ("\\begin{tabular}{lcccc}\n\\toprule\nMetric & RE mean & RE std & GS mean & GS std \\\\\n\\midrule\n")
    for m in keep:
        body += (f"{disp[m]} & {f4(re[m]['mean'])} & {f4(re[m]['std'])} & "
                 f"{f4(gs[m]['mean'])} & {f4(gs[m]['std'])} \\\\\n")
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table3_main_detection", body,
         "Main detection on synthetic controlled poisoning, 10 seeds "
         "(RE = Rule Engine, GS = GraphSAGE, leakage-free).", "tab:main")


def table4():
    r = rows("table4_statistical_comparison")
    body = ("\\setlength{\\tabcolsep}{4pt}\n"
            "\\begin{tabular}{lccccc}\n\\toprule\n"
            "Metric & $\\Delta$ & 95\\% CI & Cohen $d_z$ & Wilcoxon $p$ & $n$ \\\\\n\\midrule\n")
    for x in r:
        ci = f"[{float(x['ci_low']):.3f}, {float(x['ci_high']):.3f}]"
        name = {"f1": "F1", "roc_auc": "ROC-AUC"}.get(x["metric"], x["metric"].upper())
        body += (f"{name} & {f4(x['mean_diff'])} & {ci} & "
                 f"{f2(x['cohens_dz'])} & {f4(x['wilcoxon_p'])} & {x['n']} \\\\\n")
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table4_statistical_comparison", body,
         "Paired Rule Engine vs GraphSAGE comparison over identical test "
         "instances (10 seeds, Wilcoxon signed-rank).", "tab:significance")


def table5():
    r = rows("table5_cross_dataset")
    body = ("\\begin{tabular}{llcc}\n\\toprule\n"
            "Source & Target & Rule Engine F1 & GraphSAGE F1 \\\\\n\\midrule\n")
    for x in r:
        src = "Synthetic" if x["source"] == "synthetic" else x["source"]
        tgt = "Theia 3" if x["target"] == "theia3" else "Theia 5m"
        body += (f"{src} & {tgt} & {f4(x['rule_engine_f1_mean'])} $\\pm$ "
                 f"{f4(x['rule_engine_f1_std'])} & "
                 f"{f4(x['graphsage_own_model_f1_mean'])} $\\pm$ "
                 f"{f4(x['graphsage_own_model_f1_std'])} \\\\\n")
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table5_cross_dataset", body,
         "Cross-dataset generalization (5 seeds). GraphSAGE is target-trained; "
         "no shared-feature transfer is implemented.", "tab:generalization")


def table6():
    r = rows("table6_mimicry")
    order = ["none", "light", "medium", "heavy"]
    body = ("\\begin{tabular}{llcccc}\n\\toprule\n"
            "Strength & Detector & Prec. & Rec. & F1 ($\\pm$ std) & ROC-AUC \\\\\n\\midrule\n")
    for s in order:
        for det in ["RuleEngine", "GraphSAGE"]:
            x = next(t for t in r if t["strength"] == s and t["detector"] == det)
            d = "RE" if det == "RuleEngine" else "GS"
            body += (f"{s.capitalize()} & {d} & {f4(x['precision_mean'])} & "
                     f"{f4(x['recall_mean'])} & {f4(x['f1_mean'])} $\\pm$ {f4(x['f1_std'])} & "
                     f"{f4(x['roc_auc_mean'])} \\\\\n")
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table6_mimicry", body,
         "Robustness to invariant-preserving mimicry (10 seeds). Noise edges "
         "introduce zero rule self-violations.", "tab:mimicry")


def table7():
    r = rows("table7_rule_ablation")
    keep = ["all_rules", "without_structural", "without_temporal", "without_semantic",
            "loo_ReadWriteConsistencyRule", "loo_NetworkConsistencyRule",
            "loo_SpawnConsistencyRule", "loo_SequenceMonotonicityRule",
            "loo_UnspawnedProcessRule"]
    disp = {"all_rules": "All rules", "without_structural": "w/o structural",
            "without_temporal": "w/o temporal", "without_semantic": "w/o semantic",
            "loo_ReadWriteConsistencyRule": "$-$ReadWrite",
            "loo_NetworkConsistencyRule": "$-$Network",
            "loo_SpawnConsistencyRule": "$-$Spawn",
            "loo_SequenceMonotonicityRule": "$-$SeqMono",
            "loo_UnspawnedProcessRule": "$-$Unspawned"}
    by = {x["variant"]: x for x in r}
    body = ("\\begin{tabular}{lccc}\n\\toprule\nVariant & F1 mean & F1 std & 95\\% CI \\\\\n\\midrule\n")
    for v in keep:
        x = by[v]
        ci = f"[{float(x['ci_low']):.3f}, {float(x['ci_high']):.3f}]"
        body += f"{disp[v]} & {f4(x['mean'])} & {f4(x['std'])} & {ci} \\\\\n"
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table7_rule_ablation", body,
         "Rule-group and leave-one-rule-out ablation (10 seeds).", "tab:ablation")


def table8():
    r = rows("table8_scalability")
    body = ("\\begin{tabular}{rccccc}\n\\toprule\n"
            "Edges & Constr.\\ (s) & Poison (s) & RE infer.\\ (s) & Peak (MB) & Thruput.\\ (e/s) \\\\\n\\midrule\n")
    for x in r:
        body += (f"{f1(x['edges'])} & {f2(x['construction_sec'])} & {f2(x['poisoning_sec'])} & "
                 f"{f2(x['rule_engine_infer_sec'])} & {f2(x['peak_python_mb'])} & "
                 f"{f1(x['throughput_eps'])} \\\\\n")
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table8_scalability", body,
         "Scalability of graph construction, poisoning and Rule Engine inference "
         "(5 repetitions per size).", "tab:scalability")


def table9():
    r = rows("table9_real_data_poisoning")
    body = ("\\begin{tabular}{llcccc}\n\\toprule\n"
            "Dataset & Detector & F1 & Prec. & Rec. & ROC-AUC \\\\\n\\midrule\n")
    for x in r:
        ds = "Theia 3" if x["dataset"] == "theia3" else "Theia 5m"
        det = x["eval_type"].split("_")[-1]
        d = "RE" if det == "rule_engine" else "GS"
        body += (f"{ds} & {d} & {f4(x['f1_mean'])} $\\pm$ {f4(x['f1_std'])} & "
                 f"{f4(x['precision_mean'])} & {f4(x['recall_mean'])} & {f4(x['roc_auc_mean'])} \\\\\n")
    body += "\\bottomrule\n\\end{tabular}\n"
    wrap("table9_real_data_poisoning", body,
         "Real Theia provenance (50k-edge cap) with synthetic post-collection "
         "poisoning (10 seeds). Not real attack labels.", "tab:realpoison")


def main():
    table1(); table2(); table3(); table4(); table5(); table6(); table7(); table8(); table9()
    print("curated LaTeX tables written")


if __name__ == "__main__":
    main()
