"""
Rule engine ablation study and per-rule detection statistics module.
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

from src.detection.rule_engine import (
    DeleteConsistencyRule,
    DuplicateEdgeRule,
    DuplicateEventRule,
    ExecutionConsistencyRule,
    MissingNodeRule,
    NetworkConsistencyRule,
    ParentChildTemporalRule,
    ProcessActivityTemporalRule,
    ReadWriteConsistencyRule,
    Rule,
    RuleEngine,
    RuleResult,
    SelfLoopRule,
    SequenceGapRule,
    SequenceMonotonicityRule,
    SpawnConsistencyRule,
    TimestampRule,
    UnspawnedProcessRule,
    default_rule_engine,
)
from src.eval.evaluator import Evaluator
from src.graph_construction.schema import ProvenanceGraph


STRUCTURAL_RULES = [
    DuplicateEdgeRule,
    DuplicateEventRule,
    SelfLoopRule,
    MissingNodeRule,
    UnspawnedProcessRule,
    SequenceGapRule,
]

TEMPORAL_RULES = [
    TimestampRule,
    ParentChildTemporalRule,
    ProcessActivityTemporalRule,
    SequenceMonotonicityRule,
]

SEMANTIC_RULES = [
    SpawnConsistencyRule,
    ExecutionConsistencyRule,
    ReadWriteConsistencyRule,
    NetworkConsistencyRule,
    DeleteConsistencyRule,
]

ALL_RULES_CLASSES = STRUCTURAL_RULES + TEMPORAL_RULES + SEMANTIC_RULES


@dataclass
class AblationResult:
    """Dataclass storing rule ablation evaluation results."""

    config_name: str
    num_rules: int
    precision: float
    recall: float
    f1: float
    accuracy: float
    runtime: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "Configuration": self.config_name,
            "NumRules": self.num_rules,
            "Precision": round(self.precision, 6),
            "Recall": round(self.recall, 6),
            "F1": round(self.f1, 6),
            "Accuracy": round(self.accuracy, 6),
            "Runtime": round(self.runtime, 6),
        }


@dataclass
class RuleStatResult:
    """Dataclass storing per-rule detection statistics."""

    rule_name: str
    category: str
    violations: int
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "Rule": self.rule_name,
            "Category": self.category,
            "Violations": self.violations,
            "TP": self.tp,
            "FP": self.fp,
            "FN": self.fn,
            "Precision": round(self.precision, 6),
            "Recall": round(self.recall, 6),
        }


def _evaluate_rule_set(
    rules: list[Rule],
    graph: ProvenanceGraph,
    poison_res: Any,
    config_name: str,
) -> AblationResult:
    """Evaluates a specific subset of rules against ground truth poisoning."""
    engine = RuleEngine(rules)

    t0 = time.time()
    rule_results = engine.run(poison_res.graph)
    t_runtime = time.time() - t0

    evaluator = Evaluator()
    eval_res = evaluator.evaluate(
        ground_truth=poison_res,
        detected_violations=rule_results,
        graph=poison_res.graph,
    )

    return AblationResult(
        config_name=config_name,
        num_rules=len(rules),
        precision=eval_res.metrics.precision,
        recall=eval_res.metrics.recall,
        f1=eval_res.metrics.f1,
        accuracy=eval_res.metrics.accuracy,
        runtime=t_runtime,
    )


def run_rule_ablation(
    graph: ProvenanceGraph,
    poison_res: Any,
) -> List[AblationResult]:
    """
    Executes comprehensive Rule Ablation Study:
    1. ALL rules enabled
    2. Without structural rules
    3. Without temporal rules
    4. Without semantic rules
    5. Leave-one-out per-rule removal (15 runs)
    """
    results: List[AblationResult] = []

    # 1. All rules enabled
    all_rules_instances = [cls() for cls in ALL_RULES_CLASSES]
    results.append(_evaluate_rule_set(all_rules_instances, graph, poison_res, "ALL Rules Enabled"))

    # 2. Without structural rules
    no_struct = [cls() for cls in ALL_RULES_CLASSES if cls not in STRUCTURAL_RULES]
    results.append(_evaluate_rule_set(no_struct, graph, poison_res, "Without Structural Rules"))

    # 3. Without temporal rules
    no_temp = [cls() for cls in ALL_RULES_CLASSES if cls not in TEMPORAL_RULES]
    results.append(_evaluate_rule_set(no_temp, graph, poison_res, "Without Temporal Rules"))

    # 4. Without semantic rules
    no_sem = [cls() for cls in ALL_RULES_CLASSES if cls not in SEMANTIC_RULES]
    results.append(_evaluate_rule_set(no_sem, graph, poison_res, "Without Semantic Rules"))

    # 5. Leave-one-out ablation per individual rule
    for target_cls in ALL_RULES_CLASSES:
        subset = [cls() for cls in ALL_RULES_CLASSES if cls != target_cls]
        results.append(_evaluate_rule_set(subset, graph, poison_res, f"Without {target_cls.name}"))

    return results


def run_per_rule_statistics(
    graph: ProvenanceGraph,
    poison_res: Any,
) -> List[RuleStatResult]:
    """
    Evaluates every rule individually against ground-truth poisoning.
    Reports: Rule Name, Category, Violations, TP, FP, FN, Precision, Recall.
    """
    evaluator = Evaluator()
    results: List[RuleStatResult] = []

    for cls in ALL_RULES_CLASSES:
        rule_instance = cls()
        if cls in STRUCTURAL_RULES:
            cat = "Structural"
        elif cls in TEMPORAL_RULES:
            cat = "Temporal"
        else:
            cat = "Semantic"

        engine = RuleEngine([rule_instance])
        rule_results = engine.run(poison_res.graph)

        eval_res = evaluator.evaluate(
            ground_truth=poison_res,
            detected_violations=rule_results,
            graph=poison_res.graph,
        )

        cm = eval_res.confusion_matrix
        tot_violations = len(evaluator._extract_detected_ids(rule_results))

        results.append(

            RuleStatResult(
                rule_name=rule_instance.name,
                category=cat,
                violations=tot_violations,
                tp=cm.tp,
                fp=cm.fp,
                fn=cm.fn,
                precision=eval_res.metrics.precision,
                recall=eval_res.metrics.recall,
            )
        )

    return results


def generate_ablation_csv(
    results: Sequence[AblationResult],
    output_path: Path | str = "results/ablation.csv",
) -> Path:
    """Generates results/ablation.csv."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["Configuration", "NumRules", "Precision", "Recall", "F1", "Accuracy", "Runtime"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            d = res.to_dict()
            writer.writerow({
                "Configuration": d["Configuration"],
                "NumRules": d["NumRules"],
                "Precision": d["Precision"],
                "Recall": d["Recall"],
                "F1": d["F1"],
                "Accuracy": d["Accuracy"],
                "Runtime": d["Runtime"],
            })

    return path


def generate_ablation_md(
    results: Sequence[AblationResult],
    output_path: Path | str = "results/ablation.md",
) -> Path:
    """Generates results/ablation.md."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Rule Engine Ablation Study Report",
        "",
        "| Configuration | Active Rules | Precision | Recall | F1 Score | Accuracy | Runtime (s) |",
        "|---|---|---|---|---|---|---|",
    ]

    for res in results:
        d = res.to_dict()
        lines.append(
            f"| **{d['Configuration']}** | {d['NumRules']} | "
            f"{d['Precision']:.4f} | {d['Recall']:.4f} | {d['F1']:.4f} | {d['Accuracy']:.4f} | "
            f"{d['Runtime']:.4f} |"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path


def generate_rule_statistics_csv(
    results: Sequence[RuleStatResult],
    output_path: Path | str = "results/rule_statistics.csv",
) -> Path:
    """Generates results/rule_statistics.csv."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["Rule", "Category", "Violations", "TP", "FP", "FN", "Precision", "Recall"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            d = res.to_dict()
            writer.writerow({
                "Rule": d["Rule"],
                "Category": d["Category"],
                "Violations": d["Violations"],
                "TP": d["TP"],
                "FP": d["FP"],
                "FN": d["FN"],
                "Precision": d["Precision"],
                "Recall": d["Recall"],
            })

    return path


def generate_rule_statistics_md(
    results: Sequence[RuleStatResult],
    output_path: Path | str = "results/rule_statistics.md",
) -> Path:
    """Generates results/rule_statistics.md."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Individual Rule Performance Statistics",
        "",
        "| Rule Name | Category | Violations | TP | FP | FN | Precision | Recall |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for res in results:
        d = res.to_dict()
        lines.append(
            f"| **{d['Rule']}** | {d['Category']} | {d['Violations']} | "
            f"{d['TP']} | {d['FP']} | {d['FN']} | {d['Precision']:.4f} | {d['Recall']:.4f} |"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path
