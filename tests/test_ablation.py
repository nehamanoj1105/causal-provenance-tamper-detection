"""
Unit tests for Phase 9 Rule Engine ablation study and report generation.
"""

import tempfile
import unittest
from pathlib import Path

from src.detection.poisoning_injection import inject_poisoning
from src.eval.ablation import (
    AblationResult,
    generate_ablation_csv,
    generate_ablation_md,
    run_rule_ablation,
)
from src.graph_construction.synthetic import generate_synthetic_graph


class TestRuleAblation(unittest.TestCase):

    def setUp(self):
        self.graph = generate_synthetic_graph(num_processes=10, num_files=10, num_network=4, seed=42)
        self.poison_res = inject_poisoning(self.graph, 2, 2, 2, 2, seed=42)

    def test_run_rule_ablation(self):
        results = run_rule_ablation(self.graph, self.poison_res)
        self.assertGreater(len(results), 5)

        config_names = [r.config_name for r in results]
        self.assertIn("ALL Rules Enabled", config_names)
        self.assertIn("Without Structural Rules", config_names)
        self.assertIn("Without Temporal Rules", config_names)
        self.assertIn("Without Semantic Rules", config_names)

        all_rules_res = results[0]
        self.assertEqual(all_rules_res.num_rules, 15)

    def test_generate_ablation_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            results = run_rule_ablation(self.graph, self.poison_res)

            csv_p = generate_ablation_csv(results, out_dir / "ablation.csv")
            md_p = generate_ablation_md(results, out_dir / "ablation.md")

            self.assertTrue(csv_p.exists())
            self.assertTrue(md_p.exists())
            self.assertGreater(csv_p.stat().st_size, 0)
            self.assertGreater(md_p.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
