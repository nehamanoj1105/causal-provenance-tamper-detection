"""
Comprehensive unit tests for evaluator.py.
"""

import unittest

from src.detection.poisoning_injection import PoisoningEvent, PoisoningResult, PoisoningType
from src.detection.rule_engine import RuleResult, RuleViolation
from src.eval.evaluator import Evaluator, EvaluationResult
from src.graph_construction.schema import EdgeType, NodeType, ProvenanceEdge, ProvenanceGraph, ProvenanceNode


def _create_sample_graph(n_edges: int = 10) -> ProvenanceGraph:
    graph = ProvenanceGraph()
    graph.add_node(ProvenanceNode("proc_0", NodeType.PROCESS, "proc_0"))
    for i in range(n_edges):
        fid = f"file_{i}"
        graph.add_node(ProvenanceNode(fid, NodeType.FILE, fid))
        graph.add_edge(ProvenanceEdge(f"edge_{i}", "proc_0", fid, EdgeType.READ, float(100 + i)))
    return graph


class TestEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = Evaluator()

    def test_perfect_detection(self):
        graph = _create_sample_graph(10)
        gt_events = [
            PoisoningEvent(PoisoningType.REORDERING, "edge_0"),
            PoisoningEvent(PoisoningType.INSERTION, "edge_1"),
        ]
        gt = PoisoningResult(graph=graph, events=gt_events)

        violations = [
            RuleViolation(rule="TimestampRule", severity="HIGH", message="invalid", edge_id="edge_0"),
            RuleViolation(rule="DuplicateRule", severity="HIGH", message="invalid", edge_id="edge_1"),
        ]

        res = self.evaluator.evaluate(
            ground_truth=gt,
            detected_violations=violations,
            graph=graph,
            dataset="synthetic",
            attack_type="all",
        )

        self.assertIsInstance(res, EvaluationResult)
        self.assertEqual(res.confusion_matrix.tp, 2)
        self.assertEqual(res.confusion_matrix.fp, 0)
        self.assertEqual(res.confusion_matrix.fn, 0)
        self.assertEqual(res.confusion_matrix.tn, 8)
        self.assertEqual(res.metrics.precision, 1.0)
        self.assertEqual(res.metrics.recall, 1.0)
        self.assertEqual(res.metrics.f1, 1.0)

    def test_false_positives(self):
        graph = _create_sample_graph(10)
        gt_events = [PoisoningEvent(PoisoningType.REORDERING, "edge_0")]

        # Edge 0 is GT. Edge 1 and 2 are false positives.
        violations = [
            RuleViolation(rule="R1", severity="H", message="", edge_id="edge_0"),
            RuleViolation(rule="R2", severity="H", message="", edge_id="edge_1"),
            RuleViolation(rule="R3", severity="H", message="", edge_id="edge_2"),
        ]

        res = self.evaluator.evaluate(gt_events, violations, graph)
        self.assertEqual(res.confusion_matrix.tp, 1)
        self.assertEqual(res.confusion_matrix.fp, 2)
        self.assertEqual(res.confusion_matrix.fn, 0)
        self.assertEqual(res.confusion_matrix.tn, 7)

    def test_false_negatives(self):
        graph = _create_sample_graph(10)
        gt_events = [
            PoisoningEvent(PoisoningType.REORDERING, "edge_0"),
            PoisoningEvent(PoisoningType.DELETION, "edge_1"),
        ]

        # Only edge_0 is detected; edge_1 is a false negative.
        violations = [RuleViolation(rule="R1", severity="H", message="", edge_id="edge_0")]

        res = self.evaluator.evaluate(gt_events, violations, graph)
        self.assertEqual(res.confusion_matrix.tp, 1)
        self.assertEqual(res.confusion_matrix.fp, 0)
        self.assertEqual(res.confusion_matrix.fn, 1)
        self.assertEqual(res.confusion_matrix.tn, 8)

    def test_mixed_detections(self):
        graph = _create_sample_graph(10)
        gt_events = [
            PoisoningEvent(PoisoningType.REORDERING, "edge_0"),  # TP
            PoisoningEvent(PoisoningType.DELETION, "edge_1"),   # FN
        ]

        violations = [
            RuleViolation(rule="R1", severity="H", message="", edge_id="edge_0"),  # TP
            RuleViolation(rule="R2", severity="H", message="", edge_id="edge_5"),  # FP
        ]

        res = self.evaluator.evaluate(gt_events, violations, graph)
        self.assertEqual(res.confusion_matrix.tp, 1)
        self.assertEqual(res.confusion_matrix.fp, 1)
        self.assertEqual(res.confusion_matrix.fn, 1)
        self.assertEqual(res.confusion_matrix.tn, 7)

    def test_no_attacks(self):
        graph = _create_sample_graph(10)
        gt_events = []
        violations = [RuleViolation(rule="R1", severity="H", message="", edge_id="edge_0")]

        res = self.evaluator.evaluate(gt_events, violations, graph)
        self.assertEqual(res.confusion_matrix.tp, 0)
        self.assertEqual(res.confusion_matrix.fp, 1)
        self.assertEqual(res.confusion_matrix.fn, 0)
        self.assertEqual(res.confusion_matrix.tn, 9)

    def test_no_detections(self):
        graph = _create_sample_graph(10)
        gt_events = [PoisoningEvent(PoisoningType.REORDERING, "edge_0")]
        violations = []

        res = self.evaluator.evaluate(gt_events, violations, graph)
        self.assertEqual(res.confusion_matrix.tp, 0)
        self.assertEqual(res.confusion_matrix.fp, 0)
        self.assertEqual(res.confusion_matrix.fn, 1)
        self.assertEqual(res.confusion_matrix.tn, 9)

    def test_empty_graph(self):
        graph = ProvenanceGraph()
        res = self.evaluator.evaluate([], [], graph)
        self.assertEqual(res.confusion_matrix.tp, 0)
        self.assertEqual(res.confusion_matrix.fp, 0)
        self.assertEqual(res.confusion_matrix.fn, 0)
        self.assertEqual(res.confusion_matrix.tn, 0)
        self.assertEqual(res.metrics.precision, 0.0)
        self.assertEqual(res.metrics.recall, 0.0)

    def test_duplicate_detections_deduplicated(self):
        graph = _create_sample_graph(10)
        gt_events = [PoisoningEvent(PoisoningType.REORDERING, "edge_0")]

        # Multiple rules flag the SAME edge_0
        rule_results = [
            RuleResult(
                rule="R1",
                violations=[
                    RuleViolation(rule="R1", severity="H", message="", edge_id="edge_0"),
                    RuleViolation(rule="R1_dup", severity="H", message="", edge_id="edge_0"),
                ],
            ),
            RuleResult(
                rule="R2",
                violations=[
                    RuleViolation(rule="R2", severity="H", message="", edge_id="edge_0"),
                ],
            ),
        ]

        res = self.evaluator.evaluate(gt_events, rule_results, graph)
        self.assertEqual(res.confusion_matrix.tp, 1)
        self.assertEqual(res.confusion_matrix.fp, 0)


if __name__ == "__main__":
    unittest.main()
