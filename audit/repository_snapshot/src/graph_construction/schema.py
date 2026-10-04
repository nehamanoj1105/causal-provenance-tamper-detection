"""
Core data model for provenance graphs.

A provenance graph models causal relationships between system entities:
nodes are users, processes, files, and network endpoints; edges are the
operations connecting them (READ, WRITE, EXECUTE, CONNECT, SPAWN, DELETE).

This schema is intentionally independent of any specific raw log format
(e.g. TC/CDM, OpTC) so the parsers in this package can all normalize into
the same representation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class NodeType(str, Enum):
    PROCESS = "process"
    FILE = "file"
    USER = "user"
    NETWORK = "network"


class EdgeType(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    CONNECT = "connect"
    SPAWN = "spawn"
    DELETE = "delete"


@dataclass
class ProvenanceNode:
    node_id: str
    node_type: NodeType
    label: str  # e.g. process name, file path, IP:port
    attributes: dict = field(default_factory=dict)


@dataclass
class ProvenanceEdge:
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    timestamp: float  # unix epoch seconds
    attributes: dict = field(default_factory=dict)


@dataclass
class ProvenanceGraph:
    nodes: dict[str, ProvenanceNode] = field(default_factory=dict)
    edges: list[ProvenanceEdge] = field(default_factory=list)

    def add_node(self, node: ProvenanceNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: ProvenanceEdge) -> None:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError(
                f"Edge {edge.edge_id} references unknown node(s): "
                f"{edge.source_id} -> {edge.target_id}"
            )
        self.edges.append(edge)

    def edges_sorted_by_time(self) -> list[ProvenanceEdge]:
        return sorted(self.edges, key=lambda e: e.timestamp)

    def edges_from(self, node_id: str) -> list[ProvenanceEdge]:
        return [e for e in self.edges if e.source_id == node_id]

    def edges_to(self, node_id: str) -> list[ProvenanceEdge]:
        return [e for e in self.edges if e.target_id == node_id]
