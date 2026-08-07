"""
Comprehensive unit tests for confusion_matrix.py.
"""

import unittest

from src.eval.confusion_matrix import ConfusionMatrix


class TestConfusionMatrix(unittest.TestCase):

    def test_correct_counts(self):
        cm = ConfusionMatrix(tp=10, fp=2, tn=20, fn=1)
        self.assertEqual(cm.tp, 10)
        self.assertEqual(cm.fp, 2)
        self.assertEqual(cm.tn, 20)
        self.assertEqual(cm.fn, 1)
        self.assertEqual(cm.total(), 33)

    def test_dictionary_conversion(self):
        cm = ConfusionMatrix(tp=5, fp=1, tn=15, fn=2)
        d = cm.to_dict()
        self.assertEqual(d, {"tp": 5, "fp": 1, "tn": 15, "fn": 2})

    def test_pretty_print(self):
        cm = ConfusionMatrix(tp=10, fp=2, tn=20, fn=1)
        output = cm.pretty_print()
        self.assertIn("CONFUSION MATRIX", output)
        self.assertIn("True Positives  (TP) :       10", output)
        self.assertIn("Total Evaluated      :       33", output)


if __name__ == "__main__":
    unittest.main()
