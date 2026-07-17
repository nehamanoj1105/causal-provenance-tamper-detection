"""
Evaluation metrics for the poisoning detection pipeline.

Scoped to the two metrics that apply to detection (not survivability, which
is out of scope for this repo, see README):

- Provenance Integrity Score (PIS): Valid Edges / Total Edges
- Tamper Detection Rate (TDR): proportion of poisoned edges correctly flagged
"""

from __future__ import annotations

from dataclasses import dataclass

from ..graph_construction.schema import ProvenanceGraph


@dataclass
class DetectionMetrics:
    pis: float
    tdr: float
    precision: float
    false_positive_rate: float
    num_edges: int
    num_poisoned: int
    num_flagged: int
    num_true_positives: int


def compute_metrics(
    graph: ProvenanceGraph,
    poisoned_edge_ids: set[str],
    flagged_edge_ids: set[str],
) -> DetectionMetrics:
    all_edge_ids = {e.edge_id for e in graph.edges}
    num_edges = len(all_edge_ids)
    num_poisoned = len(poisoned_edge_ids & all_edge_ids) + len(
        poisoned_edge_ids - all_edge_ids  # deleted edges: not in graph anymore, still counted
    )

    true_positives = flagged_edge_ids & poisoned_edge_ids
    false_positives = flagged_edge_ids - poisoned_edge_ids
    benign_edges = all_edge_ids - poisoned_edge_ids

    valid_edges = num_edges - len(poisoned_edge_ids & all_edge_ids)
    pis = valid_edges / num_edges if num_edges else 0.0

    tdr = len(true_positives) / num_poisoned if num_poisoned else 0.0
    precision = len(true_positives) / len(flagged_edge_ids) if flagged_edge_ids else 0.0
    fpr = len(false_positives) / len(benign_edges) if benign_edges else 0.0

    return DetectionMetrics(
        pis=pis,
        tdr=tdr,
        precision=precision,
        false_positive_rate=fpr,
        num_edges=num_edges,
        num_poisoned=num_poisoned,
        num_flagged=len(flagged_edge_ids),
        num_true_positives=len(true_positives),
    )


def print_report(metrics: DetectionMetrics) -> None:
    print("Detection results")
    print(f"  edges in graph:        {metrics.num_edges}")
    print(f"  poisoning events:      {metrics.num_poisoned}")
    print(f"  edges flagged:         {metrics.num_flagged}")
    print(f"  true positives:        {metrics.num_true_positives}")
    print(f"  PIS (integrity score): {metrics.pis:.3f}")
    print(f"  TDR (detection rate):  {metrics.tdr:.3f}")
    print(f"  precision:             {metrics.precision:.3f}")
    print(f"  false positive rate:   {metrics.false_positive_rate:.3f}")
