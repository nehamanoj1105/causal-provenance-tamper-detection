"""
Comprehensive unit tests for Phase 6 evaluation framework and semantic rule extensions.
"""

import tempfile
import unittest
from pathlib import Path

from src.detection.poisoning_injection import PoisoningEvent, PoisoningResult, PoisoningType
from src.detection.rule_engine import (
    ParentChildTemporalRule,
    ProcessActivityTemporalRule,
    RuleResult,
    RuleViolation,
    SequenceGapRule,
    SequenceMonotonicityRule,
    UnspawnedProcessRule,
    default_rule_engine,
)
from src.eval.evaluator import EvaluationResult, Evaluator, RuntimeMetrics
from src.eval.metrics import (
    MetricResult,
    SeedStatistics,
    aggregate_seed_statistics,
    compute_mean_std,
)
from src.eval.report import (
    generate_all_reports,
    generate_attack_breakdown_csv,
    generate_attack_breakdown_md,
    generate_runtime_csv,
    generate_runtime_md,
    generate_seed_statistics_csv,
    generate_seed_statistics_md,
)
from src.graph_construction.schema import EdgeType, NodeType, ProvenanceEdge, ProvenanceGraph, ProvenanceNode


class TestPhase6Metrics(unittest.TestCase):

    def test_compute_mean_std(self):
        values = [10.0, 20.0, 30.0]
        mean, std = compute_mean_std(values)
        self.assertEqual(mean, 20.0)
        self.assertAlmostEqual(std, 10.0)

    def test_compute_mean_std_single_value(self):
        mean, std = compute_mean_std([5.0])
        self.assertEqual(mean, 5.0)
        self.assertEqual(std, 0.0)

    def test_compute_mean_std_empty(self):
        mean, std = compute_mean_std([])
        self.assertEqual(mean, 0.0)
        self.assertEqual(std, 0.0)

    def test_aggregate_seed_statistics(self):
        m1 = MetricResult(precision=0.8, recall=0.6, f1=0.7, accuracy=0.9)
        m2 = MetricResult(precision=1.0, recall=0.8, f1=0.9, accuracy=0.95)
        stats = aggregate_seed_statistics([m1, m2])
        self.assertIsInstance(stats, SeedStatistics)
        self.assertEqual(stats.precision_mean, 0.9)
        self.assertAlmostEqual(stats.precision_std, 0.141421356)
        self.assertEqual(stats.recall_mean, 0.7)


class TestPhase6RuntimeMetrics(unittest.TestCase):

    def test_runtime_metrics_dict(self):
        rm = RuntimeMetrics(
            graph_loading_time=0.1,
            attack_injection_time=0.2,
            rule_engine_runtime=0.3,
            evaluation_runtime=0.05,
            total_runtime=0.65,
        )
        d = rm.to_dict()
        self.assertEqual(d["graph_loading_time"], 0.1)
        self.assertEqual(d["total_runtime"], 0.65)


class TestPhase6SemanticRules(unittest.TestCase):

    def test_unspawned_process_rule(self):
        graph = ProvenanceGraph()
        # proc_1 performs read action but has no spawn edge
        graph.add_node(ProvenanceNode("proc_1", NodeType.PROCESS, "proc_1"))
        graph.add_node(ProvenanceNode("file_1", NodeType.FILE, "file_1"))
        graph.add_edge(ProvenanceEdge("e_activity_1", "proc_1", "file_1", EdgeType.READ, 100.0))

        res = UnspawnedProcessRule().check(graph)
        self.assertFalse(res.passed)
        self.assertEqual(len(res.violations), 1)
        self.assertEqual(res.violations[0].edge_id, "e_spawn_1")

    def test_sequence_gap_rule(self):
        graph = ProvenanceGraph()
        graph.add_node(ProvenanceNode("p0", NodeType.PROCESS, "p0"))
        graph.add_node(ProvenanceNode("f0", NodeType.FILE, "f0"))
        # e_activity_1 and e_activity_3 present, e_activity_2 missing
        graph.add_edge(ProvenanceEdge("e_activity_1", "p0", "f0", EdgeType.READ, 100.0))
        graph.add_edge(ProvenanceEdge("e_activity_3", "p0", "f0", EdgeType.WRITE, 102.0))

        res = SequenceGapRule().check(graph)
        self.assertFalse(res.passed)
        self.assertEqual(res.violations[0].edge_id, "e_activity_2")

    def test_parent_child_temporal_rule(self):
        graph = ProvenanceGraph()
        graph.add_node(ProvenanceNode("p1", NodeType.PROCESS, "p1"))
        graph.add_node(ProvenanceNode("p2", NodeType.PROCESS, "p2"))
        graph.add_node(ProvenanceNode("p3", NodeType.PROCESS, "p3"))
        # p1 spawned p2 at 100.0
        graph.add_edge(ProvenanceEdge("e_spawn_2", "p1", "p2", EdgeType.SPAWN, 100.0))
        # p2 spawns p3 at 50.0 (inconsistent: before p2 was spawned)
        graph.add_edge(ProvenanceEdge("e_spawn_3", "p2", "p3", EdgeType.SPAWN, 50.0))

        res = ParentChildTemporalRule().check(graph)
        self.assertFalse(res.passed)
        self.assertEqual(res.violations[0].edge_id, "e_spawn_3")

    def test_sequence_monotonicity_rule(self):
        graph = ProvenanceGraph()
        graph.add_node(ProvenanceNode("p1", NodeType.PROCESS, "p1"))
        graph.add_node(ProvenanceNode("f1", NodeType.FILE, "f1"))
        # e_activity_10 at 100.0, e_activity_11 at 80.0 (inconsistent timestamp order)
        graph.add_edge(ProvenanceEdge("e_activity_10", "p1", "f1", EdgeType.READ, 100.0))
        graph.add_edge(ProvenanceEdge("e_activity_11", "p1", "f1", EdgeType.WRITE, 80.0))

        res = SequenceMonotonicityRule().check(graph)
        self.assertFalse(res.passed)
        flagged_ids = {v.edge_id for v in res.violations}
        self.assertIn("e_activity_10", flagged_ids)
        self.assertIn("e_activity_11", flagged_ids)


class TestPhase6Reports(unittest.TestCase):

    def test_report_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            cm = Evaluator().evaluate([], [], ProvenanceGraph()).confusion_matrix
            m = MetricResult(precision=1.0, recall=0.8, f1=0.89, accuracy=0.95)
            rm = RuntimeMetrics(total_runtime=0.01)

            res = EvaluationResult(
                confusion_matrix=cm,
                metrics=m,
                dataset="synthetic",
                attack_type="random_deletion",
                seed=42,
                runtime_metrics=rm,
            )

            paths = generate_all_reports([res], results_dir=out_dir)

            for name, path in paths.items():
                self.assertTrue(path.exists(), f"Report file {name} was not created")
                self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
