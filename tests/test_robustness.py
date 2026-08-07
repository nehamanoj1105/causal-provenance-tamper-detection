"""
Unit tests for Phase 10 detector robustness evaluation, plots, and report generation.
"""

import tempfile
import unittest
from pathlib import Path

from src.eval.robustness import (
    RobustnessResult,
    generate_mimicry_results_csv,
    generate_mimicry_results_md,
    plot_robustness_curves,
    run_robustness_benchmark,
)
from src.graph_construction.synthetic import generate_synthetic_graph


class TestRobustnessEvaluation(unittest.TestCase):

    def setUp(self):
        self.graph = generate_synthetic_graph(num_processes=10, num_files=10, num_network=4, seed=42)

    def test_run_robustness_benchmark(self):
        results = run_robustness_benchmark(
            self.graph,
            strengths=("none", "light"),
            intensity=2,
            epochs=3,
            seed=42,
        )
        self.assertEqual(len(results), 4)  # 2 strengths * 2 detectors

        for res in results:
            self.assertIsInstance(res, RobustnessResult)
            self.assertGreaterEqual(res.precision, 0.0)
            self.assertLessEqual(res.precision, 1.0)
            self.assertGreaterEqual(res.recall, 0.0)
            self.assertLessEqual(res.recall, 1.0)

    def test_robustness_plots_and_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            results = run_robustness_benchmark(
                self.graph,
                strengths=("none", "light"),
                intensity=2,
                epochs=3,
                seed=42,
            )

            csv_p = generate_mimicry_results_csv(results, out_dir / "mimicry_results.csv")
            md_p = generate_mimicry_results_md(results, out_dir / "mimicry_results.md")

            p_rob, p_prec, p_rec, p_f1 = plot_robustness_curves(results, out_dir)

            self.assertTrue(csv_p.exists())
            self.assertTrue(md_p.exists())
            self.assertTrue(p_rob.exists())
            self.assertTrue(p_prec.exists())
            self.assertTrue(p_rec.exists())
            self.assertTrue(p_f1.exists())


if __name__ == "__main__":
    unittest.main()
