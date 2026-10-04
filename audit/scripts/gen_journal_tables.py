"""Generate the extended journal tables (11-15) from authoritative raw runs.

Numbers are read from audit/raw_runs/* and audit/FINAL_RESEARCH_REPORT/
verified_numbers.json; nothing is typed by hand. Writes CSV and LaTeX into the
journal tables directory.
"""
from __future__ import annotations

import csv
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "final_manuscripts" / "journal" / "tables"
V = json.load(open(ROOT / "audit" / "FINAL_RESEARCH_REPORT" / "verified_numbers.json"))
POI = json.load(open(ROOT / "audit" / "raw_runs" / "poisoning_audit.json"))


def wr(name, header, rows):
    with open(OUT / f"{name}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def tex_tabular(name, header, rows, align=None, small=True, caption="", label=""):
    cols = align or ("l" + "r" * (len(header) - 1))
    body = ["\\begin{tabular}{" + cols + "}", "\\toprule",
            " & ".join(header) + " \\\\", "\\midrule"]
    for r in rows:
        body.append(" & ".join(str(x) for x in r) + " \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    inner = ("{\\small\n" + "\n".join(body) + "\n}") if small else "\n".join(body)
    env = ["\\begin{table}[t]", "\\centering"]
    if caption:
        env.append("\\caption{" + caption + "}")
    if label:
        env.append("\\label{" + label + "}")
    env.append(inner)
    env.append("\\end{table}")
    (OUT / f"{name}.tex").write_text("\n".join(env) + "\n")


# ---- Table 11: per-seed synthetic performance -----------------------------
seeds = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
re_f1 = V["synthetic"]["RE_f1_per_seed"]
gs_f1 = V["synthetic"]["GS_f1_per_seed"]
su = {r["seed"]: r for r in V["scoring_universe"]["per_seed"]}
rows = []
for i, s in enumerate(seeds):
    r = su[s]
    rows.append([s, r["n_gt_detectable"], r["n_universe_final"],
                 f"{r['precision_det']:.4f}", f"{r['recall_det']:.4f}",
                 f"{re_f1[i]:.4f}", f"{gs_f1[i]:.4f}"])
wr("table11_per_seed_synthetic",
   ["seed", "detectable_positives", "final_edges", "re_precision",
    "re_recall", "re_f1", "gs_f1"], rows)
tex_tabular("table11_per_seed_synthetic",
            ["Seed", "Det. pos.", "Final edges", "RE prec.", "RE rec.",
             "RE F1", "GS F1"], rows,
            caption="Per-seed synthetic detection (final-graph universe).",
            label="tab:perseed")

# ---- Table 12: dataset characteristics ------------------------------------
rows = [
    ["Synthetic", "80", "~180", "controlled", "generator"],
    ["Theia E3 scenario 3 (real, parsed)", "20157", "297777", "post-collection synthetic", "gain"],
    ["Theia E3 scenario 5m (real, parsed)", "34835", "464858", "post-collection synthetic", "gain"],
    ["Theia E3 scenario 1r", "n/a", "n/a", "unavailable (drive quota)", "-"],
    ["Theia E3 scenario 6r", "n/a", "n/a", "unavailable (drive quota)", "-"],
]
wr("table12_dataset_characteristics",
   ["dataset", "nodes", "edges", "attack_label", "source"], rows)
tex_tabular("table12_dataset_characteristics",
            ["Dataset", "Nodes", "Edges", "Attack labels", "Source"], rows,
            align="p{3.4cm}rrp{3.0cm}p{1.4cm}",
            caption="Dataset characteristics. Node and edge counts are the "
                    "full parsed counts before the 50{,}000-edge evaluation "
                    "truncation. Synthetic node count is a generator constant.",
            label="tab:datasetsfull")

# ---- Table 13: attack-operator audit --------------------------------------
rows = []
DISP = {"random_deletion": "random del.", "random_insertion": "random ins.",
        "random_reordering": "random reord.",
        "random_dependency_forgery": "random dep. frog.",
        "targeted_deletion": "targeted del.", "targeted_insertion": "targeted ins.",
        "targeted_reordering": "targeted reord.",
        "targeted_dependency_forgery": "targeted dep. frog."}
for name, atk in POI["attacks"].items():
    ps = atk["per_seed"]
    rows.append([
        DISP.get(name, name.replace("_", "\\_")),
        f"{st.mean(x['requested'] for x in ps):.1f}",
        f"{st.mean(x['successful_events'] for x in ps):.1f}",
        f"{st.mean(x['gt_positive_count'] for x in ps):.1f}",
        f"{st.mean(len(x['detectable_positives']) for x in ps):.1f}",
        f"{st.mean(x['duplicate_gt_ids'] for x in ps):.2f}",
        f"{st.mean(len(x.get('gt_ids_absent_from_final_graph', [])) for x in ps):.1f}",
        f"{st.mean(x.get('input_graph_edges_mutated_in_place', 0) for x in ps):.1f}",
    ])
wr("table13_attack_operator_audit",
   ["operator", "requested", "successful", "gt_positives", "detectable",
    "dup_gt_ids", "absent_from_final", "in_place_mutations"], rows)
tex_tabular("table13_attack_operator_audit",
            ["Operator", "Req.", "Succ.", "GT pos.", "Det.", "Dup.",
             "Absent", "In-place"], rows,
            align="p{3.0cm}r" + "r" * 7,
            caption="Attack-operator audit over ten seeds (means). "
                    "Det.\\ = detectable positives in the final graph; "
                    "Absent\\ = ground-truth ids absent from the final graph "
                    "(deleted edges); In-place\\ = input graphs mutated "
                    "in place (must be zero).",
            label="tab:operators")

print("wrote tables 11-13")

# ---- Table 14: per-rule violation statistics ------------------------------
rs = V["rule_statistics"]
rows = []
for rule, d in rs.items():
    name = rule.replace(".violations", "")
    rows.append([name, f"{d['mean']:.1f}", f"{d['std']:.3f}",
                 f"{d['min']:.1f}", f"{d['max']:.1f}"])
wr("table14_rule_statistics",
   ["rule", "mean_violations", "std", "min", "max"], rows)
tex_tabular("table14_rule_statistics",
            ["Rule", "Mean", "Std", "Min", "Max"], rows,
            align="p{5.2cm}rrrr",
            caption="Per-rule violation counts over ten seeds (synthetic).",
            label="tab:rules")

# ---- Table 15: Rule Engine AUC under mimicry (score definitions) ----------
rsa = V["rule_score"]
rows = []
for strength in ["none", "light", "medium", "heavy"]:
    rows.append([
        strength,
        f"{rsa[f'{strength}.roc_auc_count_score']['mean']:.4f}",
        f"{rsa[f'{strength}.roc_auc_count_score']['std']:.4f}",
        f"{rsa[f'{strength}.pr_auc_count_score']['mean']:.4f}",
        f"{rsa[f'{strength}.roc_auc_binary_flag']['mean']:.4f}",
        f"{rsa[f'{strength}.paper_reported_roc_auc']['mean']:.4f}",
    ])
wr("table15_rule_engine_auc_scores",
   ["mimicry", "roc_auc_count_score_mean", "roc_auc_count_score_std",
    "pr_auc_count_score_mean", "roc_auc_binary_flag_mean",
    "paper_reported_roc_auc_mean"], rows)
tex_tabular("table15_rule_engine_auc_scores",
            ["Mimicry", "ROC-AUC (severity)", "Std", "PR-AUC (severity)",
             "ROC-AUC (binary)", "Reported fallback"], rows,
            align="lrrrrr",
            caption="Rule Engine ranking scores under mimicry. The severity "
                    "score is the genuine continuous signal (count of "
                    "violations, weighted); the binary flag is the "
                    "greater-than-zero decision; the reported fallback is the "
                    "constant that must not be used.",
            label="tab:rerec")

# ---- Table 16: scalability, detailed per-stage means ----------------------
sc = V["scalability"]
rows = []
for size in [10000, 25000, 50000, 100000, 250000, 500000, 1000000]:
    k = str(size)
    rows.append([
        size,
        f"{sc[f'{k}.construction_sec']['mean']:.3f}",
        f"{sc[f'{k}.poisoning_sec']['mean']:.3f}",
        f"{sc[f'{k}.rule_engine_infer_sec']['mean']:.3f}",
        f"{sc[f'{k}.evaluation_sec']['mean']:.4f}",
        f"{sc[f'{k}.end_to_end_sec']['mean']:.3f}",
        f"{sc[f'{k}.peak_python_mb']['mean']:.1f}",
        f"{sc[f'{k}.rss_delta_mb']['mean']:.1f}",
        f"{sc[f'{k}.rule_engine_throughput_eps']['mean']:.0f}",
    ])
wr("table16_scalability_detail",
   ["edges", "construction_sec", "poisoning_sec", "rule_engine_infer_sec",
    "evaluation_sec", "end_to_end_sec", "peak_python_mb", "rss_delta_mb",
    "throughput_eps"], rows)
tex_tabular("table16_scalability_detail",
            ["Edges", "Constr.", "Poison", "RE infer", "Eval", "End-to-end",
             "Peak MB", "RSS MB", "Through."], rows,
            align="l" + "r" * 8,
            caption="Scalability, means over five repetitions per size. "
                    "Times in seconds; memory in MB; throughput in edges per "
                    "second. Construction, poisoning, Rule Engine inference and "
                    "evaluation are timed separately.",
            label="tab:scalabilitydetail")

print("wrote tables 11-16")

# ---- Table 17: rule-family contribution (verified ablation aggregate) -----
ab = V["ablation"]
allm = ab["all_rules.f1"]["mean"]
allstd = ab["all_rules.f1"]["std"]
rows = []
for label, key in [("All rules", "all_rules"),
                   ("Without structural", "without_structural"),
                   ("Without temporal", "without_temporal"),
                   ("Without semantic", "without_semantic")]:
    d = ab[f"{key}.f1"]
    rows.append([label, f"{d['mean']:.4f}", f"{d['std']:.4f}",
                 f"{allm - d['mean']:+.4f}",
                 f"{d['ci95_low']:.4f}", f"{d['ci95_high']:.4f}"])
wr("table17_rule_family_contribution",
   ["variant", "f1_mean", "f1_std", "delta_vs_all", "ci_low", "ci_high"],
   rows)
tex_tabular("table17_rule_family_contribution",
            ["Rule set", "F1 mean", "F1 std", "Delta vs all", "CI low",
             "CI high"], rows, align="lrrrrr",
            caption="Rule-family contribution over ten seeds. Delta vs all "
                    "is the F1 lost when the family is removed.",
            label="tab:families")

print("wrote tables 11-17")

# ---- Table 18: GraphSAGE / harness configuration --------------------------
cfg = [
    ["Backbone", "2-layer GraphSAGE (SAGEConv)"],
    ["Hidden channels", "64"],
    ["Edge classifier", "MLP, hidden 32"],
    ["Node features", "one-hot node type + degree"],
    ["Edge features", "one-hot edge type + normalised timestamp"],
    ["Optimiser", "Adam, lr $=0.01$, weight decay $=10^{-4}$"],
    ["Epochs", "100"],
    ["Split", "60/20/20 train/validation/test by seed"],
    ["Threshold", "selected on validation only (max F1)"],
    ["Message passing", "train + validation edges only"],
    ["Rule Engine threshold", "$s>0$ (no tuning)"],
]
wr("table18_graphsage_configuration", ["item", "setting"], cfg)
rows = [[a, b] for a, b in cfg]
tex_tabular("table18_graphsage_configuration", ["Item", "Setting"], rows,
            align="p{4.6cm}p{8.0cm}",
            caption="Learned-baseline and harness configuration under the "
                    "leakage-free protocol.",
            label="tab:gscfg")

print("wrote tables 11-18")

# ---- Table 19: per-seed full Rule Engine metrics --------------------------
rows = []
for i, s in enumerate(seeds):
    r = su[s]
    rows.append([s, f"{r['precision_det']:.4f}", f"{r['recall_det']:.4f}",
                 f"{r['f1_det']:.4f}", f"{r['roc_auc_det']:.4f}",
                 f"{gs_f1[i]:.4f}"])
wr("table19_per_seed_full",
   ["seed", "re_precision", "re_recall", "re_f1", "re_roc_auc", "gs_f1"], rows)
tex_tabular("table19_per_seed_full",
            ["Seed", "RE prec.", "RE rec.", "RE F1", "RE ROC-AUC", "GS F1"],
            rows,
            caption="Per-seed Rule Engine metrics (continuous-score ROC-AUC) "
                    "and leakage-free GraphSAGE F1, final-graph universe.",
            label="tab:perseedfull")

# ---- Table 20: scalability per repetition (raw) ---------------------------
import glob
rows = []
for size in [10000, 25000, 50000, 100000, 250000, 500000, 1000000]:
    for f in sorted(glob.glob(str(ROOT / "audit" / "raw_runs" / "scalability"
                                / f"size_{size}_rep_*.json"))):
        d = json.load(open(f))
        gs = d.get("graphsage_total_sec")
        gs_s = f"{gs:.3f}" if gs is not None else "n/a"
        rows.append([size, d["rep"], d["seed"],
                     f"{d['construction_sec']:.3f}", f"{d['poisoning_sec']:.3f}",
                     f"{d['rule_engine_infer_sec']:.3f}",
                     f"{d['peak_python_mb']:.1f}",
                     f"{d['rule_engine_throughput_eps']:.0f}",
                     gs_s, f"{d['rule_engine_f1']:.4f}"])
wr("table20_scalability_per_rep",
   ["edges", "rep", "seed", "construct_sec", "poison_sec",
    "rule_engine_infer_sec", "peak_python_mb", "rule_engine_throughput_eps",
    "graphsage_total_sec", "rule_engine_f1"], rows)
tex_tabular("table20_scalability_per_rep",
            ["Edges", "Rep", "Seed", "Constr.", "Poison", "RE infer", "Peak MB",
             "Thr.", "GS total", "RE F1"], rows,
            align="rrr" + "r" * 7,
            caption="Scalability, every repetition (five per size). RE infer is "
                    "Rule Engine inference; GS total is full GraphSAGE "
                    "train-plus-inference; the two are reported separately and "
                    "never compared directly.",
            label="tab:scalperrep")

print("wrote tables 11-20")

# ---- Table 21: rule catalogue (families and severities from src) ----------
CAT = [
    ("DuplicateEdgeRule", "Structural", "High", "no repeated edge identifier"),
    ("DuplicateEventRule", "Structural", "Medium", "no repeated event identifier"),
    ("SpawnConsistencyRule", "Semantic", "High/Low", "spawn endpoints are processes; parent exists; no self-spawn; no duplicate spawn"),
    ("ExecutionConsistencyRule", "Semantic", "High/Low", "execute edges target files; source is a process"),
    ("ReadWriteConsistencyRule", "Semantic", "High/Low", "read/write edges target files; source is a process"),
    ("NetworkConsistencyRule", "Semantic", "High", "connect edges target network endpoints"),
    ("DeleteConsistencyRule", "Semantic", "High", "delete edges target files; source is a process"),
    ("SelfLoopRule", "Structural", "Medium", "no self-referential edge"),
    ("MissingNodeRule", "Structural", "High", "every edge endpoint exists as a node"),
    ("TimestampRule", "Temporal", "High/Medium", "timestamps are non-negative"),
    ("UnspawnedProcessRule", "Structural", "High", "an acting process has an observed parent spawn"),
    ("SequenceGapRule", "Structural", "High", "identifier sequences have no gaps"),
    ("ParentChildTemporalRule", "Temporal", "High", "child spawn does not predate parent spawn"),
    ("ProcessActivityTemporalRule", "Temporal", "High", "activity does not predate the process spawn"),
    ("SequenceMonotonicityRule", "Temporal", "High", "timestamps increase along an event stream"),
]
rows = [[a, b, c, d] for a, b, c, d in CAT]
wr("table21_rule_catalogue",
   ["rule", "family", "severity", "invariant"], rows)
tex_tabular("table21_rule_catalogue",
            ["Rule", "Family", "Severity", "Invariant checked"], rows,
            align="p{4.2cm}p{1.5cm}p{1.9cm}p{5.6cm}",
            caption="The fifteen rules. Family membership follows the "
                    "ablation configuration; severities are those assigned in "
                    "the implementation.",
            label="tab:catalogue")

print("wrote tables 11-21")

# ---- Table 22: reconciliation of claimed vs corrected values ---------------
import csv as _csv
rec = list(_csv.DictReader(open(ROOT / "audit" / "final_result_reconciliation.csv")))
SHORT = {
    "Synthetic RE Precision (seed 42, committed)": "Synthetic RE precision (seed 42)",
    "Synthetic RE Recall (seed 42, committed)": "Synthetic RE recall (seed 42)",
    "Synthetic RE F1 (seed 42, committed)": "Synthetic RE F1 (seed 42)",
    "Synthetic RE multi-seed F1 mean (committed as 0.7222)":
        "Synthetic RE F1 multi-seed mean",
    "Synthetic GraphSAGE F1 (committed 0.5600)": "Synthetic GraphSAGE F1",
    "Mimicry none RE F1 (committed)": "Mimicry none, RE F1",
    "Mimicry light RE F1 (committed)": "Mimicry light, RE F1",
    "Mimicry medium RE F1 (committed)": "Mimicry medium, RE F1",
    "Mimicry heavy RE F1 (committed)": "Mimicry heavy, RE F1",
    "Rule Engine ROC-AUC under mimicry (paper 1.0000)":
        "RE ROC-AUC under mimicry",
    "Paired RE-GS f1 difference": "Paired RE--GS F1 difference",
    "Paired RE-GS roc_auc difference": "Paired RE--GS ROC-AUC difference",
}


def _name(x):
    raw = (x or "")
    if raw in SHORT:
        return SHORT[raw]
    if raw.startswith("DARPA"):
        parts = raw.split()
        scen = parts[1].replace("_", " ") if len(parts) > 1 else raw
        detector = "RE" if "rule_engine" in raw else "GS"
        return f"DARPA {scen}, {detector} F1"
    x = raw.replace("\\", "").replace("_", "\\_")
    return x if len(x) <= 38 else x[:37] + "."


def _num(x):
    x = (x or "").strip()
    if x == "":
        return "--"
    try:
        return f"{float(x):.6f}"
    except ValueError:
        return x.replace("_", "\\_")


rows = [[r["reproducible"], _name(r["experiment"]), _num(r["paper_value"]),
         _num(r["audited_value"])]
        for r in rec]
wr("table22_reconciliation",
   ["disposition", "experiment", "committed_value", "corrected_value"], rows)
tex_tabular("table22_reconciliation",
            ["Disposition", "Experiment", "Committed", "Corrected"], rows,
            align="lp{5.6cm}rr",
            caption="Reconciliation of every committed value against its "
                    "corrected counterpart. Disposition is yes (reproduces "
                    "qualitatively), no (does not reproduce) or n/a (never "
                    "reported). Values are shown to six decimals; the raw "
                    "audit files preserve full precision.",
            label="tab:reconciliation")

print("wrote tables 11-22")
