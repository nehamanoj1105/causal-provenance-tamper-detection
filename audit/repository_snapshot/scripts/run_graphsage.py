#!/usr/bin/env python3
"""
Runs the enhanced Phase 7/8 GraphSAGE evaluation and calibration pipeline:

    Train GraphSAGE -> Perform Threshold Sweep -> Optimize Threshold ->
    Generate Curves & Plots -> Output Calibration Stats -> Generate Diagnostic Report

Usage:
    python3 scripts/run_graphsage.py --epochs 30 --seed 42
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.detection.poisoning_injection import inject_poisoning
from src.graph_construction.converter import dataframe_to_schema
from src.graph_construction.graph_loader import dataset_exists, load_graph
from src.graph_construction.synthetic import generate_synthetic_graph
from src.ml.dataset import provenance_to_pyg_data
from src.ml.metrics import (
    compute_calibration_stats,
    generate_graphsage_diagnostics_md,
    generate_threshold_metrics_csv,
    generate_threshold_metrics_md,
    plot_prediction_histogram,
    plot_precision_recall_curve,
    plot_roc_curve,
    threshold_sweep,
)
from src.ml.predict import predict_edges
from src.ml.train import train_pipeline
from src.ml.utils import get_device, set_seed


def load_graphsage_data(
    dataset: str = "synthetic",
    num_processes: int = 30,
    num_files: int = 40,
    num_network: int = 10,
    intensity: int = 5,
    seed: int = 42,
):
    """
    Loads or generates provenance graph and converts to PyG Data with poisoning labels.
    """
    set_seed(seed)

    if dataset.lower() == "synthetic" or not dataset_exists(dataset):
        print(f"[*] Generating synthetic provenance graph (seed={seed})...")
        graph = generate_synthetic_graph(
            num_processes=num_processes,
            num_files=num_files,
            num_network=num_network,
            seed=seed,
        )
    else:
        print(f"[*] Loading provenance dataset '{dataset}'...")
        df_graph = load_graph(dataset)
        graph = dataframe_to_schema(df_graph)

    print(f"    Graph loaded: {len(graph.nodes)} nodes, {len(graph.edges)} edges.")

    print(f"[*] Injecting poisoning attack (intensity={intensity}, seed={seed})...")
    poison_res = inject_poisoning(
        graph,
        num_deletions=intensity,
        num_insertions=intensity,
        num_reorderings=intensity,
        num_forgeries=intensity,
        seed=seed,
    )
    print(f"    Poisoned graph ready: {len(poison_res.events)} poisoning events injected.")

    print("[*] Converting ProvenanceGraph to PyTorch Geometric Data object...")
    pyg_data = provenance_to_pyg_data(poison_res.graph, poisoning_result=poison_res)
    print(f"    PyG Data ready: x={list(pyg_data.x.shape)}, edge_index={list(pyg_data.edge_index.shape)}.")

    return pyg_data, poison_res


def run_graphsage_pipeline(
    dataset: str = "synthetic",
    epochs: int = 30,
    lr: float = 0.01,
    hidden_channels: int = 64,
    intensity: int = 5,
    seed: int = 42,
    output_dir: str = "results",
):
    """
    Runs full GraphSAGE training, threshold optimization, plot generation, and diagnostic reporting.
    """
    start_time = time.time()
    set_seed(seed)
    device = get_device()
    print(f"[*] PyTorch Device: {device}")

    # 1. Load & Convert Data
    pyg_data, poison_res = load_graphsage_data(
        dataset=dataset,
        intensity=intensity,
        seed=seed,
    )

    # 2. Train GraphSAGE Baseline Model
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    chkpt_path = out_dir / "graphsage_checkpoint.pt"

    print(f"[*] Training GraphSAGE model for {epochs} epochs...")
    model, best_metrics, best_thresh, train_loss_hist, val_loss_hist = train_pipeline(
        pyg_data,
        epochs=epochs,
        lr=lr,
        hidden_channels=hidden_channels,
        seed=seed,
        checkpoint_path=chkpt_path,
    )

    # 3. Predict Probabilities & Perform Threshold Sweep
    print("[*] Performing threshold sweep across 0.05 to 1.00...")
    model.eval()
    with torch.no_grad():
        x_dev = pyg_data.x.to(device)
        edge_idx_dev = pyg_data.edge_index.to(device)
        _, edge_logits, _ = model(x_dev, edge_idx_dev)
        y_true = pyg_data.edge_label.cpu().numpy()
        y_prob = torch.sigmoid(edge_logits).cpu().numpy()

    sweep_results = threshold_sweep(y_true, y_prob)
    calib = compute_calibration_stats(y_prob)

    # 4. Generate Reports & Plots
    print(f"[*] Generating evaluation reports and plots under '{output_dir}/'...")
    t_csv_path = generate_threshold_metrics_csv(sweep_results, out_dir / "threshold_metrics.csv")
    t_md_path = generate_threshold_metrics_md(sweep_results, out_dir / "threshold_metrics.md")
    diag_path = generate_graphsage_diagnostics_md(
        y_true=y_true,
        y_prob=y_prob,
        best_threshold=best_thresh,
        best_metrics=best_metrics,
        train_loss_history=train_loss_hist,
        val_loss_history=val_loss_hist,
        output_path=out_dir / "graphsage_diagnostics.md",
    )

    pr_plot = plot_precision_recall_curve(y_true, y_prob, out_dir / "precision_recall_curve.png")
    roc_plot = plot_roc_curve(y_true, y_prob, out_dir / "roc_curve.png")
    hist_plot = plot_prediction_histogram(y_prob, out_dir / "prediction_histogram.png")

    total_time = time.time() - start_time

    # 5. Print Results Summary
    print("\n" + "=" * 65)
    print("GRAPHSAGE ENHANCED EVALUATION RESULTS")
    print("=" * 65)
    m = best_metrics
    print(f"  Optimal Threshold   : {best_thresh:.2f}")
    print(f"  Precision           : {m.precision:.4f}")
    print(f"  Recall              : {m.recall:.4f}")
    print(f"  F1 Score            : {m.f1:.4f}")
    print(f"  Accuracy            : {m.accuracy:.4f}")
    print(f"  ROC-AUC             : {m.roc_auc:.4f}")
    print(f"  PR-AUC              : {m.pr_auc:.4f}")
    print(f"  MCC                 : {m.mcc:.4f}")
    print(f"  False Positive Rate : {m.false_positive_rate:.4f}")
    print(f"  Specificity         : {m.specificity:.4f}")
    print(f"  Prob Min / Max      : {calib['min_prob']:.4f} / {calib['max_prob']:.4f}")
    print(f"  Prob Mean / Median  : {calib['mean_prob']:.4f} / {calib['median_prob']:.4f}")
    print(f"  Total Runtime       : {total_time:.4f}s")
    print("=" * 65)

    print("\nGENERATED ARTIFACTS:")
    print(f"  [PR CURVE]   {pr_plot}")
    print(f"  [ROC CURVE]  {roc_plot}")
    print(f"  [HISTOGRAM]  {hist_plot}")
    print(f"  [METRICS]    {t_csv_path}")
    print(f"  [REPORT]     {t_md_path}")
    print(f"  [DIAGNOSIS]  {diag_path}")

    print("\n[+] GraphSAGE baseline training, calibration, and evaluation completed.")
    return model, best_metrics, best_thresh


def main():
    parser = argparse.ArgumentParser(description="GraphSAGE Baseline Enhanced Evaluation & Calibration Pipeline")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name or 'synthetic'")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
    parser.add_argument("--hidden-channels", type=int, default=64, help="GraphSAGE hidden dimension")
    parser.add_argument("--intensity", type=int, default=5, help="Poisoning attack intensity per type")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory for output report files")

    args = parser.parse_args()

    run_graphsage_pipeline(
        dataset=args.dataset,
        epochs=args.epochs,
        lr=args.lr,
        hidden_channels=args.hidden_channels,
        intensity=args.intensity,
        seed=args.seed,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
