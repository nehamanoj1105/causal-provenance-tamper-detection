"""
End-to-end pipeline, runnable right now on synthetic data:

    generate synthetic graph -> inject poisoning -> run rule-based checks
    -> run graph-feature anomaly detector -> combine -> evaluate (PIS, TDR)

Once real Theia data is downloaded and cdm_parser.py is verified against it,
swap generate_synthetic_graph() for parse_cdm_file() here, nothing else in
the pipeline needs to change, poisoning injection, detection, and eval all
operate on the same ProvenanceGraph type regardless of where it came from.

Run:
    python3 -m src.run_pipeline
"""

from __future__ import annotations

from src.detection.graph_anomaly import detect_against_baseline
from src.detection.poisoning_injection import inject_poisoning
from src.detection.rule_based import flagged_edge_ids as rule_based_flagged
from src.eval.metrics import compute_metrics, print_report
from src.graph_construction.synthetic import generate_synthetic_graph


def run(anomaly_score_threshold: float = 0.0, seed: int = 7) -> None:
    print("Generating synthetic benign provenance graph (baseline)...")
    baseline_graph = generate_synthetic_graph(
        num_processes=30, num_files=40, num_network=10, seed=seed
    )
    print(f"  {len(baseline_graph.nodes)} nodes, {len(baseline_graph.edges)} edges\n")

    print("Generating a second, separate benign graph to poison...")
    # Different seed: a different host/session, not the same graph the
    # anomaly detector trained on, otherwise the eval is testing the model
    # against data it already memorized.
    clean_graph = generate_synthetic_graph(
        num_processes=30, num_files=40, num_network=10, seed=seed + 1000
    )

    print("Injecting poisoning attacks...")
    result = inject_poisoning(
        clean_graph,
        num_deletions=6,
        num_insertions=6,
        num_reorderings=6,
        num_forgeries=6,
        seed=seed,
    )
    poisoned_graph = result.graph
    poisoned_ids = set(result.edge_labels().keys())
    by_type: dict[str, int] = {}
    for e in result.events:
        by_type[e.poisoning_type.value] = by_type.get(e.poisoning_type.value, 0) + 1
    print(f"  {len(result.events)} poisoning events injected: {by_type}")
    print(f"  poisoned graph now has {len(poisoned_graph.edges)} edges\n")

    print("Running rule-based causal consistency checks...")
    rule_flags = rule_based_flagged(poisoned_graph)
    print(f"  {len(rule_flags)} edges flagged by rules\n")

    print("Running graph-feature anomaly detector (trained on baseline, scored on poisoned)...")
    scores = detect_against_baseline(baseline_graph, poisoned_graph, contamination=0.15)
    anomaly_flags = {
        edge_id for edge_id, score in scores.items() if score > anomaly_score_threshold
    }
    print(f"  {len(anomaly_flags)} edges flagged by anomaly detector\n")

    combined_flags = rule_flags | anomaly_flags

    print("=" * 50)
    print("Rule-based only:")
    print_report(compute_metrics(poisoned_graph, poisoned_ids, rule_flags))
    print()
    print("Anomaly detector only:")
    print_report(compute_metrics(poisoned_graph, poisoned_ids, anomaly_flags))
    print()
    print("Combined (rules OR anomaly):")
    print_report(compute_metrics(poisoned_graph, poisoned_ids, combined_flags))
    print("=" * 50)


if __name__ == "__main__":
    run()
