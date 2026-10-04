#!/usr/bin/env python3
"""
Runs the Phase 9 USENIX-grade Scalability, Memory, Throughput, Rule Ablation,
and Per-Rule Statistical Benchmarking Pipeline.

Generates:
- results/memory.csv & results/memory.md
- results/throughput.csv & results/throughput.md
- results/runtime_vs_edges.png
- results/memory_vs_edges.png
- results/throughput_vs_edges.png
- results/ablation.csv & results/ablation.md
- results/rule_statistics.csv & results/rule_statistics.md

Usage:
    python3 scripts/run_scalability.py
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.detection.poisoning_injection import inject_poisoning
from src.eval.ablation import (
    generate_ablation_csv,
    generate_ablation_md,
    generate_rule_statistics_csv,
    generate_rule_statistics_md,
    run_per_rule_statistics,
    run_rule_ablation,
)
from src.eval.scalability import (
    generate_memory_csv,
    generate_memory_md,
    generate_throughput_csv,
    generate_throughput_md,
    plot_memory_vs_edges,
    plot_runtime_vs_edges,
    plot_throughput_vs_edges,
    run_scalability_benchmark,
)
from src.graph_construction.synthetic import generate_synthetic_graph


def main():
    parser = argparse.ArgumentParser(description="Phase 9 USENIX-Grade Scalability & Ablation Benchmarking Pipeline")
    parser.add_argument("--scales", type=str, default="10000,25000,50000,100000,250000,500000,1000000", help="Comma-separated edge scales for benchmarking")
    parser.add_argument("--intensity", type=int, default=5, help="Poisoning attack intensity per type")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory for output report files")

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    edge_scales = [int(s.strip()) for s in args.scales.split(",") if s.strip()]

    # 1. Run Scalability, Memory & Throughput Benchmark
    print("=" * 80)
    print("PART 1-3: RUNNING SCALABILITY, MEMORY & THROUGHPUT BENCHMARK")
    print("=" * 80)
    scalability_results = run_scalability_benchmark(
        edge_scales=edge_scales,
        intensity=args.intensity,
        seed=args.seed,
    )

    # 2. Generate Memory & Throughput Reports
    print("\n[*] Generating Memory & Throughput Reports...")
    mem_csv = generate_memory_csv(scalability_results, out_dir / "memory.csv")
    mem_md = generate_memory_md(scalability_results, out_dir / "memory.md")
    tp_csv = generate_throughput_csv(scalability_results, out_dir / "throughput.csv")
    tp_md = generate_throughput_md(scalability_results, out_dir / "throughput.md")

    # 3. Generate Benchmark Plots
    print("[*] Generating Benchmark Curves & Plots...")
    p_rt = plot_runtime_vs_edges(scalability_results, out_dir / "runtime_vs_edges.png")
    p_mem = plot_memory_vs_edges(scalability_results, out_dir / "memory_vs_edges.png")
    p_tp = plot_throughput_vs_edges(scalability_results, out_dir / "throughput_vs_edges.png")

    # 4. Run Rule Engine Ablation Study
    print("\n" + "=" * 80)
    print("PART 5: RUNNING RULE ENGINE ABLATION STUDY")
    print("=" * 80)
    bench_graph = generate_synthetic_graph(num_processes=30, num_files=40, num_network=10, seed=args.seed)
    bench_poison = inject_poisoning(bench_graph, 5, 5, 5, 5, seed=args.seed)

    ablation_results = run_rule_ablation(bench_graph, bench_poison)
    ab_csv = generate_ablation_csv(ablation_results, out_dir / "ablation.csv")
    ab_md = generate_ablation_md(ablation_results, out_dir / "ablation.md")

    # 5. Run Per-Rule Performance Statistics
    print("\n" + "=" * 80)
    print("PART 6: RUNNING PER-RULE PERFORMANCE STATISTICS")
    print("=" * 80)
    rule_stats = run_per_rule_statistics(bench_graph, bench_poison)
    rs_csv = generate_rule_statistics_csv(rule_stats, out_dir / "rule_statistics.csv")
    rs_md = generate_rule_statistics_md(rule_stats, out_dir / "rule_statistics.md")

    print("\n" + "=" * 80)
    print("PHASE 9 BENCHMARKING COMPLETE")
    print("=" * 80)
    print(f"  [MEMORY CSV]      {mem_csv}")
    print(f"  [MEMORY MD]       {mem_md}")
    print(f"  [THROUGHPUT CSV]  {tp_csv}")
    print(f"  [THROUGHPUT MD]   {tp_md}")
    print(f"  [RUNTIME PLOT]    {p_rt}")
    print(f"  [MEMORY PLOT]     {p_mem}")
    print(f"  [THROUGHPUT PLOT] {p_tp}")
    print(f"  [ABLATION CSV]    {ab_csv}")
    print(f"  [ABLATION MD]     {ab_md}")
    print(f"  [RULE STATS CSV]  {rs_csv}")
    print(f"  [RULE STATS MD]   {rs_md}")

    print("\n[+] All Phase 9 benchmarks, reports, and plots generated successfully.")


if __name__ == "__main__":
    main()
