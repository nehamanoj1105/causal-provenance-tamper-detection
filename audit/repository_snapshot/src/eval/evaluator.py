"""
Evaluator for matching detector output against ground truth poisoning labels.

Implements the Evaluator class, EvaluationResult dataclass, and RuntimeMetrics
to produce ConfusionMatrix, MetricResult, and multi-seed statistical evaluation outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from src.eval.confusion_matrix import ConfusionMatrix
from src.eval.metrics import MetricResult, SeedStatistics, aggregate_seed_statistics, compute_metrics_from_counts
from src.graph_construction.schema import ProvenanceGraph


@dataclass
class RuntimeMetrics:
    """Dataclass storing granular execution timing measurements in seconds."""

    graph_loading_time: float = 0.0
    attack_injection_time: float = 0.0
    rule_engine_runtime: float = 0.0
    evaluation_runtime: float = 0.0
    total_runtime: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert timing metrics to dictionary."""
        return {
            "graph_loading_time": round(self.graph_loading_time, 6),
            "attack_injection_time": round(self.attack_injection_time, 6),
            "rule_engine_runtime": round(self.rule_engine_runtime, 6),
            "evaluation_runtime": round(self.evaluation_runtime, 6),
            "total_runtime": round(self.total_runtime, 6),
        }


@dataclass
class EvaluationResult:
    """
    Complete evaluation summary containing confusion matrix, metrics,
    metadata, seed, and runtime measurements.
    """

    confusion_matrix: ConfusionMatrix
    metrics: MetricResult
    dataset: str = "unknown"
    attack_type: str = "unknown"
    seed: int = 42
    runtime_metrics: RuntimeMetrics = field(default_factory=RuntimeMetrics)

    @property
    def runtime_seconds(self) -> float:
        """Returns total runtime in seconds."""
        return self.runtime_metrics.total_runtime

    def to_dict(self) -> dict[str, Any]:
        """Convert full evaluation result into a serializable dictionary matching required CSV schema."""
        return {
            "Attack": self.attack_type,
            "Seed": self.seed,
            "TP": self.confusion_matrix.tp,
            "FP": self.confusion_matrix.fp,
            "TN": self.confusion_matrix.tn,
            "FN": self.confusion_matrix.fn,
            "Precision": round(self.metrics.precision, 6),
            "Recall": round(self.metrics.recall, 6),
            "F1": round(self.metrics.f1, 6),
            "Accuracy": round(self.metrics.accuracy, 6),
            "FalsePositiveRate": round(self.metrics.false_positive_rate, 6),
            "FalseNegativeRate": round(self.metrics.false_negative_rate, 6),
            "Specificity": round(self.metrics.specificity, 6),
            "BalancedAccuracy": round(self.metrics.balanced_accuracy, 6),
            "Runtime": round(self.runtime_metrics.total_runtime, 6),
            # Additional lower-case aliases for backward compatibility
            "dataset": self.dataset,
            "attack": self.attack_type,
            "seed": self.seed,
            "tp": self.confusion_matrix.tp,
            "fp": self.confusion_matrix.fp,
            "tn": self.confusion_matrix.tn,
            "fn": self.confusion_matrix.fn,
            "precision": round(self.metrics.precision, 6),
            "recall": round(self.metrics.recall, 6),
            "f1": round(self.metrics.f1, 6),
            "accuracy": round(self.metrics.accuracy, 6),
            "false_positive_rate": round(self.metrics.false_positive_rate, 6),
            "false_negative_rate": round(self.metrics.false_negative_rate, 6),
            "specificity": round(self.metrics.specificity, 6),
            "balanced_accuracy": round(self.metrics.balanced_accuracy, 6),
            "runtime": round(self.runtime_metrics.total_runtime, 6),
            "graph_loading_time": round(self.runtime_metrics.graph_loading_time, 6),
            "attack_injection_time": round(self.runtime_metrics.attack_injection_time, 6),
            "rule_engine_runtime": round(self.runtime_metrics.rule_engine_runtime, 6),
            "evaluation_runtime": round(self.runtime_metrics.evaluation_runtime, 6),
        }


class Evaluator:
    """
    Evaluates detector output against ground truth poisoning labels.
    """

    @staticmethod
    def _extract_gt_ids(ground_truth: Any) -> set[str]:
        """Extracts ground truth poisoned edge IDs from various input shapes."""
        if ground_truth is None:
            return set()

        if hasattr(ground_truth, "events"):
            return {
                e.edge_id
                for e in ground_truth.events
                if getattr(e, "edge_id", None) is not None
            }

        if hasattr(ground_truth, "edge_labels") and callable(ground_truth.edge_labels):
            return set(ground_truth.edge_labels().keys())

        if isinstance(ground_truth, (set, list, tuple)):
            gt_set = set()
            for item in ground_truth:
                if isinstance(item, str):
                    gt_set.add(item)
                elif hasattr(item, "edge_id") and getattr(item, "edge_id", None):
                    gt_set.add(item.edge_id)
            return gt_set

        return set()

    @staticmethod
    def _extract_detected_ids(detected_violations: Any) -> set[str]:
        """
        Extracts detected edge IDs from rule engine output, deduplicating
        multiple violations pointing to the same edge ID.
        """
        if detected_violations is None:
            return set()

        det_set: set[str] = set()

        if isinstance(detected_violations, (set, list, tuple)):
            for item in detected_violations:
                if isinstance(item, str):
                    det_set.add(item)
                elif hasattr(item, "violations"):
                    # RuleResult containing multiple RuleViolation objects
                    for v in getattr(item, "violations", []):
                        eid = getattr(v, "edge_id", None)
                        if eid is not None:
                            det_set.add(str(eid))
                elif hasattr(item, "edge_id"):
                    # RuleViolation or ConsistencyViolation object directly
                    eid = getattr(item, "edge_id", None)
                    if eid is not None:
                        det_set.add(str(eid))

        return det_set

    def evaluate(
        self,
        ground_truth: Any,
        detected_violations: Any,
        graph: ProvenanceGraph | None = None,
        dataset: str = "synthetic",
        attack_type: str = "all",
        seed: int = 42,
        runtime_metrics: RuntimeMetrics | float | None = None,
        runtime_seconds: float = 0.0,
    ) -> EvaluationResult:
        """
        Runs evaluation matching detected edge IDs against ground truth.

        Args:
            ground_truth: PoisoningResult or list of PoisoningEvents or set of edge IDs.
            detected_violations: Rule engine output (RuleResult list, violation list, or edge set).
            graph: Optional ProvenanceGraph to determine the total edge universe.
            dataset: Identifier for the dataset evaluated.
            attack_type: Identifier for the attack type evaluated.
            seed: Random seed evaluated.
            runtime_metrics: RuntimeMetrics object or total float runtime.
            runtime_seconds: Fallback total runtime seconds.

        Returns:
            EvaluationResult dataclass containing ConfusionMatrix and MetricResult.
        """
        gt_ids = self._extract_gt_ids(ground_truth)
        det_ids = self._extract_detected_ids(detected_violations)

        # Build universe of all relevant edge IDs
        if graph is not None and hasattr(graph, "edges"):
            graph_edge_ids = {e.edge_id for e in graph.edges}
        else:
            graph_edge_ids = set()

        universe = graph_edge_ids | gt_ids | det_ids

        # Normalize runtime metrics
        if isinstance(runtime_metrics, RuntimeMetrics):
            rt_metrics = runtime_metrics
        elif isinstance(runtime_metrics, (int, float)):
            rt_metrics = RuntimeMetrics(total_runtime=float(runtime_metrics))
        else:
            rt_metrics = RuntimeMetrics(total_runtime=float(runtime_seconds))

        # If universe is completely empty (e.g. empty graph with 0 events), all counts are 0
        if not universe:
            cm = ConfusionMatrix(tp=0, fp=0, tn=0, fn=0)
            metrics = compute_metrics_from_counts(0, 0, 0, 0)
            return EvaluationResult(
                confusion_matrix=cm,
                metrics=metrics,
                dataset=dataset,
                attack_type=attack_type,
                seed=seed,
                runtime_metrics=rt_metrics,
            )

        tp = len(gt_ids & det_ids)
        fp = len(det_ids - gt_ids)
        fn = len(gt_ids - det_ids)
        tn = len(universe - (gt_ids | det_ids))

        cm = ConfusionMatrix(tp=tp, fp=fp, tn=tn, fn=fn)
        metrics = compute_metrics_from_counts(tp=tp, fp=fp, tn=tn, fn=fn)

        return EvaluationResult(
            confusion_matrix=cm,
            metrics=metrics,
            dataset=dataset,
            attack_type=attack_type,
            seed=seed,
            runtime_metrics=rt_metrics,
        )

    def evaluate_multiple_seeds(
        self,
        results_per_seed: Sequence[EvaluationResult],
    ) -> tuple[list[EvaluationResult], SeedStatistics]:
        """
        Aggregates multiple EvaluationResult instances across seeds into SeedStatistics.
        """
        res_list = list(results_per_seed)
        metrics_list = [r.metrics for r in res_list]
        stats = aggregate_seed_statistics(metrics_list)
        return res_list, stats
