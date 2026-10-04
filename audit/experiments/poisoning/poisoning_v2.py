"""
Corrected poisoning operators with immutable, well-defined ground truth.

Differences from the repository's `src/detection/poisoning_injection.py`:

1. Deep-copy semantics: the clean graph is *never* mutated. Asserted.
2. Every event records an immutable record with the original and modified state
   and an explicit `expected_detection_target`.
3. Reordering events that do not change the relative ordering with any neighbour
   are marked `effective=False` and excluded from the detectable-positive set.
4. Forgery and insertion are only counted as *detectable* when they actually
   violate a rule invariant (wrong-typed endpoint for the edge type); otherwise
   they are recorded as `detectable=False` (guaranteed false negatives).
5. Deletion is recorded with the removed edge id; detection is only possible if
   a rule can reconstruct/flag a dependent artifact, which is recorded.

Ground-truth records have the schema requested by the audit:
    {attack_id, attack_type, source_edge_or_entity, original_state,
     modified_state, expected_detection_target}
plus audit fields: effective, detectable, reason.

This module is additive; the original implementation is untouched.
"""
from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field

from src.graph_construction.schema import EdgeType, NodeType, ProvenanceEdge, ProvenanceGraph

# Which node type each edge type *requires* on the source side (invariant).
SOURCE_TYPE = {
    EdgeType.READ: NodeType.PROCESS,
    EdgeType.WRITE: NodeType.PROCESS,
    EdgeType.EXECUTE: NodeType.PROCESS,
    EdgeType.CONNECT: NodeType.PROCESS,
    EdgeType.SPAWN: NodeType.PROCESS,
    EdgeType.DELETE: NodeType.PROCESS,
}
TARGET_TYPE = {
    EdgeType.READ: NodeType.FILE,
    EdgeType.WRITE: NodeType.FILE,
    EdgeType.EXECUTE: NodeType.FILE,
    EdgeType.CONNECT: NodeType.NETWORK,
    EdgeType.SPAWN: NodeType.PROCESS,
    EdgeType.DELETE: NodeType.FILE,
}


@dataclass
class PoisonEvent:
    attack_id: str
    attack_type: str
    source_edge_or_entity: str
    original_state: dict
    modified_state: dict
    expected_detection_target: str | None
    effective: bool = True
    detectable: bool = True
    reason: str = ""

    def record(self) -> dict:
        return {
            "attack_id": self.attack_id,
            "attack_type": self.attack_type,
            "source_edge_or_entity": self.source_edge_or_entity,
            "original_state": self.original_state,
            "modified_state": self.modified_state,
            "expected_detection_target": self.expected_detection_target,
            "effective": self.effective,
            "detectable": self.detectable,
            "reason": self.reason,
        }


@dataclass
class PoisoningV2:
    clean_graph: ProvenanceGraph
    poisoned_graph: ProvenanceGraph
    events: list[PoisonEvent] = field(default_factory=list)

    def ground_truth_edge_ids(self) -> set[str]:
        """Edge ids that a detector is expected to flag (all effective positives)."""
        return {e.expected_detection_target for e in self.events
                if e.effective and e.expected_detection_target}

    def detectable_edge_ids(self) -> set[str]:
        return {e.expected_detection_target for e in self.events
                if e.effective and e.detectable and e.expected_detection_target}

    def records(self) -> list[dict]:
        return [e.record() for e in self.events]


def _edge_state(e: ProvenanceEdge) -> dict:
    return {
        "edge_id": e.edge_id,
        "source_id": e.source_id,
        "target_id": e.target_id,
        "edge_type": e.edge_type.value,
        "timestamp": e.timestamp,
    }


def _copy_graph(graph: ProvenanceGraph) -> ProvenanceGraph:
    return ProvenanceGraph(
        nodes={k: copy.deepcopy(v) for k, v in graph.nodes.items()},
        edges=[copy.deepcopy(e) for e in graph.edges],
    )


def _relative_order_changes(edges: list[ProvenanceEdge], edge: ProvenanceEdge,
                            clean_ts: float) -> bool:
    """True if shifting `edge` flips ordering with a neighbour sharing an endpoint."""
    for other in edges:
        if other.edge_id == edge.edge_id:
            continue
        if edge.source_id in (other.source_id, other.target_id) or \
           edge.target_id in (other.source_id, other.target_id):
            before = clean_ts <= other.timestamp
            after = edge.timestamp <= other.timestamp
            if before != after:
                return True
    return False


def inject_poisoning_v2(
    graph: ProvenanceGraph,
    num_deletions: int = 5,
    num_insertions: int = 5,
    num_reorderings: int = 5,
    num_forgeries: int = 5,
    seed: int | None = None,
    require_detectable: bool = True,
) -> PoisoningV2:
    """Corrected poisoning injection. Never mutates `graph`."""
    clean = _copy_graph(graph)
    poisoned = _copy_graph(graph)
    rng = random.Random(seed)
    events: list[PoisonEvent] = []
    counter = 0

    node_ids = list(poisoned.nodes.keys())
    node_types = {nid: poisoned.nodes[nid].node_type for nid in node_ids}

    # ---------- Deletion ----------
    deletable = list(poisoned.edges)
    rng.shuffle(deletable)
    for e in deletable[:num_deletions]:
        poisoned.edges.remove(e)
        counter += 1
        # A deleted edge cannot be matched by id in the final graph; detectable
        # only if a higher-level rule can reconstruct a dependent artifact.
        events.append(PoisonEvent(
            attack_id=f"d{counter}", attack_type="deletion",
            source_edge_or_entity=e.edge_id,
            original_state=_edge_state(e), modified_state={},
            expected_detection_target=e.edge_id,
            effective=True,
            detectable=False,
            reason="edge absent from final graph; no id-based match possible",
        ))

    # ---------- Insertion ----------
    for i in range(num_insertions):
        if len(node_ids) < 2:
            break
        # Make insertion malicious and well-defined: 50% wrong-typed source,
        # 50% wrong-typed target, so a type-consistency rule can fire.
        e = rng.choice(poisoned.edges)
        src, tgt = rng.sample(node_ids, 2)
        mode = rng.choice(["bad_source", "bad_target"])
        if mode == "bad_source":
            # pick a source whose type violates the invariant for e.edge_type
            bad = [n for n in node_ids if node_types[n] != SOURCE_TYPE[e.edge_type]]
            if bad:
                src = rng.choice(bad)
        else:
            bad = [n for n in node_ids if node_types[n] != TARGET_TYPE[e.edge_type]]
            if bad:
                tgt = rng.choice(bad)
        if src == tgt:
            continue
        ts = rng.uniform(min(x.timestamp for x in poisoned.edges),
                         max(x.timestamp for x in poisoned.edges))
        new = ProvenanceEdge(f"poisonv2_insert_{i}", src, tgt, e.edge_type, ts)
        poisoned.edges.append(new)
        counter += 1
        detectable = node_types[src] != SOURCE_TYPE[e.edge_type] or \
                     node_types[tgt] != TARGET_TYPE[e.edge_type]
        events.append(PoisonEvent(
            attack_id=f"i{counter}", attack_type="insertion",
            source_edge_or_entity=e.edge_id,
            original_state={}, modified_state=_edge_state(new),
            expected_detection_target=new.edge_id,
            effective=True, detectable=detectable,
            reason="" if detectable else "type-consistent insertion (benign-looking)",
        ))

    # ---------- Reordering ----------
    reorderable = [e for e in poisoned.edges if not e.edge_id.startswith("poisonv2_")]
    rng.shuffle(reorderable)
    done = 0
    for e in reorderable:
        if done >= num_reorderings:
            break
        clean_ts = e.timestamp
        shift = rng.uniform(-50.0, 50.0)
        e.timestamp = max(0.0, clean_ts + shift)
        effective = _relative_order_changes(poisoned.edges, e, clean_ts)
        if not effective:
            e.timestamp = clean_ts  # revert no-op reorder
            continue
        counter += 1
        done += 1
        events.append(PoisonEvent(
            attack_id=f"r{counter}", attack_type="reordering",
            source_edge_or_entity=e.edge_id,
            original_state={"timestamp": clean_ts},
            modified_state={"timestamp": e.timestamp},
            expected_detection_target=e.edge_id,
            effective=True, detectable=True,
            reason="relative order with a neighbour changed",
        ))

    # ---------- Dependency forgery ----------
    forgeable = [e for e in poisoned.edges
                 if e.edge_id not in {ev.expected_detection_target for ev in events}
                 and not e.edge_id.startswith("poisonv2_")]
    rng.shuffle(forgeable)
    done = 0
    for e in forgeable:
        if done >= num_forgeries:
            break
        orig_src = e.source_id
        # Prefer a same-type process (realistic) but require distinguishability
        # via lineage/type rules; else forge to a different-typed node.
        candidates = [n for n in node_ids if n not in (e.target_id,)]
        if require_detectable:
            bad = [n for n in candidates if node_types[n] != SOURCE_TYPE[e.edge_type]]
            if bad:
                candidates = bad
        new_src = rng.choice(candidates)
        e.source_id = new_src
        counter += 1
        done += 1
        detectable = node_types[new_src] != SOURCE_TYPE[e.edge_type]
        events.append(PoisonEvent(
            attack_id=f"f{counter}", attack_type="dependency_forgery",
            source_edge_or_entity=e.edge_id,
            original_state={"source_id": orig_src},
            modified_state={"source_id": new_src},
            expected_detection_target=e.edge_id,
            effective=True, detectable=detectable,
            reason="" if detectable else "forged source has consistent type",
        ))

    return PoisoningV2(clean_graph=clean, poisoned_graph=poisoned, events=events)


def assert_integrity(graph: ProvenanceGraph, result: PoisoningV2) -> list[str]:
    """Automated assertions that the clean graph is untouched and the poisoned
    graph differs exactly where intended. Returns a list of violations."""
    problems: list[str] = []
    clean = result.clean_graph
    # 1. clean graph equals the input
    if len(clean.edges) != len(graph.edges):
        problems.append("clean edge count mismatch")
    clean_state = {e.edge_id: _edge_state(e) for e in clean.edges}
    for e in graph.edges:
        if clean_state.get(e.edge_id) != _edge_state(e):
            problems.append(f"clean graph mutated at {e.edge_id}")
    # 2. poisoned diff matches events
    poisoned_state = {e.edge_id: _edge_state(e) for e in result.poisoned_graph.edges}
    for ev in result.events:
        tgt = ev.expected_detection_target
        if ev.attack_type == "deletion":
            if tgt in poisoned_state:
                problems.append(f"deleted edge {tgt} still present")
        elif ev.attack_type == "insertion":
            if tgt not in poisoned_state:
                problems.append(f"inserted edge {tgt} missing")
        elif ev.attack_type == "reordering":
            if tgt not in poisoned_state:
                problems.append(f"reordered edge {tgt} missing")
            elif abs(poisoned_state[tgt]["timestamp"] - ev.modified_state["timestamp"]) > 1e-9:
                problems.append(f"reordered edge {tgt} timestamp mismatch")
        elif ev.attack_type == "dependency_forgery":
            if tgt not in poisoned_state:
                problems.append(f"forged edge {tgt} missing")
            elif poisoned_state[tgt]["source_id"] != ev.modified_state["source_id"]:
                problems.append(f"forged edge {tgt} source mismatch")
    return problems
