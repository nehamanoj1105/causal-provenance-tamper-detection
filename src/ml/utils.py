"""
Utility functions for ML models: random seed configuration, device selection, and graph dataset splits.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Tuple

import numpy as np

if TYPE_CHECKING:
    import torch


def set_seed(seed: int = 42) -> None:
    """
    Sets random seed across random, numpy, and torch for reproducible ML experiments.
    """
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def get_device() -> torch.device:
    """
    Returns PyTorch device (cuda if GPU is available, else cpu).
    """
    import torch

    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def create_train_val_test_masks(
    num_items: int,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Creates boolean train, validation, and test masks over `num_items`.
    """
    import torch

    rng = np.random.RandomState(seed)
    indices = np.arange(num_items)
    rng.shuffle(indices)

    n_train = int(num_items * train_ratio)
    n_val = int(num_items * val_ratio)

    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    train_mask = torch.zeros(num_items, dtype=torch.bool)
    val_mask = torch.zeros(num_items, dtype=torch.bool)
    test_mask = torch.zeros(num_items, dtype=torch.bool)

    if len(train_idx) > 0:
        train_mask[train_idx] = True
    if len(val_idx) > 0:
        val_mask[val_idx] = True
    if len(test_idx) > 0:
        test_mask[test_idx] = True

    return train_mask, val_mask, test_mask
