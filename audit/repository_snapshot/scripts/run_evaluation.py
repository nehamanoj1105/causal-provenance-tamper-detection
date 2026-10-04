#!/usr/bin/env python3
"""
Runs the complete Phase 6 evaluation pipeline across single or multiple random seeds and attack types:

    Load graph -> Inject poisoning -> Run rule engine -> Evaluate -> Measure Runtimes -> Generate Reports

Usage:
    python3 scripts/run_evaluation.py --attack-type all --multiple-seeds
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Sequence

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.detection.poisoning_injection import (
    inject_poisoning,
    targeted_deletion,
    targeted_dependency_forgery,
    targeted_insertion,
    targeted_reordering,
)
from src.detection.rule_engine import default_rule_engine
from src.eval.evaluator import Evaluator, EvaluationResult, RuntimeMetrics
from src.eval.metrics import aggregate_seed_statistics
from src.eval.report import generate_all_reports
from src.graph_construction.converter import dataframe_to_schema
from src.graph_construction.graph_loader import dataset_exists, load_graph
from src.graph_construction.synthetic import generate_synthetic_graph

DEFAULT_SEEDS = [1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]
ATTACK_TYPES = [
    "random_deletion",
    "random_insertion",
    "random_reordering",
    "random_dependency_forgery",
    "targeted_deletion",
    "targeted_insertion",
    "targeted_reordering",
    "targeted_dependency_forgery",
]


def load_evaluation_graph(dataset: str, seed: int = 42):
    """
    Loads graph by dataset name (e.g. 'synthetic' or parsed dataset).
    """
    if dataset.lower() == "synthetic" or not dataset_exists(dataset):
        return generate_synthetic_graph(
            num_processes=30,
            num_files=40,
            num_network=10,
            seed=seed,
        )

    df_graph = load_graph(dataset)
    return dataframe_to_schema(df_graph)


def run_single_eval(
    dataset: str = "synthetic",
    attack_type: str = "all",
    seed: int = 42,
    intensity: int = 5,
) -> EvaluationResult:
    """
    Executes a single evaluation run with timing metrics.
    """
    t_start = time.time()

    # 1. Load Graph
    t0 = time.time()
    graph = load_evaluation_graph(dataset, seed=seed)
    t_load = time.time() - t0

    # 2. Inject Poisoning Attack
    t1 = time.time()
    atk_key = attack_type.lower()
    target_node = list(graph.nodes.keys())[0] if graph.nodes else "node_0"

    if atk_key in ("all", "all_random"):
        poison_res = inject_poisoning(
            graph,
            num_deletions=intensity,
            num_insertions=intensity,
            num_reorderings=intensity,
            num_forgeries=intensity,
            seed=seed,
        )
    elif atk_key in ("deletion", "random_deletion"):
        poison_res = inject_poisoning(graph, num_deletions=intensity, num_insertions=0, num_reorderings=0, num_forgeries=0, seed=seed)
    elif atk_key in ("insertion", "random_insertion"):
        poison_res = inject_poisoning(graph, num_deletions=0, num_insertions=intensity, num_reorderings=0, num_forgeries=0, seed=seed)
    elif atk_key in ("reordering", "random_reordering"):
        poison_res = inject_poisoning(graph, num_deletions=0, num_insertions=0, num_reorderings=intensity, num_forgeries=0, seed=seed)
    elif atk_key in ("dependency_forgery", "random_dependency_forgery"):
        poison_res = inject_poisoning(graph, num_deletions=0, num_insertions=0, num_reorderings=0, num_forgeries=intensity, seed=seed)
    elif atk_key == "targeted_deletion":
        poison_res = targeted_deletion(graph, target_node=target_node, max_edges=intensity, seed=seed)
    elif atk_key == "targeted_dependency_forgery":
        poison_res = targeted_dependency_forgery(graph, target_node=target_node, max_edges=intensity, seed=seed)
    elif atk_key == "targeted_insertion":
        poison_res = targeted_insertion(graph, target_node=target_node, max_insertions=intensity, seed=seed)
    elif atk_key == "targeted_reordering":
        poison_res = targeted_reordering(graph, target_node=target_node, max_swaps=intensity, seed=seed)
    else:
        raise ValueError(f"Unsupported attack type: {attack_type}")

    t_inject = time.time() - t1

    # 3. Run Semantic Rule Engine
    t2 = time.time()
    engine = default_rule_engine()
    rule_results = engine.run(poison_res.graph)
    t_engine = time.time() - t2

    # 4. Evaluate
    t3 = time.time()
    evaluator = Evaluator()
    t_total = time.time() - t_start
    t_eval = time.time() - t3

    runtime_metrics = RuntimeMetrics(
        graph_loading_time=t_load,
        attack_injection_time=t_inject,
        rule_engine_runtime=t_engine,
        evaluation_runtime=t_eval,
        total_runtime=t_total,
    )

    eval_res = evaluator.evaluate(
        ground_truth=poison_res,
        detected_violations=rule_results,
        graph=poison_res.graph,
        dataset=dataset,
        attack_type=attack_type,
        seed=seed,
        runtime_metrics=runtime_metrics,
    )

    return eval_res


def run_evaluation(
    dataset: str = "synthetic",
    attack_type: str = "all",
    seeds: Sequence[int] = (42,),
    intensity: int = 5,
    output_dir: str = "results",
) -> list[EvaluationResult]:
    """
    Executes Phase 6 evaluation across attack types and seeds.
    """
    all_results: list[EvaluationResult] = []

    if attack_type.lower() == "all_attacks":
        attacks_to_run = ATTACK_TYPES
    elif attack_type.lower() == "all":
        attacks_to_run = ["all"]
    else:
        attacks_to_run = [attack_type]

    print(f"[*] Starting Phase 6 Evaluation (dataset='{dataset}', attacks={attacks_to_run}, seeds={list(seeds)})...")

    for atk in attacks_to_run:
        for s in seeds:
            res = run_single_eval(dataset=dataset, attack_type=atk, seed=s, intensity=intensity)
            all_results.append(res)

    # Compute seed statistics per attack
    by_attack: dict[str, list[EvaluationResult]] = {}
    for r in all_results:
        by_attack.setdefault(r.attack_type, []).append(r)

    stats_per_attack = {
        atk: aggregate_seed_statistics([r.metrics for r in res_group])
        for atk, res_group in by_attack.items()
    }

    # Generate Reports
    print(f"[*] Generating Phase 6 evaluation reports under '{output_dir}/'...")
    report_paths = generate_all_reports(all_results, stats_per_attack=stats_per_attack, results_dir=output_dir)

    print("\n" + "=" * 60)
    print("SEED STATISTICS SUMMARY (Mean ± Std)")
    print("=" * 60)
    for atk, st in stats_per_attack.items():
        print(f"  {atk:30s} | Precision: {st.precision_mean:.4f} ± {st.precision_std:.4f} | Recall: {st.recall_mean:.4f} ± {st.recall_std:.4f} | F1: {st.f1_mean:.4f} ± {st.f1_std:.4f}")

    print("\nREPORTS GENERATED:")
    for name, p in report_paths.items():
        print(f"  [{name.upper()}] {p}")

    print("\n[+] Phase 6 evaluation completed successfully.")
    return all_results


def main():
    parser = argparse.ArgumentParser(description="Phase 6 Provenance Graph Tamper Detection Evaluation Pipeline")
    parser.add_argument("--dataset", type=str, default="synthetic", help="Dataset name or 'synthetic'")
    parser.add_argument("--attack-type", "--attack", type=str, default="all", help="Attack type (all, deletion, insertion, reordering, dependency_forgery, targeted_deletion, etc., or all_attacks)")
    parser.add_argument("--seed", type=int, default=42, help="Single random seed (default: 42)")
    parser.add_argument("--seeds", type=str, default="", help="Comma-separated random seeds (e.g. 1,7,13)")
    parser.add_argument("--multiple-seeds", action="store_true", help="Run evaluation across default 10 random seeds")
    parser.add_argument("--intensity", "--num-attacks", type=int, default=5, help="Number of attacks to inject per type")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory for output report files")

    args = parser.parse_args()

    if args.multiple_seeds:
        seeds = DEFAULT_SEEDS
    elif args.seeds:
        seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    else:
        seeds = [args.seed]

    run_evaluation(
        dataset=args.dataset,
        attack_type=args.attack_type,
        seeds=seeds,
        intensity=args.intensity,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
