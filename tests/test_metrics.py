"""
Comprehensive unit tests for metrics.py.
"""

import unittest

from src.eval.metrics import (
    MetricResult,
    accuracy,
    balanced_accuracy,
    compute_metrics_from_counts,
    f1_score,
    false_negative_rate,
    false_positive_rate,
    precision,
    recall,
    specificity,
)


class TestMetrics(unittest.TestCase):

    def test_perfect_precision(self):
        # TP = 10, FP = 0 -> Precision = 1.0
        self.assertEqual(precision(10, 0), 1.0)

    def test_zero_precision(self):
        # TP = 0, FP = 10 -> Precision = 0.0
        self.assertEqual(precision(0, 10), 0.0)

    def test_perfect_recall(self):
        # TP = 10, FN = 0 -> Recall = 1.0
        self.assertEqual(recall(10, 0), 1.0)

    def test_zero_recall(self):
        # TP = 0, FN = 10 -> Recall = 0.0
        self.assertEqual(recall(0, 10), 0.0)

    def test_perfect_f1(self):
        # Precision = 1.0, Recall = 1.0 -> F1 = 1.0
        self.assertEqual(f1_score(10, 0, 0), 1.0)
        self.assertEqual(f1_score(precision_val=1.0, recall_val=1.0), 1.0)

    def test_zero_f1(self):
        self.assertEqual(f1_score(0, 5, 5), 0.0)
        self.assertEqual(f1_score(precision_val=0.0, recall_val=0.0), 0.0)

    def test_divide_by_zero(self):
        # All metric functions must handle 0 denominators safely without crashing
        self.assertEqual(precision(0, 0), 0.0)
        self.assertEqual(recall(0, 0), 0.0)
        self.assertEqual(f1_score(0, 0, 0), 0.0)
        self.assertEqual(f1_score(precision_val=0.0, recall_val=0.0), 0.0)
        self.assertEqual(accuracy(0, 0, 0, 0), 0.0)
        self.assertEqual(false_positive_rate(0, 0), 0.0)
        self.assertEqual(false_negative_rate(0, 0), 0.0)
        self.assertEqual(specificity(0, 0), 0.0)
        self.assertEqual(balanced_accuracy(0, 0, 0, 0), 0.0)

    def test_accuracy_calculation(self):
        # TP=5, FP=1, TN=8, FN=1 -> Total=15, (5+8)/15 = 13/15 = 0.866666...
        self.assertAlmostEqual(accuracy(5, 1, 8, 1), 13.0 / 15.0)

    def test_fpr_and_fnr_calculation(self):
        # FP=2, TN=8 -> FPR = 2/10 = 0.2
        self.assertEqual(false_positive_rate(2, 8), 0.2)
        # FN=3, TP=7 -> FNR = 3/10 = 0.3
        self.assertEqual(false_negative_rate(3, 7), 0.3)

    def test_specificity_and_balanced_accuracy(self):
        # TN=8, FP=2 -> Specificity = 8/10 = 0.8
        self.assertEqual(specificity(8, 2), 0.8)
        # Sensitivity (Recall) = 7/10 = 0.7, Specificity = 0.8 -> Balanced Acc = (0.7 + 0.8)/2 = 0.75
        self.assertEqual(balanced_accuracy(7, 2, 8, 3), 0.75)

    def test_compute_metrics_from_counts(self):
        res = compute_metrics_from_counts(tp=8, fp=2, tn=18, fn=2)
        self.assertIsInstance(res, MetricResult)
        self.assertAlmostEqual(res.precision, 0.8)
        self.assertAlmostEqual(res.recall, 0.8)
        self.assertAlmostEqual(res.f1, 0.8)
        self.assertAlmostEqual(res.accuracy, 26.0 / 30.0)
        self.assertAlmostEqual(res.f1_score, 0.8)
        self.assertIn("precision", res.to_dict())


if __name__ == "__main__":
    unittest.main()
