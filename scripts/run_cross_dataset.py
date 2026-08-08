#!/usr/bin/env python3
"""
Runs Multi-Scenario Evaluation across all available DARPA TC E3 provenance datasets.

Executes both Rule Engine and GraphSAGE models on each dataset, measuring:
- Precision, Recall, F1 Score, Accuracy
- Execution Runtime (seconds)
- Peak Memory Usage (MB)

Generates:
- results/cross_dataset.csv
- results/cross_dataset.md

Usage:
    python3 scripts/run_cross_dataset.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.eval.cross_dataset import (
    generate_cross_dataset_csv,
    generate_cross_dataset_md,
    run_cross_dataset_eval,
)
from src.graph_construction.graph_loader import available_datasets


def main():
    parser = argparse.ArgumentParser(description="Multi-Scenario Evaluation across DARPA TC E3 Datasets")

    parser.add_argument("--epochs", type=int, default=15, help="Number of GraphSAGE training epochs per dataset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max-edges", type=int, default=50000, help="Maximum edges per dataset for fast evaluation (0 for full dataset)")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory for output report files")

    args = parser.parse_args()

    disc_datasets = available_datasets()
    print(f"[*] Discovered available datasets: {disc_datasets}")

    max_edges = args.max_edges if args.max_edges > 0 else None

    results = run_cross_dataset_eval(
        datasets=disc_datasets,
        epochs=args.epochs,
        seed=args.seed,
        max_edges=max_edges,
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = generate_cross_dataset_csv(results, out_dir / "cross_dataset.csv")
    md_path = generate_cross_dataset_md(results, out_dir / "cross_dataset.md")

    print("\n" + "=" * 85)
    print("CROSS-DATASET EVALUATION SUMMARY REPORT")
    print("=" * 85)
    print(f"{'Dataset':<12} | {'Detector':<12} | {'Nodes':<6} | {'Edges':<6} | {'Precision':<9} | {'Recall':<9} | {'F1':<9} | {'Runtime (s)':<11} | {'Memory (MB)':<11}")
    print("-" * 85)
    for r in results:
        print(f"{r.dataset:<12} | {r.detector:<12} | {r.nodes:<6} | {r.edges:<6} | {r.precision:<9.4f} | {r.recall:<9.4f} | {r.f1:<9.4f} | {r.runtime:<11.4f} | {r.memory:<11.2f}")

    print("\n[+] Reports generated successfully:")
    print(f"  [CSV] {csv_path}")
    print(f"  [MD]  {md_path}")
    print("\n[+] Phase 8 cross-dataset evaluation completed.")


if __name__ == "__main__":
    main()
