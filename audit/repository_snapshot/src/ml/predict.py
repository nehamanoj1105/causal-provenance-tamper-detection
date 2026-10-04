"""
Inference module for predicting tampered edges and nodes using trained GraphSAGE model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Tuple

import torch

if TYPE_CHECKING:
    from torch_geometric.data import Data

from src.ml.graphsage import GraphSAGEForTamperDetection
from src.ml.utils import get_device


def predict_edges(
    model: GraphSAGEForTamperDetection,
    data: Data,
    threshold: float = 0.5,
    device: torch.device | None = None,
) -> Dict[str, Any]:
    """
    Predicts tampered edges for a provenance graph Data object at specified threshold.

    Args:
        model: Trained GraphSAGEForTamperDetection model.
        data: PyG Data object.
        threshold: Decision probability threshold.
        device: PyTorch device.

    Returns:
        Dictionary containing:
            - edge_probs: Array of edge tamper probabilities [E]
            - edge_preds: Array of binary edge predictions [E]
            - flagged_edge_ids: Set of string edge IDs predicted as tampered
            - edge_id_map: Mapping from edge index -> edge_id string
    """
    if device is None:
        device = get_device()

    model.eval()
    model.to(device)

    with torch.no_grad():
        x = data.x.to(device)
        edge_index = data.edge_index.to(device)

        _, edge_logits, _ = model(x, edge_index)
        probs = torch.sigmoid(edge_logits).cpu().numpy()
        preds = (probs >= threshold).astype(int)

    edge_id_map = getattr(data, "edge_id_map", {})
    flagged_edge_ids = {
        edge_id_map[idx]
        for idx, pred in enumerate(preds)
        if pred == 1 and idx in edge_id_map
    }

    return {
        "edge_probs": probs,
        "edge_preds": preds,
        "flagged_edge_ids": flagged_edge_ids,
        "edge_id_map": edge_id_map,
        "threshold": threshold,
    }


def predict_nodes(
    model: GraphSAGEForTamperDetection,
    data: Data,
    threshold: float = 0.5,
    device: torch.device | None = None,
) -> Dict[str, Any]:
    """
    Predicts tampered/compromised nodes for a provenance graph Data object at specified threshold.

    Args:
        model: Trained GraphSAGEForTamperDetection model.
        data: PyG Data object.
        threshold: Decision probability threshold.
        device: PyTorch device.

    Returns:
        Dictionary containing:
            - node_probs: Array of node tamper probabilities [N]
            - node_preds: Array of binary node predictions [N]
            - flagged_node_ids: Set of string node IDs predicted as compromised
            - node_id_map: Mapping from node_id string -> node index
    """
    if device is None:
        device = get_device()

    model.eval()
    model.to(device)

    with torch.no_grad():
        x = data.x.to(device)
        edge_index = data.edge_index.to(device)

        _, _, node_logits = model(x, edge_index)
        probs = torch.sigmoid(node_logits).cpu().numpy()
        preds = (probs >= threshold).astype(int)

    node_id_map = getattr(data, "node_id_map", {})
    idx_to_node = {idx: nid for nid, idx in node_id_map.items()}

    flagged_node_ids = {
        idx_to_node[idx]
        for idx, pred in enumerate(preds)
        if pred == 1 and idx in idx_to_node
    }

    return {
        "node_probs": probs,
        "node_preds": preds,
        "flagged_node_ids": flagged_node_ids,
        "node_id_map": node_id_map,
        "threshold": threshold,
    }
