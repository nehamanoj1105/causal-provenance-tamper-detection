"""Statistically rigorous metric utilities for the corrected audit.

All values are kept at full float precision; rounding only happens at the
presentation layer (journal tables), never here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    matthews_corrcoef,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)


@dataclass
class Metrics:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    accuracy: float = 0.0
    balanced_accuracy: float = 0.0
    mcc: float = 0.0
    fpr: float = 0.0
    fnr: float = 0.0
    specificity: float = 0.0
    roc_auc: float | None = None
    pr_auc: float | None = None
    avg_precision: float | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def compute_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    y_score: Sequence[float] | None = None,
) -> Metrics:
    """Confusion-matrix metrics. ROC/PR-AUC only when a genuine continuous
    `y_score` is supplied AND both classes are present."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))

    def div(a, b):
        return float(a) / float(b) if b else 0.0

    prec = div(tp, tp + fp)
    rec = div(tp, tp + fn)
    f1 = div(2 * prec * rec, prec + rec)
    acc = div(tp + tn, tp + fp + tn + fn)
    spec = div(tn, tn + fp)
    bacc = (rec + spec) / 2.0
    fpr = div(fp, fp + tn)
    fnr = div(fn, fn + tp)
    try:
        mcc = float(matthews_corrcoef(y_true, y_pred)) if len(y_true) else 0.0
    except Exception:
        mcc = 0.0

    roc = pr = ap = None
    if y_score is not None:
        ys = np.asarray(y_score, dtype=float)
        if len(np.unique(y_true)) == 2:
            roc = float(roc_auc_score(y_true, ys))
            ap = float(average_precision_score(y_true, ys))
            pr = ap
        else:
            roc = None
            pr = None
            ap = None

    return Metrics(tp, fp, tn, fn, prec, rec, f1, acc, bacc, mcc, fpr, fnr, spec, roc, pr, ap)


def roc_pr_curves(y_true, y_score):
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    if len(np.unique(y_true)) < 2:
        return None
    fpr, tpr, _ = roc_curve(y_true, y_score)
    prec, rec, _ = precision_recall_curve(y_true, y_score)
    return {"roc": (fpr.tolist(), tpr.tolist()), "pr": (rec.tolist(), prec.tolist())}


def summarize(values: Sequence[float]) -> dict:
    """mean, sample std (ddof=1), median, min, max, 95% CI (t-based)."""
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    n = len(arr)
    if n == 0:
        return {"n": 0, "mean": None, "std": None, "median": None,
                "min": None, "max": None, "ci95_low": None, "ci95_high": None}
    mean = float(np.mean(arr))
    if n == 1:
        return {"n": 1, "mean": mean, "std": 0.0, "median": mean,
                "min": mean, "max": mean, "ci95_low": None, "ci95_high": None}
    std = float(np.std(arr, ddof=1))
    se = std / math.sqrt(n)
    try:
        from scipy import stats
        tcrit = float(stats.t.ppf(0.975, df=n - 1))
    except Exception:
        tcrit = 1.96
    return {
        "n": n, "mean": mean, "std": std,
        "median": float(np.median(arr)),
        "min": float(np.min(arr)), "max": float(np.max(arr)),
        "ci95_low": mean - tcrit * se, "ci95_high": mean + tcrit * se,
    }


def paired_stats(a: Sequence[float], b: Sequence[float]) -> dict:
    """Paired comparison of two matched per-seed sequences."""
    from scipy import stats
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = a - b
    n = len(d)
    out = {"n": int(n), "mean_diff": float(np.mean(d)),
           "median_diff": float(np.median(d))}
    if n >= 2:
        sd = float(np.std(d, ddof=1))
        se = sd / math.sqrt(n)
        tcrit = float(stats.t.ppf(0.975, df=n - 1))
        out["std_diff"] = sd
        out["ci95_low"] = float(np.mean(d) - tcrit * se)
        out["ci95_high"] = float(np.mean(d) + tcrit * se)
        out["cohens_dz"] = float(np.mean(d) / sd) if sd > 0 else 0.0
        if np.allclose(d, 0):
            out["wilcoxon_stat"] = None
            out["wilcoxon_p"] = None
        else:
            try:
                stat, p = stats.wilcoxon(a, b, zero_method="wilcox")
                out["wilcoxon_stat"] = float(stat)
                out["wilcoxon_p"] = float(p)
            except Exception as e:
                out["wilcoxon_stat"] = None
                out["wilcoxon_p"] = None
                out["wilcoxon_error"] = str(e)
    return out
