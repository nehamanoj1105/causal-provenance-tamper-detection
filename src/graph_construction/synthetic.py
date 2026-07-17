"""
Generates synthetic provenance graphs that mimic the shape of real system
provenance (process trees, file access, network connections) so the rest of
the pipeline (poisoning injection, detection, evaluation) can be built and
tested without waiting on the DARPA dataset download.

This is scaffolding, not a substitute for real evaluation. Once Theia .bin
files are parsed via cdm_parser.py, swap this generator's output for real
parsed graphs, everything downstream (injection, detection, eval) consumes
the same ProvenanceGraph type either way.
"""

from __future__ import annotations

import random

from .schema import EdgeType, NodeType, ProvenanceEdge, ProvenanceGraph, ProvenanceNode


def generate_synthetic_graph(
    num_processes: int = 20,
    num_files: int = 30,
    num_network: int = 8,
    seed: int | None = None,
) -> ProvenanceGraph:
    """
    Builds a plausible-looking benign provenance graph:
    - a shallow process tree (init spawns children, children spawn grandchildren)
    - processes reading/writing a subset of files
    - a few processes making network connections
    All timestamps are monotonically increasing to keep the graph causally
    well-formed before any poisoning is injected.
    """
    rng = random.Random(seed)
    graph = ProvenanceGraph()
    t = 1_700_000_000.0

    # Root process
    graph.add_node(
        ProvenanceNode("proc_0", NodeType.PROCESS, "init", {"pid": 1})
    )

    process_ids = ["proc_0"]
    for i in range(1, num_processes):
        parent = rng.choice(process_ids)
        pid = f"proc_{i}"
        graph.add_node(
            ProvenanceNode(pid, NodeType.PROCESS, f"process_{i}", {"parent": parent})
        )
        t += rng.uniform(0.01, 2.0)
        graph.add_edge(
            ProvenanceEdge(f"e_spawn_{i}", parent, pid, EdgeType.SPAWN, t)
        )
        process_ids.append(pid)

    file_ids = []
    for i in range(num_files):
        fid = f"file_{i}"
        graph.add_node(
            ProvenanceNode(fid, NodeType.FILE, f"/var/tmp/file_{i}.dat")
        )
        file_ids.append(fid)

    net_ids = []
    for i in range(num_network):
        nid = f"net_{i}"
        graph.add_node(
            ProvenanceNode(nid, NodeType.NETWORK, f"10.0.0.{i}:443")
        )
        net_ids.append(nid)

    # Benign file/network activity
    num_activity_edges = (num_files + num_network) * 3
    for i in range(num_activity_edges):
        proc = rng.choice(process_ids)
        t += rng.uniform(0.001, 1.0)
        if rng.random() < 0.7 and file_ids:
            target = rng.choice(file_ids)
            edge_type = rng.choice([EdgeType.READ, EdgeType.WRITE])
        elif net_ids:
            target = rng.choice(net_ids)
            edge_type = EdgeType.CONNECT
        else:
            continue
        graph.add_edge(
            ProvenanceEdge(f"e_activity_{i}", proc, target, edge_type, t)
        )

    return graph
