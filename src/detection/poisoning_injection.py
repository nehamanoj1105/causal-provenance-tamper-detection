"""
Injects provenance poisoning attacks into a ProvenanceGraph and returns
ground-truth labels alongside the poisoned graph, this is what the detection
and evaluation modules are scored against.

Four attack types, matching the proposal's Phase 4 scope:
- deletion: remove an edge, as if an attacker erased a log entry
- insertion: add a fabricated edge that didn't causally happen
- reordering: shift an edge's timestamp out of its true causal position
- dependency_forgery: rewire an edge's source or target to a different node,
  attributing an action to the wrong actor
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from ..graph_construction.schema import ProvenanceEdge, ProvenanceGraph


class PoisoningType(str, Enum):
    DELETION = "deletion"
    INSERTION = "insertion"
    REORDERING = "reordering"
    DEPENDENCY_FORGERY = "dependency_forgery"


@dataclass
class PoisoningEvent:
    poisoning_type: PoisoningType
    edge_id: str
    details: dict = field(default_factory=dict)


@dataclass
class PoisoningResult:
    graph: ProvenanceGraph
    events: list[PoisoningEvent]

    def edge_labels(self) -> dict[str, str]:
        """Maps edge_id -> poisoning_type for every edge touched by an attack.
        Edges not in this dict are benign/untouched."""
        return {e.edge_id: e.poisoning_type.value for e in self.events}


def inject_poisoning(
    graph: ProvenanceGraph,
    num_deletions: int = 5,
    num_insertions: int = 5,
    num_reorderings: int = 5,
    num_forgeries: int = 5,
    seed: int | None = None,
) -> PoisoningResult:
    """
    Returns a NEW PoisoningResult, does not mutate the input graph.
    """
    rng = random.Random(seed)
    events: list[PoisoningEvent] = []

    # Work on a copy so the caller's original (clean) graph stays untouched,
    # useful for computing recall against ground truth later.
    poisoned = ProvenanceGraph(
        nodes=dict(graph.nodes),
        edges=list(graph.edges),
    )

    node_ids = list(poisoned.nodes.keys())

    # --- Deletion ---
    deletable = list(poisoned.edges)
    rng.shuffle(deletable)
    for edge in deletable[:num_deletions]:
        poisoned.edges.remove(edge)
        events.append(
            PoisoningEvent(
                PoisoningType.DELETION,
                edge.edge_id,
                {"removed_source": edge.source_id, "removed_target": edge.target_id},
            )
        )

    # --- Insertion ---
    for i in range(num_insertions):
        if len(node_ids) < 2:
            break
        src, tgt = rng.sample(node_ids, 2)
        fake_edge_type = rng.choice(list(poisoned.edges)).edge_type if poisoned.edges else None
        if fake_edge_type is None:
            break
        # Insert at a plausible-looking but fabricated timestamp
        fake_ts = rng.uniform(
            min((e.timestamp for e in poisoned.edges), default=0),
            max((e.timestamp for e in poisoned.edges), default=1),
        )
        fake_edge = ProvenanceEdge(
            edge_id=f"poison_insert_{i}",
            source_id=src,
            target_id=tgt,
            edge_type=fake_edge_type,
            timestamp=fake_ts,
        )
        poisoned.edges.append(fake_edge)
        events.append(
            PoisoningEvent(PoisoningType.INSERTION, fake_edge.edge_id)
        )

    # --- Reordering ---
    reorderable = [e for e in poisoned.edges if not e.edge_id.startswith("poison_")]
    rng.shuffle(reorderable)
    for edge in reorderable[:num_reorderings]:
        original_ts = edge.timestamp
        # Shift far enough to plausibly violate causal ordering (e.g. a WRITE
        # appearing before the SPAWN that created the writing process).
        shift = rng.uniform(-50.0, 50.0)
        edge.timestamp = max(0.0, original_ts + shift)
        events.append(
            PoisoningEvent(
                PoisoningType.REORDERING,
                edge.edge_id,
                {"original_timestamp": original_ts, "new_timestamp": edge.timestamp},
            )
        )

    # --- Dependency forgery ---
    forgeable = [
        e for e in poisoned.edges
        if e.edge_id not in {ev.edge_id for ev in events}
    ]
    rng.shuffle(forgeable)
    for edge in forgeable[:num_forgeries]:
        if len(node_ids) < 2:
            break
        original_source = edge.source_id
        new_source = rng.choice([n for n in node_ids if n != edge.target_id])
        edge.source_id = new_source
        events.append(
            PoisoningEvent(
                PoisoningType.DEPENDENCY_FORGERY,
                edge.edge_id,
                {"original_source": original_source, "forged_source": new_source},
            )
        )

    return PoisoningResult(graph=poisoned, events=events)
