"""
PyTorch Geometric Data converter for ProvenanceGraph instances.

Converts ProvenanceGraph and optional PoisoningResult ground truth into
PyTorch Geometric Data objects supporting node features, edge indices,
edge features, and edge/node poisoning labels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    import torch
    from torch_geometric.data import Data

from src.graph_construction.schema import EdgeType, NodeType, ProvenanceGraph
from src.detection.poisoning_injection import PoisoningResult


NODE_TYPE_MAP: Dict[NodeType, int] = {
    NodeType.PROCESS: 0,
    NodeType.FILE: 1,
    NodeType.USER: 2,
    NodeType.NETWORK: 3,
}

EDGE_TYPE_MAP: Dict[EdgeType, int] = {
    EdgeType.READ: 0,
    EdgeType.WRITE: 1,
    EdgeType.EXECUTE: 2,
    EdgeType.CONNECT: 3,
    EdgeType.SPAWN: 4,
    EdgeType.DELETE: 5,
}


def provenance_to_pyg_data(
    graph: ProvenanceGraph,
    poisoning_result: Optional[PoisoningResult] = None,
    poisoned_edge_ids: Optional[set[str]] = None,
) -> Data:
    """
    Converts a ProvenanceGraph and optional poisoning labels into a PyTorch Geometric Data object.

    Args:
        graph: ProvenanceGraph schema instance.
        poisoning_result: Optional PoisoningResult containing ground-truth poisoning events.
        poisoned_edge_ids: Optional set of ground-truth poisoned edge IDs.

    Returns:
        PyTorch Geometric Data object with attributes:
            - x: Node feature tensor [N, num_node_features]
            - edge_index: Edge index tensor [2, E]
            - edge_attr: Edge feature tensor [E, num_edge_features]
            - edge_label: Binary ground-truth edge labels [E]
            - node_label: Binary ground-truth node labels [N]
            - node_id_map: Dictionary mapping string node_id -> integer index
            - edge_id_map: Dictionary mapping integer index -> string edge_id
    """
    import torch
    from torch_geometric.data import Data

    # Extract ground truth poisoned edge IDs
    gt_poisoned_ids: set[str] = set()
    if poisoning_result is not None:
        gt_poisoned_ids.update(poisoning_result.edge_labels().keys())
    if poisoned_edge_ids is not None:
        gt_poisoned_ids.update(poisoned_edge_ids)

    # 1. Map node IDs to 0-indexed integers
    node_ids: List[str] = list(graph.nodes.keys())
    node_to_idx: Dict[str, int] = {nid: idx for idx, nid in enumerate(node_ids)}
    num_nodes = len(node_ids)

    # Calculate node degrees
    in_degree = np.zeros(num_nodes, dtype=float)
    out_degree = np.zeros(num_nodes, dtype=float)

    for edge in graph.edges:
        if edge.source_id in node_to_idx:
            out_degree[node_to_idx[edge.source_id]] += 1.0
        if edge.target_id in node_to_idx:
            in_degree[node_to_idx[edge.target_id]] += 1.0

    # Build node feature matrix X
    # One-hot node_type (4) + out_degree (1) + in_degree (1) + total_degree (1) = 7 features
    x_features: List[List[float]] = []
    for idx, nid in enumerate(node_ids):
        node = graph.nodes[nid]
        type_idx = NODE_TYPE_MAP.get(node.node_type, 0)
        type_onehot = [0.0] * 4
        type_onehot[type_idx] = 1.0

        out_d = out_degree[idx]
        in_d = in_degree[idx]
        tot_d = out_d + in_d

        x_features.append(type_onehot + [out_d, in_d, tot_d])

    x_tensor = torch.tensor(x_features, dtype=torch.float) if x_features else torch.zeros((0, 7), dtype=torch.float)

    # 2. Build Edge Index & Edge Attributes & Edge Labels
    edge_src: List[int] = []
    edge_tgt: List[int] = []
    edge_features: List[List[float]] = []
    edge_labels: List[float] = []
    edge_id_map: Dict[int, str] = {}
    poisoned_nodes: set[int] = set()

    timestamps = [e.timestamp for e in graph.edges if e.timestamp is not None]
    min_ts = min(timestamps, default=0.0)
    max_ts = max(timestamps, default=1.0)
    ts_range = max_ts - min_ts if max_ts > min_ts else 1.0

    for idx, edge in enumerate(graph.edges):
        if edge.source_id not in node_to_idx or edge.target_id not in node_to_idx:
            continue

        src_idx = node_to_idx[edge.source_id]
        tgt_idx = node_to_idx[edge.target_id]

        edge_src.append(src_idx)
        edge_tgt.append(tgt_idx)
        edge_id_map[idx] = edge.edge_id

        # One-hot edge_type (6) + normalized timestamp (1) = 7 edge features
        etype_idx = EDGE_TYPE_MAP.get(edge.edge_type, 0)
        etype_onehot = [0.0] * 6
        etype_onehot[etype_idx] = 1.0

        norm_ts = (edge.timestamp - min_ts) / ts_range if edge.timestamp is not None else 0.0
        edge_features.append(etype_onehot + [norm_ts])

        # Poisoning label
        is_poisoned = 1.0 if edge.edge_id in gt_poisoned_ids else 0.0
        edge_labels.append(is_poisoned)
        if is_poisoned > 0.5:
            poisoned_nodes.add(src_idx)
            poisoned_nodes.add(tgt_idx)

    if edge_src:
        edge_index_tensor = torch.tensor([edge_src, edge_tgt], dtype=torch.long)
        edge_attr_tensor = torch.tensor(edge_features, dtype=torch.float)
        edge_label_tensor = torch.tensor(edge_labels, dtype=torch.float)
    else:
        edge_index_tensor = torch.zeros((2, 0), dtype=torch.long)
        edge_attr_tensor = torch.zeros((0, 7), dtype=torch.float)
        edge_label_tensor = torch.zeros((0,), dtype=torch.float)

    # 3. Node Labels (1 if incident to poisoned edge, else 0)
    node_labels = [1.0 if idx in poisoned_nodes else 0.0 for idx in range(num_nodes)]
    node_label_tensor = torch.tensor(node_labels, dtype=torch.float)

    # PyG Data object
    data = Data(
        x=x_tensor,
        edge_index=edge_index_tensor,
        edge_attr=edge_attr_tensor,
        edge_label=edge_label_tensor,
        node_label=node_label_tensor,
    )

    data.node_id_map = node_to_idx
    data.edge_id_map = edge_id_map

    return data
