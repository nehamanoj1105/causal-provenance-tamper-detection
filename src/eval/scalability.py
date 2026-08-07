"""
Scalability, memory footprint, and throughput benchmarking module for USENIX-grade evaluation.
"""

from __future__ import annotations

import csv
import gc
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import psutil
import torch

from src.detection.poisoning_injection import inject_poisoning
from src.detection.rule_engine import default_rule_engine
from src.eval.evaluator import Evaluator
from src.graph_construction.converter import dataframe_to_schema
from src.graph_construction.graph_loader import available_datasets, dataset_exists, load_edges, load_nodes
from src.graph_construction.schema import ProvenanceGraph
from src.graph_construction.synthetic import generate_synthetic_graph
from src.ml.dataset import provenance_to_pyg_data
from src.ml.graphsage import GraphSAGEForTamperDetection
from src.ml.utils import get_device, set_seed


@dataclass
class ScalabilityResult:
    """Dataclass storing scalability, memory, runtime, and throughput metrics."""

    graph_size_edges: int
    graph_size_nodes: int
    detector: str
    loading_time: float
    attack_time: float
    detector_time: float
    eval_time: float
    total_time: float
    rss_memory_mb: float
    peak_memory_mb: float
    python_alloc_mb: float
    throughput_eps: float  # edges processed per second

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary matching report schemas."""
        return {
            "Edges": self.graph_size_edges,
            "Nodes": self.graph_size_nodes,
            "Detector": self.detector,
            "LoadingTime": round(self.loading_time, 6),
            "AttackTime": round(self.attack_time, 6),
            "DetectorTime": round(self.detector_time, 6),
            "EvalTime": round(self.eval_time, 6),
            "TotalTime": round(self.total_time, 6),
            "RSSMemoryMB": round(self.rss_memory_mb, 2),
            "PeakMemoryMB": round(self.peak_memory_mb, 2),
            "PythonAllocMB": round(self.python_alloc_mb, 2),
            "ThroughputEPS": round(self.throughput_eps, 2),
        }


def get_memory_info_mb() -> Tuple[float, float]:
    """Returns (RSS memory in MB, Current Python allocated memory in MB)."""
    process = psutil.Process()
    rss_mb = process.memory_info().rss / (1024.0 * 1024.0)
    current_bytes, _ = tracemalloc.get_traced_memory() if tracemalloc.is_tracing() else (0, 0)
    py_mb = current_bytes / (1024.0 * 1024.0)
    return rss_mb, py_mb


def benchmark_rule_engine_on_graph(
    graph: ProvenanceGraph,
    poison_res: Any,
    t_load: float,
    t_attack: float,
) -> ScalabilityResult:
    """
    Benchmarks Rule Engine performance, memory, and throughput on a given graph.
    """
    gc.collect()
    tracemalloc.start()
    rss_before, _ = get_memory_info_mb()

    t0 = time.time()
    engine = default_rule_engine()
    rule_results = engine.run(poison_res.graph)
    t_detector = time.time() - t0

    t1 = time.time()
    evaluator = Evaluator()
    eval_res = evaluator.evaluate(
        ground_truth=poison_res,
        detected_violations=rule_results,
        graph=poison_res.graph,
    )
    t_eval = time.time() - t1

    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rss_after, py_alloc = get_memory_info_mb()
    peak_mb = max(peak_bytes / (1024.0 * 1024.0), rss_after - rss_before)

    num_edges = len(graph.edges)
    num_nodes = len(graph.nodes)
    throughput = num_edges / t_detector if t_detector > 0 else 0.0
    t_total = t_load + t_attack + t_detector + t_eval

    return ScalabilityResult(
        graph_size_edges=num_edges,
        graph_size_nodes=num_nodes,
        detector="Rule Engine",
        loading_time=t_load,
        attack_time=t_attack,
        detector_time=t_detector,
        eval_time=t_eval,
        total_time=t_total,
        rss_memory_mb=rss_after,
        peak_memory_mb=peak_mb,
        python_alloc_mb=py_alloc,
        throughput_eps=throughput,
    )


def benchmark_graphsage_inference_on_graph(
    graph: ProvenanceGraph,
    poison_res: Any,
    t_load: float,
    t_attack: float,
    seed: int = 42,
) -> ScalabilityResult:
    """
    Benchmarks GraphSAGE inference performance, memory, and throughput on a given graph.
    """
    set_seed(seed)
    device = get_device()

    # Pre-convert to PyG Data
    pyg_data = provenance_to_pyg_data(poison_res.graph, poisoning_result=poison_res)
    in_channels = pyg_data.x.size(1) if pyg_data.x.dim() > 1 else 7
    model = GraphSAGEForTamperDetection(in_channels=in_channels, hidden_channels=64).to(device)
    model.eval()

    gc.collect()
    tracemalloc.start()
    rss_before, _ = get_memory_info_mb()

    t0 = time.time()
    with torch.no_grad():
        x_dev = pyg_data.x.to(device)
        edge_idx_dev = pyg_data.edge_index.to(device)
        _, edge_logits, _ = model(x_dev, edge_idx_dev)
        probs = torch.sigmoid(edge_logits).cpu().numpy()
        preds = (probs >= 0.5).astype(int)
    t_detector = time.time() - t0

    t1 = time.time()
    edge_id_map = getattr(pyg_data, "edge_id_map", {})
    flagged_ids = {edge_id_map[i] for i, p in enumerate(preds) if p == 1 and i in edge_id_map}
    evaluator = Evaluator()
    eval_res = evaluator.evaluate(
        ground_truth=poison_res,
        detected_violations=flagged_ids,
        graph=poison_res.graph,
    )
    t_eval = time.time() - t1

    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rss_after, py_alloc = get_memory_info_mb()
    peak_mb = max(peak_bytes / (1024.0 * 1024.0), rss_after - rss_before)

    num_edges = len(graph.edges)
    num_nodes = len(graph.nodes)
    throughput = num_edges / t_detector if t_detector > 0 else 0.0
    t_total = t_load + t_attack + t_detector + t_eval

    return ScalabilityResult(
        graph_size_edges=num_edges,
        graph_size_nodes=num_nodes,
        detector="GraphSAGE Inference",
        loading_time=t_load,
        attack_time=t_attack,
        detector_time=t_detector,
        eval_time=t_eval,
        total_time=t_total,
        rss_memory_mb=rss_after,
        peak_memory_mb=peak_mb,
        python_alloc_mb=py_alloc,
        throughput_eps=throughput,
    )


def run_scalability_benchmark(
    edge_scales: Sequence[int] = (10000, 25000, 50000, 100000, 250000),
    intensity: int = 5,
    seed: int = 42,
) -> List[ScalabilityResult]:
    """
    Executes scalability, memory, and throughput benchmarking over synthetic and DARPA graphs.
    """
    all_results: List[ScalabilityResult] = []

    print(f"[*] Starting Scalability & Memory Benchmark across edge scales: {list(edge_scales)}...")

    for num_edges in edge_scales:
        print(f"\n--- Benchmarking Graph Size: {num_edges:,} Edges ---")

        # 1. Load / Generate Graph
        t0 = time.time()
        # Scale nodes proportionately (~1 node per 2-4 edges)
        num_procs = max(10, num_edges // 1000)
        num_files = max(10, num_edges // 800)
        graph = generate_synthetic_graph(
            num_processes=num_procs,
            num_files=num_files,
            num_network=max(5, num_procs // 2),
            seed=seed,
        )
        t_load = time.time() - t0

        # 2. Inject Poisoning
        t1 = time.time()
        poison_res = inject_poisoning(
            graph,
            num_deletions=intensity,
            num_insertions=intensity,
            num_reorderings=intensity,
            num_forgeries=intensity,
            seed=seed,
        )
        t_attack = time.time() - t1

        # 3. Rule Engine Benchmark
        re_res = benchmark_rule_engine_on_graph(graph, poison_res, t_load, t_attack)
        all_results.append(re_res)
        print(f"  [Rule Engine] Edges: {re_res.graph_size_edges:,} | Time: {re_res.detector_time:.4f}s | Throughput: {re_res.throughput_eps:,.2f} eps | Peak Mem: {re_res.peak_memory_mb:.2f}MB")

        # 4. GraphSAGE Inference Benchmark
        gs_res = benchmark_graphsage_inference_on_graph(graph, poison_res, t_load, t_attack, seed=seed)
        all_results.append(gs_res)
        print(f"  [GraphSAGE]   Edges: {gs_res.graph_size_edges:,} | Time: {gs_res.detector_time:.4f}s | Throughput: {gs_res.throughput_eps:,.2f} eps | Peak Mem: {gs_res.peak_memory_mb:.2f}MB")

    return all_results


def generate_memory_csv(
    results: Sequence[ScalabilityResult],
    output_path: Path | str = "results/memory.csv",
) -> Path:
    """Generates results/memory.csv."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["Edges", "Nodes", "Detector", "RSSMemoryMB", "PeakMemoryMB", "PythonAllocMB"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            d = res.to_dict()
            writer.writerow({
                "Edges": d["Edges"],
                "Nodes": d["Nodes"],
                "Detector": d["Detector"],
                "RSSMemoryMB": d["RSSMemoryMB"],
                "PeakMemoryMB": d["PeakMemoryMB"],
                "PythonAllocMB": d["PythonAllocMB"],
            })

    return path


def generate_memory_md(
    results: Sequence[ScalabilityResult],
    output_path: Path | str = "results/memory.md",
) -> Path:
    """Generates results/memory.md."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Memory Footprint Benchmark Report",
        "",
        "| Graph Size (Edges) | Nodes | Detector | RSS Memory (MB) | Peak Memory (MB) | Python Alloc (MB) |",
        "|---|---|---|---|---|---|",
    ]

    for res in results:
        d = res.to_dict()
        lines.append(
            f"| {d['Edges']:,} | {d['Nodes']:,} | {d['Detector']} | "
            f"{d['RSSMemoryMB']:.2f} | {d['PeakMemoryMB']:.2f} | {d['PythonAllocMB']:.2f} |"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path


def generate_throughput_csv(
    results: Sequence[ScalabilityResult],
    output_path: Path | str = "results/throughput.csv",
) -> Path:
    """Generates results/throughput.csv."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["Edges", "Nodes", "Detector", "DetectorTimeSec", "ThroughputEPS"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            d = res.to_dict()
            writer.writerow({
                "Edges": d["Edges"],
                "Nodes": d["Nodes"],
                "Detector": d["Detector"],
                "DetectorTimeSec": d["DetectorTime"],
                "ThroughputEPS": d["ThroughputEPS"],
            })

    return path


def generate_throughput_md(
    results: Sequence[ScalabilityResult],
    output_path: Path | str = "results/throughput.md",
) -> Path:
    """Generates results/throughput.md."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Detection Throughput Benchmark Report",
        "",
        "| Graph Size (Edges) | Detector | Execution Time (s) | Throughput (Edges / Sec) |",
        "|---|---|---|---|",
    ]

    for res in results:
        d = res.to_dict()
        lines.append(
            f"| {d['Edges']:,} | {d['Detector']} | {d['DetectorTime']:.4f} | {d['ThroughputEPS']:,.2f} |"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path


def plot_runtime_vs_edges(
    results: Sequence[ScalabilityResult],
    output_path: Path | str = "results/runtime_vs_edges.png",
) -> Path:
    """Generates and saves runtime vs. graph size plot."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    re_res = [r for r in results if r.detector == "Rule Engine"]
    gs_res = [r for r in results if "GraphSAGE" in r.detector]

    plt.figure(figsize=(7, 5))
    if re_res:
        x_re = [r.graph_size_edges for r in re_res]
        y_re = [r.detector_time for r in re_res]
        plt.plot(x_re, y_re, "o-", color="#1f77b4", lw=2, label="Semantic Rule Engine")

    if gs_res:
        x_gs = [r.graph_size_edges for r in gs_res]
        y_gs = [r.detector_time for r in gs_res]
        plt.plot(x_gs, y_gs, "s--", color="#ff7f0e", lw=2, label="GraphSAGE Inference")

    plt.xlabel("Graph Size (Edges)", fontsize=12)
    plt.ylabel("Detector Execution Time (Seconds)", fontsize=12)
    plt.title("Execution Runtime Scaling vs. Graph Size", fontsize=14)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper left", fontsize=11)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    return path


def plot_memory_vs_edges(
    results: Sequence[ScalabilityResult],
    output_path: Path | str = "results/memory_vs_edges.png",
) -> Path:
    """Generates and saves peak memory footprint vs. graph size plot."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    re_res = [r for r in results if r.detector == "Rule Engine"]
    gs_res = [r for r in results if "GraphSAGE" in r.detector]

    plt.figure(figsize=(7, 5))
    if re_res:
        x_re = [r.graph_size_edges for r in re_res]
        y_re = [r.peak_memory_mb for r in re_res]
        plt.plot(x_re, y_re, "o-", color="#2ca02c", lw=2, label="Semantic Rule Engine")

    if gs_res:
        x_gs = [r.graph_size_edges for r in gs_res]
        y_gs = [r.peak_memory_mb for r in gs_res]
        plt.plot(x_gs, y_gs, "s--", color="#d62728", lw=2, label="GraphSAGE Inference")

    plt.xlabel("Graph Size (Edges)", fontsize=12)
    plt.ylabel("Peak Memory Footprint (MB)", fontsize=12)
    plt.title("Peak Memory Usage vs. Graph Size", fontsize=14)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper left", fontsize=11)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    return path


def plot_throughput_vs_edges(
    results: Sequence[ScalabilityResult],
    output_path: Path | str = "results/throughput_vs_edges.png",
) -> Path:
    """Generates and saves throughput vs. graph size plot."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    re_res = [r for r in results if r.detector == "Rule Engine"]
    gs_res = [r for r in results if "GraphSAGE" in r.detector]

    plt.figure(figsize=(7, 5))
    if re_res:
        x_re = [r.graph_size_edges for r in re_res]
        y_re = [r.throughput_eps for r in re_res]
        plt.plot(x_re, y_re, "o-", color="#9467bd", lw=2, label="Semantic Rule Engine")

    if gs_res:
        x_gs = [r.graph_size_edges for r in gs_res]
        y_gs = [r.throughput_eps for r in gs_res]
        plt.plot(x_gs, y_gs, "s--", color="#8c564b", lw=2, label="GraphSAGE Inference")

    plt.xlabel("Graph Size (Edges)", fontsize=12)
    plt.ylabel("Throughput (Edges / Second)", fontsize=12)
    plt.title("Detection Throughput vs. Graph Size", fontsize=14)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower right", fontsize=11)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    return path
