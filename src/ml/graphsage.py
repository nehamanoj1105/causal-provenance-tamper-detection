"""
Standard 2-layer GraphSAGE architecture for provenance graph tamper detection.

Uses PyTorch Geometric SAGEConv layers to compute node representations,
and an edge prediction MLP head for edge tamper scoring.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv


class GraphSAGE(nn.Module):
    """
    Standard 2-layer GraphSAGE encoder.
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Computes node embeddings.

        Args:
            x: Node feature tensor [N, in_channels]
            edge_index: Edge index tensor [2, E]

        Returns:
            Node embedding tensor [N, out_channels]
        """
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return x


class EdgePredictor(nn.Module):
    """
    MLP head for predicting edge tampering by concatenating source and target node embeddings.
    """

    def __init__(self, node_emb_dim: int = 64, hidden_dim: int = 32):
        super().__init__()
        # Concatenated source and target node embeddings
        self.lin1 = nn.Linear(node_emb_dim * 2, hidden_dim)
        self.lin2 = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        node_embeddings: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        """
        Computes raw edge tamper logits.

        Args:
            node_embeddings: Node embedding tensor [N, node_emb_dim]
            edge_index: Edge index tensor [2, E]

        Returns:
            Raw edge tamper logits tensor [E]
        """
        src, tgt = edge_index[0], edge_index[1]
        src_emb = node_embeddings[src]
        tgt_emb = node_embeddings[tgt]

        edge_emb = torch.cat([src_emb, tgt_emb], dim=-1)
        h = F.relu(self.lin1(edge_emb))
        logits = self.lin2(h).squeeze(-1)
        return logits


class GraphSAGEForTamperDetection(nn.Module):
    """
    Full GraphSAGE model for provenance graph tamper detection (node embedding + edge classifier).
    """

    def __init__(
        self,
        in_channels: int = 7,
        hidden_channels: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.encoder = GraphSAGE(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=hidden_channels,
            dropout=dropout,
        )
        self.edge_predictor = EdgePredictor(
            node_emb_dim=hidden_channels,
            hidden_dim=hidden_channels // 2,
        )
        self.node_predictor = nn.Linear(hidden_channels, 1)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Returns:
            (node_embeddings [N, hidden], edge_logits [E], node_logits [N])
        """
        node_emb = self.encoder(x, edge_index)
        edge_logits = self.edge_predictor(node_emb, edge_index)
        node_logits = self.node_predictor(node_emb).squeeze(-1)
        return node_emb, edge_logits, node_logits
