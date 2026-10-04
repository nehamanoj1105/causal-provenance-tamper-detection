"""
Adversarial mimicry attack generator for provenance graph tamper detection framework.

Injects benign-looking camouflage events to hide malicious/poisoned activity
while preserving node degree distributions, edge type frequencies, and timestamp distributions.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.detection.poisoning_injection import PoisoningEvent, PoisoningResult, PoisoningType, inject_poisoning
from src.graph_construction.schema import EdgeType, NodeType, ProvenanceEdge, ProvenanceGraph, ProvenanceNode


class MimicryStrength(str, Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


@dataclass
class MimicryAttackResult:
    """Result object containing camouflaged poisoned graph and noise metadata."""

    poison_res: PoisoningResult
    num_noise_edges: int
    mimicry_strength: str
    camouflaged_edge_ids: list[str] = field(default_factory=list)

    @property
    def graph(self) -> ProvenanceGraph:
        return self.poison_res.graph

    @property
    def events(self) -> list[PoisoningEvent]:
        return self.poison_res.events


def _calculate_graph_stats(graph: ProvenanceGraph) -> dict[str, Any]:
    """Computes node degree distributions, edge type frequencies, and timestamp range."""
    in_deg: dict[str, int] = {}
    out_deg: dict[str, int] = {}
    edge_type_counts: dict[str, int] = {}
    timestamps: list[float] = []

    for node_id in graph.nodes:
        in_deg[node_id] = 0
        out_deg[node_id] = 0

    for edge in graph.edges:
        out_deg[edge.source_id] = out_deg.get(edge.source_id, 0) + 1
        in_deg[edge.target_id] = in_deg.get(edge.target_id, 0) + 1

        etype = edge.edge_type.value if hasattr(edge.edge_type, "value") else str(edge.edge_type)
        edge_type_counts[etype] = edge_type_counts.get(etype, 0) + 1
        timestamps.append(edge.timestamp)

    min_ts = min(timestamps) if timestamps else 0.0
    max_ts = max(timestamps) if timestamps else 1.0

    tot_edges = len(graph.edges)
    type_ratios = {k: v / tot_edges for k, v in edge_type_counts.items()} if tot_edges > 0 else {}

    return {
        "in_deg": in_deg,
        "out_deg": out_deg,
        "edge_type_counts": edge_type_counts,
        "type_ratios": type_ratios,
        "min_ts": min_ts,
        "max_ts": max_ts,
    }


def inject_mimicry_attack(
    graph: ProvenanceGraph,
    base_poisoning: Optional[PoisoningResult] = None,
    strength: str | MimicryStrength = MimicryStrength.MEDIUM,
    intensity: int = 5,
    seed: int | None = None,
) -> MimicryAttackResult:
    """
    Injects adversarial mimicry camouflage around poisoned events in a provenance graph.

    - Preserves background edge type ratios and degree distributions.
    - Inserts fake reads, fake writes, fake process chains, and fake network activity.
    - Pads sequence gaps and timestamp ranges to mask malicious anomalies.

    Does not modify the original input graph. Returns a new MimicryAttackResult.
    """
    rng = random.Random(seed)
    strength_str = strength.value if isinstance(strength, MimicryStrength) else str(strength).lower()

    # 1. Obtain Base Poisoning Result
    if base_poisoning is None:
        base_poisoning = inject_poisoning(
            graph,
            num_deletions=intensity,
            num_insertions=intensity,
            num_reorderings=intensity,
            num_forgeries=intensity,
            seed=seed,
        )

    # Clone base poisoned graph
    camouflaged_graph = ProvenanceGraph(
        nodes=dict(base_poisoning.graph.nodes),
        edges=[copy.deepcopy(e) for e in base_poisoning.graph.edges],
    )

    stats = _calculate_graph_stats(graph)
    min_ts, max_ts = stats["min_ts"], stats["max_ts"]

    # 2. Determine Noise Volume
    tot_base_edges = len(graph.edges)
    if strength_str == "light":
        noise_target = max(10, int(tot_base_edges * 0.3))
    elif strength_str == "heavy":
        noise_target = max(30, int(tot_base_edges * 1.5))
    else:  # medium
        noise_target = max(20, int(tot_base_edges * 0.7))

    noise_edges: list[ProvenanceEdge] = []
    noise_ids: list[str] = []

    # Categorize nodes
    proc_nodes = [nid for nid, n in camouflaged_graph.nodes.items() if (n.node_type.value if hasattr(n.node_type, "value") else str(n.node_type)).lower() == "process"]
    file_nodes = [nid for nid, n in camouflaged_graph.nodes.items() if (n.node_type.value if hasattr(n.node_type, "value") else str(n.node_type)).lower() == "file"]
    net_nodes = [nid for nid, n in camouflaged_graph.nodes.items() if (n.node_type.value if hasattr(n.node_type, "value") else str(n.node_type)).lower() == "network"]

    if not proc_nodes:
        proc_nodes = list(camouflaged_graph.nodes.keys())
    if not file_nodes:
        file_nodes = list(camouflaged_graph.nodes.keys())
    if not net_nodes:
        net_nodes = list(camouflaged_graph.nodes.keys())

    # 3. Camouflage Operations
    noise_idx = 0

    # (A) Fake Reads & Writes (File Access Camouflage)
    num_file_ops = noise_target // 3
    for _ in range(num_file_ops):
        src = rng.choice(proc_nodes)
        tgt = rng.choice(file_nodes)
        etype = rng.choice([EdgeType.READ, EdgeType.WRITE])
        ts = rng.uniform(min_ts, max_ts)
        eid = f"mimicry_file_{noise_idx}"

        edge = ProvenanceEdge(
            edge_id=eid,
            source_id=src,
            target_id=tgt,
            edge_type=etype,
            timestamp=ts,
            attributes={"mimicry": True, "op": "fake_file_access"},
        )
        noise_edges.append(edge)
        noise_ids.append(eid)
        noise_idx += 1

    # (B) Fake Process Chains (Process Spawn Camouflage)
    num_spawns = noise_target // 4
    for _ in range(num_spawns):
        if len(proc_nodes) >= 2:
            src, tgt = rng.sample(proc_nodes, 2)
        else:
            src = proc_nodes[0]
            tgt = proc_nodes[0]

        ts = rng.uniform(min_ts, max_ts)
        eid = f"mimicry_spawn_{noise_idx}"

        edge = ProvenanceEdge(
            edge_id=eid,
            source_id=src,
            target_id=tgt,
            edge_type=EdgeType.SPAWN,
            timestamp=ts,
            attributes={"mimicry": True, "op": "fake_process_chain"},
        )
        noise_edges.append(edge)
        noise_ids.append(eid)
        noise_idx += 1

    # (C) Fake Network Activity (Network Socket Camouflage)
    num_net = noise_target // 4
    for _ in range(num_net):
        src = rng.choice(proc_nodes)
        tgt = rng.choice(net_nodes)
        ts = rng.uniform(min_ts, max_ts)
        eid = f"mimicry_net_{noise_idx}"

        edge = ProvenanceEdge(
            edge_id=eid,
            source_id=src,
            target_id=tgt,
            edge_type=EdgeType.CONNECT,
            timestamp=ts,
            attributes={"mimicry": True, "op": "fake_network_activity"},
        )
        noise_edges.append(edge)
        noise_ids.append(eid)
        noise_idx += 1

    # (D) Activity Padding & Sequence Monotonicity Noise
    rem_noise = noise_target - len(noise_edges)
    all_node_ids = list(camouflaged_graph.nodes.keys())
    for _ in range(max(0, rem_noise)):
        if len(all_node_ids) >= 2:
            src, tgt = rng.sample(all_node_ids, 2)
        else:
            src = all_node_ids[0]
            tgt = all_node_ids[0]

        etype = rng.choice(list(EdgeType))
        ts = rng.uniform(min_ts, max_ts)
        eid = f"mimicry_pad_{noise_idx}"

        edge = ProvenanceEdge(
            edge_id=eid,
            source_id=src,
            target_id=tgt,
            edge_type=etype,
            timestamp=ts,
            attributes={"mimicry": True, "op": "activity_padding"},
        )
        noise_edges.append(edge)
        noise_ids.append(eid)
        noise_idx += 1

    # Add all noise edges to graph
    for ne in noise_edges:
        camouflaged_graph.edges.append(ne)

    # 4. Construct Final Result
    final_poison_res = PoisoningResult(
        graph=camouflaged_graph,
        events=base_poisoning.events,
    )

    return MimicryAttackResult(
        poison_res=final_poison_res,
        num_noise_edges=len(noise_edges),
        mimicry_strength=strength_str,
        camouflaged_edge_ids=noise_ids,
    )
