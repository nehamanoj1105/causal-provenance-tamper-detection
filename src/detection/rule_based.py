"""
Rule-based provenance poisoning detection via causal consistency checks.

These are deterministic checks, not learned, they catch violations of rules
that should always hold in a causally valid provenance graph. This is meant
to run alongside (not instead of) the graph-feature anomaly detector in
graph_anomaly.py: rules catch clear-cut violations cheaply, the anomaly
detector catches subtler statistical deviations rules don't cover.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..graph_construction.schema import EdgeType, ProvenanceEdge, ProvenanceGraph


@dataclass
class ConsistencyViolation:
    edge_id: str
    rule: str
    detail: str


def check_temporal_consistency(graph: ProvenanceGraph) -> list[ConsistencyViolation]:
    """
    A process cannot act (READ/WRITE/EXECUTE/CONNECT/DELETE) before the
    SPAWN edge that created it. Flags any non-SPAWN edge whose source
    process has a timestamp earlier than its own SPAWN edge.
    """
    violations = []
    spawn_time: dict[str, float] = {}
    for edge in graph.edges:
        if edge.edge_type == EdgeType.SPAWN:
            spawn_time[edge.target_id] = edge.timestamp

    for edge in graph.edges:
        if edge.edge_type == EdgeType.SPAWN:
            continue
        created_at = spawn_time.get(edge.source_id)
        if created_at is not None and edge.timestamp < created_at:
            violations.append(
                ConsistencyViolation(
                    edge.edge_id,
                    "temporal_consistency",
                    f"edge at {edge.timestamp:.2f} predates process spawn at {created_at:.2f}",
                )
            )
    return violations


def check_process_lineage(graph: ProvenanceGraph) -> list[ConsistencyViolation]:
    """
    Flags SPAWN edges that create a cycle in the process tree (a process
    can't be its own ancestor) or that reference a parent not present in
    the graph.
    """
    violations = []
    parent_of: dict[str, str] = {}
    for edge in graph.edges:
        if edge.edge_type == EdgeType.SPAWN:
            parent_of[edge.target_id] = edge.source_id

    for child, parent in parent_of.items():
        seen = {child}
        current = parent
        depth = 0
        while current is not None and depth < len(parent_of) + 1:
            if current in seen:
                violations.append(
                    ConsistencyViolation(
                        edge_id=f"spawn->{child}",
                        rule="process_lineage",
                        detail=f"cycle detected in process ancestry involving {current}",
                    )
                )
                break
            seen.add(current)
            current = parent_of.get(current)
            depth += 1
    return violations


def check_dangling_edges(graph: ProvenanceGraph) -> list[ConsistencyViolation]:
    """
    Flags edges whose source or target node isn't present in the graph,
    a signature of deletion attacks that removed a node but left dependent
    edges behind, or forgery attacks pointing at a nonexistent entity.
    """
    violations = []
    for edge in graph.edges:
        if edge.source_id not in graph.nodes:
            violations.append(
                ConsistencyViolation(edge.edge_id, "dangling_edge", f"missing source {edge.source_id}")
            )
        if edge.target_id not in graph.nodes:
            violations.append(
                ConsistencyViolation(edge.edge_id, "dangling_edge", f"missing target {edge.target_id}")
            )
    return violations


def check_duplicate_edges(graph: ProvenanceGraph) -> list[ConsistencyViolation]:
    """
    Flags multiple edges with identical (source, target, type, timestamp),
    a plausible artifact of insertion attacks that clone an existing edge
    rather than fabricating a fully novel one.
    """
    violations = []
    seen: dict[tuple, str] = {}
    for edge in graph.edges:
        key = (edge.source_id, edge.target_id, edge.edge_type, round(edge.timestamp, 3))
        if key in seen:
            violations.append(
                ConsistencyViolation(
                    edge.edge_id, "duplicate_edge", f"duplicates edge {seen[key]}"
                )
            )
        else:
            seen[key] = edge.edge_id
    return violations


def run_all_checks(graph: ProvenanceGraph) -> list[ConsistencyViolation]:
    violations = []
    violations += check_temporal_consistency(graph)
    violations += check_process_lineage(graph)
    violations += check_dangling_edges(graph)
    violations += check_duplicate_edges(graph)
    return violations


def flagged_edge_ids(graph: ProvenanceGraph) -> set[str]:
    return {v.edge_id for v in run_all_checks(graph)}
