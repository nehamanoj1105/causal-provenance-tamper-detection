#!/usr/bin/env python3
"""
Runs the Phase 10 Adversarial Mimicry Attack Benchmarking Pipeline:

Generates:
- results/mimicry_results.csv & results/mimicry_results.md
- results/robustness_curve.png
- results/precision_vs_attack.png
- results/recall_vs_attack.png
- results/F1_vs_attack.png

Usage:
    python3 scripts/run_mimicry.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.eval.robustness import (
    generate_mimicry_results_csv,
    generate_mimicry_results_md,
    plot_robustness_curves,
    run_robustness_benchmark,
)
from src.graph_construction.synthetic import generate_synthetic_graph


def main():
    parser = argparse.ArgumentParser(description="Phase 10 Adversarial Mimicry & Detector Robustness Pipeline")
    parser.add_argument("--epochs", type=int, default=25, help="Number of GraphSAGE training epochs")
    parser.add_argument("--intensity", type=int, default=5, help="Base poisoning attack intensity per type")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory for output report files")

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("PHASE 10: ADVERSARIAL MIMICRY ATTACK & DETECTOR ROBUSTNESS EVALUATION")
    print("=" * 80)

    print("[*] Generating baseline provenance graph for robustness evaluation...")
    graph = generate_synthetic_graph(num_processes=40, num_files=50, num_network=15, seed=args.seed)

    print("[*] Executing robustness benchmark across no mimicry, light, medium, and heavy strengths...")
    results = run_robustness_benchmark(
        graph,
        strengths=("none", "light", "medium", "heavy"),
        intensity=args.intensity,
        epochs=args.epochs,
        seed=args.seed,
    )

    print("\n[*] Generating CSV & Markdown Reports...")
    csv_p = generate_mimicry_results_csv(results, out_dir / "mimicry_results.csv")
    md_p = generate_mimicry_results_md(results, out_dir / "mimicry_results.md")

    print("[*] Generating Robustness Degradation Curves & Plots...")
    p_rob, p_prec, p_rec, p_f1 = plot_robustness_curves(results, out_dir)

    print("\n" + "=" * 80)
    print("PHASE 10 ROBUSTNESS BENCHMARKING COMPLETE")
    print("=" * 80)
    print(f"  [CSV REPORT]          {csv_p}")
    print(f"  [MD REPORT]           {md_p}")
    print(f"  [ROBUSTNESS PLOT]     {p_rob}")
    print(f"  [PRECISION PLOT]      {p_prec}")
    print(f"  [RECALL PLOT]         {p_rec}")
    print(f"  [F1 PLOT]             {p_f1}")

    print("\n[+] All Phase 10 mimicry robustness reports and plots generated successfully.")


if __name__ == "__main__":
    main()
