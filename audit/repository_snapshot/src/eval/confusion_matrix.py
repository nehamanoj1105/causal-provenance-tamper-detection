"""
Confusion matrix utilities for tamper detection evaluation.

Provides the ConfusionMatrix dataclass storing raw classification counts
and formatting utilities for reporting.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfusionMatrix:
    """
    Stores True Positives (TP), False Positives (FP),
    True Negatives (TN), and False Negatives (FN) counts.
    """

    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

    def total(self) -> int:
        """Returns the total number of evaluated items."""
        return self.tp + self.fp + self.tn + self.fn

    def pretty_print(self) -> str:
        """
        Returns a cleanly formatted text representation of the confusion matrix.
        """
        lines = [
            "========================================",
            "CONFUSION MATRIX",
            "========================================",
            f"  True Positives  (TP) : {self.tp:>8}",
            f"  False Positives (FP) : {self.fp:>8}",
            f"  True Negatives  (TN) : {self.tn:>8}",
            f"  False Negatives (FN) : {self.fn:>8}",
            "----------------------------------------",
            f"  Total Evaluated      : {self.total():>8}",
            "========================================",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, int]:
        """Returns the confusion matrix counts as a dictionary."""
        return {
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
        }
