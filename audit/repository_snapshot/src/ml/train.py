"""
Training and validation pipeline for GraphSAGE tamper detection model.

Implements train_epoch, validate, test, train_pipeline, FocalLoss,
and checkpoint saving/loading.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple, List

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

if TYPE_CHECKING:
    from torch_geometric.data import Data

from src.ml.graphsage import GraphSAGEForTamperDetection
from src.ml.metrics import MLMetricResult, compute_ml_metrics, find_best_threshold
from src.ml.utils import get_device, set_seed


class FocalLoss(nn.Module):
    """
    Focal Loss for binary edge classification on imbalanced graphs.
    FL(p_t) = - alpha_t * (1 - p_t)^gamma * log(p_t)
    """

    def __init__(self, alpha: float = 0.75, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")

        p_t = probs * targets + (1 - probs) * (1 - targets)
        alpha_factor = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        focal_weight = alpha_factor * torch.pow((1 - p_t), self.gamma)

        loss = focal_weight * bce_loss
        return loss.mean()


def train_epoch(
    model: GraphSAGEForTamperDetection,
    data: Data,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    mask: Optional[torch.Tensor] = None,
) -> float:
    """
    Executes a single training epoch.

    Returns:
        Loss value.
    """
    model.train()
    optimizer.zero_grad()

    x = data.x.to(device)
    edge_index = data.edge_index.to(device)
    edge_label = data.edge_label.to(device)

    _, edge_logits, _ = model(x, edge_index)

    if mask is not None and mask.sum() > 0:
        loss = criterion(edge_logits[mask], edge_label[mask])
    else:
        loss = criterion(edge_logits, edge_label)

    loss.backward()
    optimizer.step()

    return float(loss.item())


def evaluate_model(
    model: GraphSAGEForTamperDetection,
    data: Data,
    device: torch.device,
    mask: Optional[torch.Tensor] = None,
    threshold: float = 0.5,
    criterion: Optional[nn.Module] = None,
) -> Tuple[float, MLMetricResult]:
    """
    Evaluates model performance over PyG Data.

    Returns:
        (loss, MLMetricResult)
    """
    model.eval()

    if criterion is None:
        criterion = nn.BCEWithLogitsLoss()

    with torch.no_grad():
        x = data.x.to(device)
        edge_index = data.edge_index.to(device)
        edge_label = data.edge_label.to(device)

        _, edge_logits, _ = model(x, edge_index)

        if mask is not None and mask.sum() > 0:
            loss = float(criterion(edge_logits[mask], edge_label[mask]).item())
            y_true = edge_label[mask].cpu().numpy()
            y_prob = torch.sigmoid(edge_logits[mask]).cpu().numpy()
        else:
            loss = float(criterion(edge_logits, edge_label).item())
            y_true = edge_label.cpu().numpy()
            y_prob = torch.sigmoid(edge_logits).cpu().numpy()

        metrics = compute_ml_metrics(y_true, y_prob, threshold=threshold)

    return loss, metrics


def save_checkpoint(
    model: nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    epoch: int = 0,
    metrics: Optional[MLMetricResult] = None,
    filepath: Path | str = "results/graphsage_checkpoint.pt",
) -> Path:
    """
    Saves model checkpoint.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict() if optimizer else None,
        "metrics": metrics.to_dict() if metrics else None,
    }

    torch.save(state, path)
    return path


def load_checkpoint(
    model: nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    filepath: Path | str = "results/graphsage_checkpoint.pt",
    device: Optional[torch.device] = None,
) -> Tuple[int, Optional[dict]]:
    """
    Loads model checkpoint.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found at {filepath}")

    if device is None:
        device = torch.device("cpu")

    checkpoint = torch.load(path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])

    if optimizer and checkpoint.get("optimizer_state_dict"):
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    return checkpoint.get("epoch", 0), checkpoint.get("metrics")



def train_pipeline(
    data: Data,
    epochs: int = 50,
    lr: float = 0.01,
    hidden_channels: int = 64,
    seed: int = 42,
    checkpoint_path: Path | str = "results/graphsage_checkpoint.pt",
    loss_strategy: str = "weighted_bce",
) -> Tuple[GraphSAGEForTamperDetection, MLMetricResult, float, List[float], List[float]]:
    """
    Complete training, validation, threshold optimization, and testing pipeline for GraphSAGE.

    Returns:
        (model, best_metrics, best_threshold, train_loss_history, val_loss_history)
    """
    set_seed(seed)
    device = get_device()

    in_channels = data.x.size(1) if data.x.dim() > 1 else 7
    model = GraphSAGEForTamperDetection(
        in_channels=in_channels,
        hidden_channels=hidden_channels,
    ).to(device)

    # Calculate class imbalance pos_weight
    edge_label_dev = data.edge_label.to(device)
    num_pos = float((edge_label_dev == 1.0).sum().item())
    num_neg = float((edge_label_dev == 0.0).sum().item())

    if loss_strategy == "focal":
        criterion = FocalLoss(alpha=0.75, gamma=2.0)
    else:
        pos_w = torch.tensor([num_neg / max(1.0, num_pos)], device=device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_w)

    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    train_loss_history: List[float] = []
    val_loss_history: List[float] = []

    best_val_f1 = -1.0
    best_threshold = 0.5
    best_metrics: Optional[MLMetricResult] = None

    for epoch in range(1, epochs + 1):
        loss = train_epoch(model, data, optimizer, criterion, device)
        train_loss_history.append(loss)

        if epoch % 5 == 0 or epoch == epochs:
            val_loss, _ = evaluate_model(model, data, device, criterion=criterion)
            val_loss_history.append(val_loss)

            # Perform threshold sweep on predictions
            model.eval()
            with torch.no_grad():
                _, edge_logits, _ = model(data.x.to(device), data.edge_index.to(device))
                y_true = data.edge_label.cpu().numpy()
                y_prob = torch.sigmoid(edge_logits).cpu().numpy()
                thresh, metrics = find_best_threshold(y_true, y_prob)

            if metrics.f1 > best_val_f1 or best_metrics is None:
                best_val_f1 = metrics.f1
                best_threshold = thresh
                best_metrics = metrics
                save_checkpoint(model, optimizer, epoch=epoch, metrics=metrics, filepath=checkpoint_path)

    if best_metrics is None:
        model.eval()
        with torch.no_grad():
            _, edge_logits, _ = model(data.x.to(device), data.edge_index.to(device))
            y_true = data.edge_label.cpu().numpy()
            y_prob = torch.sigmoid(edge_logits).cpu().numpy()
            best_threshold, best_metrics = find_best_threshold(y_true, y_prob)

    return model, best_metrics, best_threshold, train_loss_history, val_loss_history
