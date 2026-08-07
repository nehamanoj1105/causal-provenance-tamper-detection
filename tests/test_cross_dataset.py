"""
Comprehensive unit tests for Phase 8 cross-dataset evaluation and report generation.
"""

import tempfile
import unittest
from pathlib import Path

from src.eval.cross_dataset import (
    CrossDatasetResult,
    generate_cross_dataset_csv,
    generate_cross_dataset_md,
    measure_execution,
    run_cross_dataset_eval,
    run_graphsage_eval,
    run_rule_engine_eval,
)
from src.graph_construction.graph_loader import available_datasets
from src.graph_construction.synthetic import generate_synthetic_graph
from src.detection.poisoning_injection import inject_poisoning


class TestCrossDatasetEvaluation(unittest.TestCase):

    def test_available_datasets_discovery(self):
        datasets = available_datasets()
        self.assertIsInstance(datasets, list)

    def test_measure_execution(self):
        def sample_fn(x, y):
            return x + y

        res, runtime, memory = measure_execution(sample_fn, 5, 10)
        self.assertEqual(res, 15)
        self.assertGreaterEqual(runtime, 0.0)
        self.assertGreaterEqual(memory, 0.0)

    def test_run_rule_engine_eval(self):
        graph = generate_synthetic_graph(num_processes=5, num_files=5, num_network=2, seed=42)
        poison_res = inject_poisoning(graph, 1, 1, 1, 1, seed=42)

        res = run_rule_engine_eval(graph, poison_res, "test_dataset")
        self.assertIsInstance(res, CrossDatasetResult)
        self.assertEqual(res.dataset, "test_dataset")
        self.assertEqual(res.detector, "Rule Engine")
        self.assertGreater(res.nodes, 0)
        self.assertGreater(res.edges, 0)

    def test_run_graphsage_eval(self):
        graph = generate_synthetic_graph(num_processes=5, num_files=5, num_network=2, seed=42)
        poison_res = inject_poisoning(graph, 1, 1, 1, 1, seed=42)

        res = run_graphsage_eval(graph, poison_res, "test_dataset", epochs=2, seed=42)
        self.assertIsInstance(res, CrossDatasetResult)
        self.assertEqual(res.dataset, "test_dataset")
        self.assertEqual(res.detector, "GraphSAGE")

    def test_report_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)

            res1 = CrossDatasetResult("ds1", "Rule Engine", 50, 100, 1.0, 0.9, 0.95, 0.98, 0.1, 12.5)
            res2 = CrossDatasetResult("ds1", "GraphSAGE", 50, 100, 0.8, 0.7, 0.75, 0.90, 0.5, 25.0)

            csv_p = generate_cross_dataset_csv([res1, res2], out_dir / "cross_dataset.csv")
            md_p = generate_cross_dataset_md([res1, res2], out_dir / "cross_dataset.md")

            self.assertTrue(csv_p.exists())
            self.assertTrue(md_p.exists())
            self.assertGreater(csv_p.stat().st_size, 0)
            self.assertGreater(md_p.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
