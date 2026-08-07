"""
Unit tests for Phase 9 scalability, memory, throughput benchmarking, and plot generation.
"""

import tempfile
import unittest
from pathlib import Path

from src.detection.poisoning_injection import inject_poisoning
from src.eval.scalability import (
    ScalabilityResult,
    benchmark_graphsage_inference_on_graph,
    benchmark_rule_engine_on_graph,
    generate_memory_csv,
    generate_memory_md,
    generate_throughput_csv,
    generate_throughput_md,
    get_memory_info_mb,
    plot_memory_vs_edges,
    plot_runtime_vs_edges,
    plot_throughput_vs_edges,
    run_scalability_benchmark,
)
from src.graph_construction.synthetic import generate_synthetic_graph


class TestScalabilityBenchmarking(unittest.TestCase):

    def setUp(self):
        self.graph = generate_synthetic_graph(num_processes=5, num_files=5, num_network=2, seed=42)
        self.poison_res = inject_poisoning(self.graph, 1, 1, 1, 1, seed=42)

    def test_get_memory_info_mb(self):
        rss, py_alloc = get_memory_info_mb()
        self.assertGreater(rss, 0.0)
        self.assertGreaterEqual(py_alloc, 0.0)

    def test_benchmark_rule_engine_on_graph(self):
        res = benchmark_rule_engine_on_graph(self.graph, self.poison_res, 0.01, 0.01)
        self.assertIsInstance(res, ScalabilityResult)
        self.assertEqual(res.detector, "Rule Engine")
        self.assertGreater(res.throughput_eps, 0.0)
        self.assertGreater(res.rss_memory_mb, 0.0)

    def test_benchmark_graphsage_inference_on_graph(self):
        res = benchmark_graphsage_inference_on_graph(self.graph, self.poison_res, 0.01, 0.01, seed=42)
        self.assertIsInstance(res, ScalabilityResult)
        self.assertIn("GraphSAGE", res.detector)
        self.assertGreater(res.throughput_eps, 0.0)

    def test_run_scalability_benchmark_small_scales(self):
        results = run_scalability_benchmark(edge_scales=[100, 200], intensity=1, seed=42)
        self.assertEqual(len(results), 4)  # 2 scales * 2 detectors

    def test_scalability_plots_and_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            results = run_scalability_benchmark(edge_scales=[100], intensity=1, seed=42)

            mem_csv = generate_memory_csv(results, out_dir / "memory.csv")
            mem_md = generate_memory_md(results, out_dir / "memory.md")
            tp_csv = generate_throughput_csv(results, out_dir / "throughput.csv")
            tp_md = generate_throughput_md(results, out_dir / "throughput.md")

            p_rt = plot_runtime_vs_edges(results, out_dir / "rt.png")
            p_mem = plot_memory_vs_edges(results, out_dir / "mem.png")
            p_tp = plot_throughput_vs_edges(results, out_dir / "tp.png")

            self.assertTrue(mem_csv.exists())
            self.assertTrue(mem_md.exists())
            self.assertTrue(tp_csv.exists())
            self.assertTrue(tp_md.exists())
            self.assertTrue(p_rt.exists())
            self.assertTrue(p_mem.exists())
            self.assertTrue(p_tp.exists())


if __name__ == "__main__":
    unittest.main()
