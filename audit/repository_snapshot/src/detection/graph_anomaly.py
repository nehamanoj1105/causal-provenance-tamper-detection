"""
Feature-based anomaly detection over provenance edges.

NOTE on scope: the original proposal specified GraphSAGE/GCN/Node2Vec for
this stage. torch + torch-geometric aren't in this environment yet, so this
first pass uses structural + temporal features per edge, scored with an
IsolationForest. It's a legitimate detector on its own and a natural
foundation to build on: swap `train_anomaly_detector`/`score_edges` for a
GNN later without touching graph_construction, poisoning_injection, or eval,
they all consume the same ProvenanceGraph/feature interface either way.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

from ..graph_construction.schema import ProvenanceEdge, ProvenanceGraph

FEATURE_NAMES = [
    "timestamp_gap_from_prev",  # time since the previous edge globally
    "source_out_degree",
    "target_in_degree",
    "is_first_edge_from_source",
    "edge_type_rarity",  # inverse frequency of this edge's type in the graph
]


def extract_edge_features(graph: ProvenanceGraph) -> tuple[list[str], np.ndarray]:
    """
    Returns (edge_ids, feature_matrix) with one row per edge, in the same
    order as edge_ids, aligned with FEATURE_NAMES columns.
    """
    edges_sorted = graph.edges_sorted_by_time()
    out_degree: dict[str, int] = {}
    in_degree: dict[str, int] = {}
    for e in graph.edges:
        out_degree[e.source_id] = out_degree.get(e.source_id, 0) + 1
        in_degree[e.target_id] = in_degree.get(e.target_id, 0) + 1

    type_counts: dict[str, int] = {}
    for e in graph.edges:
        type_counts[e.edge_type] = type_counts.get(e.edge_type, 0) + 1
    total_edges = max(len(graph.edges), 1)

    seen_sources: set[str] = set()
    edge_ids: list[str] = []
    rows: list[list[float]] = []
    prev_ts = None

    for edge in edges_sorted:
        gap = 0.0 if prev_ts is None else max(0.0, edge.timestamp - prev_ts)
        prev_ts = edge.timestamp

        is_first = 1.0 if edge.source_id not in seen_sources else 0.0
        seen_sources.add(edge.source_id)

        rarity = 1.0 - (type_counts.get(edge.edge_type, 0) / total_edges)

        edge_ids.append(edge.edge_id)
        rows.append(
            [
                gap,
                out_degree.get(edge.source_id, 0),
                in_degree.get(edge.target_id, 0),
                is_first,
                rarity,
            ]
        )

    return edge_ids, np.array(rows, dtype=float)


def train_anomaly_detector(feature_matrix: np.ndarray, contamination: float = 0.1) -> IsolationForest:
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(feature_matrix)
    return model


def score_edges(model: IsolationForest, feature_matrix: np.ndarray) -> np.ndarray:
    """Higher score = more anomalous (note: sklearn's raw decision_function
    is the opposite sign, we flip it here so callers don't have to remember)."""
    return -model.decision_function(feature_matrix)


def detect_anomalous_edges(
    graph: ProvenanceGraph, contamination: float = 0.1
) -> dict[str, float]:
    """
    Convenience wrapper: fits on the graph itself and returns edge_id ->
    anomaly_score for every edge. Only use this for quick exploration, it
    is methodologically weak for real evaluation: the model has seen the
    "normal" baseline it's supposed to be judging, which inflates results.
    Use detect_against_baseline() instead for anything you're reporting.
    """
    edge_ids, features = extract_edge_features(graph)
    if len(edge_ids) == 0:
        return {}
    model = train_anomaly_detector(features, contamination=contamination)
    scores = score_edges(model, features)
    return dict(zip(edge_ids, scores))


def detect_against_baseline(
    baseline_graph: ProvenanceGraph,
    target_graph: ProvenanceGraph,
    contamination: float = 0.1,
) -> dict[str, float]:
    """
    Trains the anomaly model on a clean baseline graph (establishing what
    "normal" looks like), then scores edges in a separate target graph
    (e.g. the poisoned version) against that baseline. This is the correct
    split for real evaluation, the model never sees the graph it's judging
    during training.
    """
    _, baseline_features = extract_edge_features(baseline_graph)
    if len(baseline_features) == 0:
        return {}
    model = train_anomaly_detector(baseline_features, contamination=contamination)

    target_edge_ids, target_features = extract_edge_features(target_graph)
    if len(target_edge_ids) == 0:
        return {}
    scores = score_edges(model, target_features)
    return dict(zip(target_edge_ids, scores))
