"""
Metric calculations for provenance graph tamper detection evaluation.

Implements core binary classification evaluation metrics with divide-by-zero protection:
- Precision
- Recall
- F1 Score
- Accuracy
- False Positive Rate (FPR)
- False Negative Rate (FNR)
- Specificity (True Negative Rate)
- Balanced Accuracy
- Multi-seed statistical aggregation (mean & standard deviation)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from src.graph_construction.schema import ProvenanceGraph


@dataclass
class MetricResult:
    """Dataclass storing calculated evaluation metrics."""

    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    accuracy: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    specificity: float = 0.0
    balanced_accuracy: float = 0.0

    @property
    def f1_score(self) -> float:
        """Alias for f1."""
        return self.f1

    def to_dict(self) -> dict[str, float]:
        """Convert metrics to dictionary."""
        return {
            "precision": round(self.precision, 6),
            "recall": round(self.recall, 6),
            "f1": round(self.f1, 6),
            "accuracy": round(self.accuracy, 6),
            "false_positive_rate": round(self.false_positive_rate, 6),
            "false_negative_rate": round(self.false_negative_rate, 6),
            "specificity": round(self.specificity, 6),
            "balanced_accuracy": round(self.balanced_accuracy, 6),
        }


@dataclass
class SeedStatistics:
    """Dataclass storing mean and standard deviation across multiple random seeds."""

    precision_mean: float = 0.0
    precision_std: float = 0.0
    recall_mean: float = 0.0
    recall_std: float = 0.0
    f1_mean: float = 0.0
    f1_std: float = 0.0
    accuracy_mean: float = 0.0
    accuracy_std: float = 0.0
    false_positive_rate_mean: float = 0.0
    false_positive_rate_std: float = 0.0
    false_negative_rate_mean: float = 0.0
    false_negative_rate_std: float = 0.0
    specificity_mean: float = 0.0
    specificity_std: float = 0.0
    balanced_accuracy_mean: float = 0.0
    balanced_accuracy_std: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert seed statistics to dictionary."""
        return {
            "precision_mean": round(self.precision_mean, 6),
            "precision_std": round(self.precision_std, 6),
            "recall_mean": round(self.recall_mean, 6),
            "recall_std": round(self.recall_std, 6),
            "f1_mean": round(self.f1_mean, 6),
            "f1_std": round(self.f1_std, 6),
            "accuracy_mean": round(self.accuracy_mean, 6),
            "accuracy_std": round(self.accuracy_std, 6),
            "false_positive_rate_mean": round(self.false_positive_rate_mean, 6),
            "false_positive_rate_std": round(self.false_positive_rate_std, 6),
            "false_negative_rate_mean": round(self.false_negative_rate_mean, 6),
            "false_negative_rate_std": round(self.false_negative_rate_std, 6),
            "specificity_mean": round(self.specificity_mean, 6),
            "specificity_std": round(self.specificity_std, 6),
            "balanced_accuracy_mean": round(self.balanced_accuracy_mean, 6),
            "balanced_accuracy_std": round(self.balanced_accuracy_std, 6),
        }


def precision(tp: int, fp: int) -> float:
    """
    Computes precision: TP / (TP + FP).
    Returns 0.0 safely if denominator is 0.
    """
    denom = tp + fp
    return float(tp / denom) if denom > 0 else 0.0


def recall(tp: int, fn: int) -> float:
    """
    Computes recall (sensitivity): TP / (TP + FN).
    Returns 0.0 safely if denominator is 0.
    """
    denom = tp + fn
    return float(tp / denom) if denom > 0 else 0.0


def f1_score(
    tp: int = 0,
    fp: int = 0,
    fn: int = 0,
    precision_val: float | None = None,
    recall_val: float | None = None,
) -> float:
    """
    Computes F1 score: 2 * (P * R) / (P + R).
    Can accept either (tp, fp, fn) or precomputed (precision_val, recall_val).
    Returns 0.0 safely if denominator is 0.
    """
    p = precision_val if precision_val is not None else precision(tp, fp)
    r = recall_val if recall_val is not None else recall(tp, fn)
    denom = p + r
    return float((2.0 * p * r) / denom) if denom > 0 else 0.0


def accuracy(tp: int, fp: int, tn: int, fn: int) -> float:
    """
    Computes overall accuracy: (TP + TN) / (TP + FP + TN + FN).
    Returns 0.0 safely if total count is 0.
    """
    total = tp + fp + tn + fn
    return float((tp + tn) / total) if total > 0 else 0.0


def false_positive_rate(fp: int, tn: int) -> float:
    """
    Computes false positive rate (FPR): FP / (FP + TN).
    Returns 0.0 safely if denominator is 0.
    """
    denom = fp + tn
    return float(fp / denom) if denom > 0 else 0.0


def false_negative_rate(fn: int, tp: int) -> float:
    """
    Computes false negative rate (FNR): FN / (FN + TP).
    Returns 0.0 safely if denominator is 0.
    """
    denom = fn + tp
    return float(fn / denom) if denom > 0 else 0.0


def specificity(tn: int, fp: int) -> float:
    """
    Computes specificity (true negative rate): TN / (TN + FP).
    Returns 0.0 safely if denominator is 0.
    """
    denom = tn + fp
    return float(tn / denom) if denom > 0 else 0.0


def balanced_accuracy(tp: int, fp: int, tn: int, fn: int) -> float:
    """
    Computes balanced accuracy: (Sensitivity + Specificity) / 2.
    """
    sens = recall(tp, fn)
    spec = specificity(tn, fp)
    return float((sens + spec) / 2.0)


def compute_metrics_from_counts(tp: int, fp: int, tn: int, fn: int) -> MetricResult:
    """
    Calculates all metrics from raw confusion matrix counts.
    """
    prec = precision(tp, fp)
    rec = recall(tp, fn)
    f1 = f1_score(precision_val=prec, recall_val=rec)
    acc = accuracy(tp, fp, tn, fn)
    fpr = false_positive_rate(fp, tn)
    fnr = false_negative_rate(fn, tp)
    spec = specificity(tn, fp)
    bacc = balanced_accuracy(tp, fp, tn, fn)

    return MetricResult(
        precision=prec,
        recall=rec,
        f1=f1,
        accuracy=acc,
        false_positive_rate=fpr,
        false_negative_rate=fnr,
        specificity=spec,
        balanced_accuracy=bacc,
    )


def compute_mean_std(values: Sequence[float]) -> tuple[float, float]:
    """
    Computes (mean, sample_std) for a sequence of numbers.
    Returns (0.0, 0.0) if sequence is empty.
    """
    if not values:
        return 0.0, 0.0
    n = len(values)
    mean_val = sum(values) / n
    if n <= 1:
        return mean_val, 0.0
    variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
    return mean_val, math.sqrt(max(0.0, variance))


def aggregate_seed_statistics(metrics_list: Sequence[MetricResult]) -> SeedStatistics:
    """
    Aggregates a list of MetricResult objects across multiple seeds into SeedStatistics.
    """
    if not metrics_list:
        return SeedStatistics()

    p_mean, p_std = compute_mean_std([m.precision for m in metrics_list])
    r_mean, r_std = compute_mean_std([m.recall for m in metrics_list])
    f1_mean, f1_std = compute_mean_std([m.f1 for m in metrics_list])
    acc_mean, acc_std = compute_mean_std([m.accuracy for m in metrics_list])
    fpr_mean, fpr_std = compute_mean_std([m.false_positive_rate for m in metrics_list])
    fnr_mean, fnr_std = compute_mean_std([m.false_negative_rate for m in metrics_list])
    spec_mean, spec_std = compute_mean_std([m.specificity for m in metrics_list])
    bacc_mean, bacc_std = compute_mean_std([m.balanced_accuracy for m in metrics_list])

    return SeedStatistics(
        precision_mean=p_mean,
        precision_std=p_std,
        recall_mean=r_mean,
        recall_std=r_std,
        f1_mean=f1_mean,
        f1_std=f1_std,
        accuracy_mean=acc_mean,
        accuracy_std=acc_std,
        false_positive_rate_mean=fpr_mean,
        false_positive_rate_std=fpr_std,
        false_negative_rate_mean=fnr_mean,
        false_negative_rate_std=fnr_std,
        specificity_mean=spec_mean,
        specificity_std=spec_std,
        balanced_accuracy_mean=bacc_mean,
        balanced_accuracy_std=bacc_std,
    )


# ---------------------------------------------------------------------
# Backward compatibility metrics for existing pipeline runners
# ---------------------------------------------------------------------

@dataclass
class DetectionMetrics:
    pis: float
    tdr: float
    precision: float
    false_positive_rate: float
    num_edges: int
    num_poisoned: int
    num_flagged: int
    num_true_positives: int


def compute_metrics(
    graph: ProvenanceGraph,
    poisoned_edge_ids: set[str],
    flagged_edge_ids: set[str],
) -> DetectionMetrics:
    """Backward compatibility helper for pipeline execution."""
    all_edge_ids = {e.edge_id for e in graph.edges}
    num_edges = len(all_edge_ids)
    num_poisoned = len(poisoned_edge_ids & all_edge_ids) + len(
        poisoned_edge_ids - all_edge_ids
    )

    true_positives = flagged_edge_ids & poisoned_edge_ids
    false_positives = flagged_edge_ids - poisoned_edge_ids
    benign_edges = all_edge_ids - poisoned_edge_ids

    valid_edges = num_edges - len(poisoned_edge_ids & all_edge_ids)
    pis = valid_edges / num_edges if num_edges else 0.0

    tdr = len(true_positives) / num_poisoned if num_poisoned else 0.0
    prec = len(true_positives) / len(flagged_edge_ids) if flagged_edge_ids else 0.0
    fpr = len(false_positives) / len(benign_edges) if benign_edges else 0.0

    return DetectionMetrics(
        pis=pis,
        tdr=tdr,
        precision=prec,
        false_positive_rate=fpr,
        num_edges=num_edges,
        num_poisoned=num_poisoned,
        num_flagged=len(flagged_edge_ids),
        num_true_positives=len(true_positives),
    )


def print_report(metrics: DetectionMetrics) -> None:
    """Backward compatibility print report."""
    print("Detection results")
    print(f"  edges in graph:        {metrics.num_edges}")
    print(f"  poisoning events:      {metrics.num_poisoned}")
    print(f"  edges flagged:         {metrics.num_flagged}")
    print(f"  true positives:        {metrics.num_true_positives}")
    print(f"  PIS (integrity score): {metrics.pis:.3f}")
    print(f"  TDR (detection rate):  {metrics.tdr:.3f}")
    print(f"  precision:             {metrics.precision:.3f}")
    print(f"  false positive rate:   {metrics.false_positive_rate:.3f}")
