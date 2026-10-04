"""
CORRECTED multi-seed evaluation with an explicit train/validation/test split.

Protocol (no test leakage):
  For each seed s:
    base        = synthetic graph (seed=s)
    train_inst  = inject_poisoning(base, seed=f(s,1))   # weights trained here
    val_inst    = inject_poisoning(base, seed=f(s,2))   # threshold chosen here
    test_inst   = inject_poisoning(base, seed=f(s,3))   # metrics reported here

  GraphSAGE:
    * weights  <- train_inst labels only
    * threshold<- val_inst labels only (max F1)
    * metrics  <- test_inst, using the validation threshold
  Rule Engine:
    * deterministic; no training. Evaluated on test_inst.
    * continuous score = #distinct rule violations per edge (for ROC-AUC/PR-AUC).

Also records the repo's ORIGINAL (leaky) protocol for the same seeds, where the
model trains and the threshold is tuned on the same graph that is scored.

Writes:
  audit/raw_runs/corrected_multiseed.json
  audit/raw_runs/corrected_multiseed_per_seed.csv
  audit/raw_runs/paired_stats.json
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import average_precision_score, matthews_corrcoef, roc_auc_score

from src.detection.poisoning_injection import inject_poisoning
from src.detection.rule_based import run_all_checks
from src.detection.rule_engine import default_rule_engine
from src.eval.metrics import (
    accuracy, balanced_accuracy, f1_score, false_negative_rate,
    false_positive_rate, precision, recall, specificity,
)
from src.graph_construction.synthetic import generate_synthetic_graph
from src.ml.dataset import provenance_to_pyg_data
from src.ml.graphsage import GraphSAGEForTamperDetection
from src.ml.train import FocalLoss, train_pipeline
from src.ml.utils import get_device, set_seed

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
INTENSITY = 5
EPOCHS = 30
LR = 0.01
HIDDEN = 64


def seed3(s, k):
    return s * 131 + k * 17 + 3


def full_metrics(y_true, y_pred, y_score=None):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    p = precision(tp, fp)
    r = recall(tp, fn)
    f1 = f1_score(precision_val=p, recall_val=r)
    acc = accuracy(tp, fp, tn, fn)
    fpr = false_positive_rate(fp, tn)
    fnr = false_negative_rate(fn, tp)
    spec = specificity(tn, fp)
    bacc = balanced_accuracy(tp, fp, tn, fn)
    mcc = float(matthews_corrcoef(y_true, y_pred)) if len(np.unique(y_true)) > 1 and len(np.unique(y_pred)) > 1 else 0.0
    roc = None
    pr = None
    if y_score is not None and len(np.unique(y_true)) > 1 and len(np.unique(y_score)) > 1:
        roc = float(roc_auc_score(y_true, y_score))
        pr = float(average_precision_score(y_true, y_score))
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": p, "recall": r, "f1": f1, "accuracy": acc,
        "balanced_accuracy": bacc, "mcc": mcc, "fpr": fpr, "fnr": fnr,
        "specificity": spec, "roc_auc": roc, "pr_auc": pr,
    }


def rule_engine_metrics(graph, gt_ids):
    violations = run_all_checks(graph)
    counts = {}
    for v in violations:
        if v.edge_id:
            counts[v.edge_id] = counts.get(v.edge_id, 0) + 1
    edge_ids = [e.edge_id for e in graph.edges]
    y_true = [1 if eid in gt_ids else 0 for eid in edge_ids]
    y_score = [float(counts.get(eid, 0)) for eid in edge_ids]
    y_pred = [1 if s > 0 else 0 for s in y_score]
    return full_metrics(y_true, y_pred, y_score)


def train_graphsage_clean(train_data, val_data, test_data, seed):
    set_seed(seed)
    device = get_device()
    model = GraphSAGEForTamperDetection(in_channels=train_data.x.size(1), hidden_channels=HIDDEN).to(device)
    num_pos = float((train_data.edge_label == 1).sum().item())
    num_neg = float((train_data.edge_label == 0).sum().item())
    pos_w = torch.tensor([num_neg / max(1.0, num_pos)], device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_w)
    opt = optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    for _ in range(EPOCHS):
        model.train()
        opt.zero_grad()
        _, logits, _ = model(train_data.x.to(device), train_data.edge_index.to(device))
        loss = criterion(logits, train_data.edge_label.to(device))
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        _, vlog, _ = model(val_data.x.to(device), val_data.edge_index.to(device))
        vprob = torch.sigmoid(vlog).cpu().numpy()
    vy = val_data.edge_label.cpu().numpy()
    best_t, best_f1 = 0.5, -1.0
    for t in np.arange(0.05, 1.001, 0.05):
        pred = (vprob >= t).astype(int)
        tp = int(((vy == 1) & (pred == 1)).sum()); fp = int(((vy == 0) & (pred == 1)).sum())
        fn = int(((vy == 1) & (pred == 0)).sum())
        p = precision(tp, fp); r = recall(tp, fn)
        f = f1_score(precision_val=p, recall_val=r)
        if f > best_f1:
            best_f1, best_t = f, float(t)

    with torch.no_grad():
        _, tlog, _ = model(test_data.x.to(device), test_data.edge_index.to(device))
        tprob = torch.sigmoid(tlog).cpu().numpy()
    ty = test_data.edge_label.cpu().numpy()
    tpred = (tprob >= best_t).astype(int)
    m = full_metrics(ty, tpred, tprob)
    m["threshold"] = best_t
    return m


def main():
    out = {"protocol": "clean train/val/test", "seeds": SEEDS, "intensity": INTENSITY,
           "epochs": EPOCHS, "lr": LR, "hidden": HIDDEN, "per_seed": [], "original_leaky": []}

    for s in SEEDS:
        base = generate_synthetic_graph(num_processes=30, num_files=40, num_network=10, seed=s)
        tr = inject_poisoning(base, INTENSITY, INTENSITY, INTENSITY, INTENSITY, seed=seed3(s, 1))
        va = inject_poisoning(base, INTENSITY, INTENSITY, INTENSITY, INTENSITY, seed=seed3(s, 2))
        te = inject_poisoning(base, INTENSITY, INTENSITY, INTENSITY, INTENSITY, seed=seed3(s, 3))

        te_gt = {ev.edge_id for ev in te.events}
        re_m = rule_engine_metrics(te.graph, te_gt)

        tr_d = provenance_to_pyg_data(tr.graph, poisoning_result=tr)
        va_d = provenance_to_pyg_data(va.graph, poisoning_result=va)
        te_d = provenance_to_pyg_data(te.graph, poisoning_result=te)
        gs_m = train_graphsage_clean(tr_d, va_d, te_d, s)

        # ORIGINAL leaky protocol: train + threshold on the same test instance
        set_seed(s)
        _, orig_metrics, orig_thresh, _, _ = train_pipeline(
            te_d, epochs=EPOCHS, lr=LR, hidden_channels=HIDDEN, seed=s,
            checkpoint_path=ROOT / "audit" / "raw_runs" / f"chk_{s}.pt",
        )
        out["per_seed"].append({"seed": s, "rule_engine": re_m, "graphsage_clean": gs_m})
        out["original_leaky"].append({
            "seed": s, "threshold": orig_thresh,
            "precision": orig_metrics.precision, "recall": orig_metrics.recall,
            "f1": orig_metrics.f1, "accuracy": orig_metrics.accuracy,
            "roc_auc": orig_metrics.roc_auc, "pr_auc": orig_metrics.pr_auc,
            "mcc": orig_metrics.mcc,
        })
        print(f"seed {s:4d}  RE F1={re_m['f1']:.4f} ROC={re_m['roc_auc']:.4f} | "
              f"GS(clean) F1={gs_m['f1']:.4f} ROC={gs_m['roc_auc']:.4f} tau={gs_m['threshold']:.2f} | "
              f"GS(leaky) F1={orig_metrics.f1:.4f}")

    # summary stats
    def summarize(key, metric):
        vals = [r[key][metric] for r in out["per_seed"] if r[key][metric] is not None]
        a = np.array(vals, dtype=float)
        if len(a) == 0:
            return {}
        n = len(a)
        mean = float(a.mean())
        std = float(a.std(ddof=1)) if n > 1 else 0.0
        se = std / np.sqrt(n) if n > 0 else 0.0
        return {
            "n": n, "mean": mean, "std": std, "median": float(np.median(a)),
            "min": float(a.min()), "max": float(a.max()),
            "ci95_low": mean - 1.96 * se, "ci95_high": mean + 1.96 * se,
            "values": vals,
        }

    metrics = ["precision", "recall", "f1", "accuracy", "balanced_accuracy", "mcc",
               "fpr", "fnr", "specificity", "roc_auc", "pr_auc"]
    out["summary"] = {
        "rule_engine": {m: summarize("rule_engine", m) for m in metrics},
        "graphsage_clean": {m: summarize("graphsage_clean", m) for m in metrics},
        "graphsage_original_leaky": {
            m: {
                "n": len(out["original_leaky"]),
                "mean": float(np.mean([r[m] for r in out["original_leaky"]])),
                "std": float(np.std([r[m] for r in out["original_leaky"]], ddof=1)),
                "values": [r[m] for r in out["original_leaky"]],
            }
            for m in ["precision", "recall", "f1", "accuracy", "roc_auc", "pr_auc", "mcc"]
        },
    }

    # paired comparison on identical test instances
    re_f1 = np.array([r["rule_engine"]["f1"] for r in out["per_seed"]])
    gs_f1 = np.array([r["graphsage_clean"]["f1"] for r in out["per_seed"]])
    diff = re_f1 - gs_f1
    paired = {
        "n": len(diff),
        "rule_engine_f1": re_f1.tolist(),
        "graphsage_clean_f1": gs_f1.tolist(),
        "paired_difference_re_minus_gs": diff.tolist(),
        "mean_difference": float(diff.mean()),
        "std_difference": float(diff.std(ddof=1)),
        "ci95_low": float(diff.mean() - 1.96 * diff.std(ddof=1) / np.sqrt(len(diff))),
        "ci95_high": float(diff.mean() + 1.96 * diff.std(ddof=1) / np.sqrt(len(diff))),
    }
    try:
        from scipy.stats import wilcoxon, ttest_rel
        if np.any(diff != 0):
            w = wilcoxon(re_f1, gs_f1)
            paired["wilcoxon_statistic"] = float(w.statistic)
            paired["wilcoxon_pvalue"] = float(w.pvalue)
        t = ttest_rel(re_f1, gs_f1)
        paired["ttest_statistic"] = float(t.statistic)
        paired["ttest_pvalue"] = float(t.pvalue)
        # Cohen's dz
        paired["cohens_dz"] = float(diff.mean() / diff.std(ddof=1)) if diff.std(ddof=1) > 0 else 0.0
    except Exception as e:
        paired["stats_error"] = str(e)
    out["paired_stats"] = paired

    outdir = ROOT / "audit" / "raw_runs"
    with open(outdir / "corrected_multiseed.json", "w") as f:
        json.dump(out, f, indent=2)

    with open(outdir / "corrected_multiseed_per_seed.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "detector", "tp", "fp", "tn", "fn", "precision", "recall", "f1",
                    "accuracy", "balanced_accuracy", "mcc", "fpr", "fnr", "specificity",
                    "roc_auc", "pr_auc", "threshold"])
        for r in out["per_seed"]:
            for det in ["rule_engine", "graphsage_clean"]:
                m = r[det]
                w.writerow([r["seed"], det, m["tp"], m["fp"], m["tn"], m["fn"],
                            m["precision"], m["recall"], m["f1"], m["accuracy"],
                            m["balanced_accuracy"], m["mcc"], m["fpr"], m["fnr"],
                            m["specificity"], m["roc_auc"], m["pr_auc"],
                            m.get("threshold", "")])

    print("\nPaired RE-GS F1 diff mean=%.4f  p(wilcoxon)=%s" % (
        paired["mean_difference"], paired.get("wilcoxon_pvalue")))
    print("Wrote", outdir / "corrected_multiseed.json")


if __name__ == "__main__":
    main()
