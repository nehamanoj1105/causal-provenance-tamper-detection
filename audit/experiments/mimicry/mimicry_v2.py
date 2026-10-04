"""
Corrected mimicry (camouflage) generator.

Fixes vs `src/detection/mimicry_attack.py`:
  1. Noise edges carry NO identifying attribute (the original tagged every
     noise edge with `{"mimicry": True}`, which leaks the attack condition to
     any detector that reads attributes).
  2. Every noise edge is *type-consistent* with the implemented invariants
     (process->file read/write/execute, process->process spawn,
     process->network connect), so benign camouflage does not itself violate
     a rule and manufacture false positives.
  3. Noise volume is defined as an exact fraction/count, reported exactly.
  4. The clean/poisoned ground truth is unchanged; camouflage is added on top
     of an already-poisoned graph.
"""
from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field

from src.detection.poisoning_injection import PoisoningResult
from src.graph_construction.schema import EdgeType, NodeType, ProvenanceEdge, ProvenanceGraph

STRENGTH_FRACTION = {
    "none": 0.0,
    "light": 0.25,
    "medium": 0.5,
    "heavy": 1.0,
}


@dataclass
class MimicryV2:
    graph: ProvenanceGraph
    base_poison: PoisoningResult
    strength: str
    num_noise_edges: int
    noise_ids: list[str] = field(default_factory=list)

    @property
    def events(self):
        return self.base_poison.events


def _node_type(graph, nid):
    return graph.nodes[nid].node_type


def generate_mimicry_v2(
    poisoned_graph: ProvenanceGraph,
    base_poison: PoisoningResult,
    strength: str = "medium",
    seed: int | None = None,
) -> MimicryV2:
    rng = random.Random(seed)
    g = ProvenanceGraph(
        nodes=dict(poisoned_graph.nodes),
        edges=[copy.deepcopy(e) for e in poisoned_graph.edges],
    )
    base_edges = len(poisoned_graph.edges)
    target = int(round(base_edges * STRENGTH_FRACTION.get(strength, 0.5)))

    procs = [n for n, x in g.nodes.items() if x.node_type == NodeType.PROCESS]
    files = [n for n, x in g.nodes.items() if x.node_type == NodeType.FILE]
    nets = [n for n, x in g.nodes.items() if x.node_type == NodeType.NETWORK]
    if not procs:
        procs = list(g.nodes.keys())
    if not files:
        files = list(g.nodes.keys())
    if not nets:
        nets = list(g.nodes.keys())

    ts_lo = min((e.timestamp for e in g.edges), default=0.0)
    ts_hi = max((e.timestamp for e in g.edges), default=1.0)

    # Traceable benign activity must not violate the temporal invariants:
    # a process cannot act before it was spawned. Record spawn times.
    spawn_time: dict[str, float] = {}
    for e in g.edges:
        if e.edge_type == EdgeType.SPAWN:
            spawn_time[e.target_id] = e.timestamp

    # Shape the noise distribution to match the graph's non-spawn edge-type mix.
    # SPAWN is excluded because adding a spawn edge overwrites the recorded
    # spawn time of a process in the temporal rules, which is itself a
    # structural confound rather than realistic background activity.
    shapes = [e.edge_type for e in poisoned_graph.edges
              if e.edge_type != EdgeType.SPAWN]
    if not shapes:
        shapes = [EdgeType.READ]

    noise_ids: list[str] = []
    chosen = []
    for i in range(target):
        et = rng.choice(shapes)
        if et in (EdgeType.READ, EdgeType.WRITE, EdgeType.EXECUTE, EdgeType.DELETE):
            src, tgt = rng.choice(procs), rng.choice(files)
        elif et == EdgeType.CONNECT:
            src, tgt = rng.choice(procs), rng.choice(nets)
        else:
            continue
        if src == tgt:
            continue
        lb = max(ts_lo, spawn_time.get(src, ts_lo))
        # offset keeps creation order monotone so the same-prefix
        # monotonicity invariant also holds, while every edge stays >= its
        # source process's spawn time.
        ts = lb + (ts_hi - lb) * (i + 1) / (target + 1) if ts_hi > lb else lb
        chosen.append((i, src, tgt, et, ts))

    for i, src, tgt, et, ts in chosen:
        eid = f"camouflage_{i}"
        g.edges.append(ProvenanceEdge(
            edge_id=eid, source_id=src, target_id=tgt,
            edge_type=et, timestamp=ts,
            attributes={},  # no attack-condition leak
        ))
        noise_ids.append(eid)

    return MimicryV2(g, base_poison, strength, len(noise_ids), noise_ids)


def count_rule_violations_in_noise(graph: ProvenanceGraph, noise_ids: list[str]) -> dict:
    """How many camouflage edges themselves trigger a rule (should be ~0)."""
    from src.detection.rule_engine import default_rule_engine
    noise = set(noise_ids)
    engine = default_rule_engine()
    results = engine.run(graph)
    hits = {}
    for r in results:
        c = sum(1 for v in r.violations if getattr(v, "edge_id", None) in noise)
        if c:
            hits[r.rule] = c
    return hits
