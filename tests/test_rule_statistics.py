"""
Unit tests for Phase 9 per-rule detection statistics and report generation.
"""

import tempfile
import unittest
from pathlib import Path

from src.detection.poisoning_injection import inject_poisoning
from src.eval.ablation import (
    RuleStatResult,
    generate_rule_statistics_csv,
    generate_rule_statistics_md,
    run_per_rule_statistics,
)
from src.graph_construction.synthetic import generate_synthetic_graph


class TestRuleStatistics(unittest.TestCase):

    def setUp(self):
        self.graph = generate_synthetic_graph(num_processes=10, num_files=10, num_network=4, seed=42)
        self.poison_res = inject_poisoning(self.graph, 2, 2, 2, 2, seed=42)

    def test_run_per_rule_statistics(self):
        results = run_per_rule_statistics(self.graph, self.poison_res)
        self.assertEqual(len(results), 15)

        rule_names = [r.rule_name for r in results]
        self.assertIn("UnspawnedProcessRule", rule_names)
        self.assertIn("SequenceGapRule", rule_names)
        self.assertIn("SequenceMonotonicityRule", rule_names)

        for res in results:
            self.assertIsInstance(res, RuleStatResult)
            self.assertGreaterEqual(res.violations, 0)
            self.assertGreaterEqual(res.tp, 0)
            self.assertGreaterEqual(res.fp, 0)

    def test_generate_rule_statistics_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            results = run_per_rule_statistics(self.graph, self.poison_res)

            csv_p = generate_rule_statistics_csv(results, out_dir / "rule_statistics.csv")
            md_p = generate_rule_statistics_md(results, out_dir / "rule_statistics.md")

            self.assertTrue(csv_p.exists())
            self.assertTrue(md_p.exists())
            self.assertGreater(csv_p.stat().st_size, 0)
            self.assertGreater(md_p.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
