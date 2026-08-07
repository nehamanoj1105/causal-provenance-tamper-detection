"""
Comprehensive unit tests for GraphSAGE machine learning baseline, evaluation, threshold search,
probability calibration, plot generation, and diagnostics reporting.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from src.detection.poisoning_injection import inject_poisoning
from src.graph_construction.synthetic import generate_synthetic_graph
from src.ml.dataset import provenance_to_pyg_data
from src.ml.graphsage import GraphSAGEForTamperDetection
from src.ml.metrics import (
    compute_calibration_stats,
    compute_mcc,
    compute_ml_metrics,
    compute_pr_auc,
    compute_roc_auc,
    find_best_threshold,
    generate_graphsage_diagnostics_md,
    generate_threshold_metrics_csv,
    generate_threshold_metrics_md,
    plot_prediction_histogram,
    plot_precision_recall_curve,
    plot_roc_curve,
    threshold_sweep,
)
from src.ml.predict import predict_edges, predict_nodes
from src.ml.train import FocalLoss, load_checkpoint, save_checkpoint, train_pipeline
from src.ml.utils import get_device, set_seed


class TestGraphSAGEDataset(unittest.TestCase):

    def setUp(self):
        set_seed(42)
        self.graph = generate_synthetic_graph(num_processes=10, num_files=10, num_network=4, seed=42)
        self.poison_res = inject_poisoning(self.graph, 2, 2, 2, 2, seed=42)

    def test_provenance_to_pyg_data(self):
        data = provenance_to_pyg_data(self.poison_res.graph, poisoning_result=self.poison_res)

        self.assertTrue(hasattr(data, "x"))
        self.assertTrue(hasattr(data, "edge_index"))
        self.assertTrue(hasattr(data, "edge_attr"))
        self.assertTrue(hasattr(data, "edge_label"))
        self.assertTrue(hasattr(data, "node_label"))

        num_nodes = len(self.poison_res.graph.nodes)
        num_edges = len(self.poison_res.graph.edges)

        self.assertEqual(data.x.shape[0], num_nodes)
        self.assertEqual(data.x.shape[1], 7)
        self.assertEqual(data.edge_index.shape[0], 2)
        self.assertEqual(data.edge_index.shape[1], num_edges)
        self.assertEqual(data.edge_attr.shape[0], num_edges)
        self.assertEqual(data.edge_label.shape[0], num_edges)
        self.assertEqual(data.node_label.shape[0], num_nodes)


class TestGraphSAGEModelAndLoss(unittest.TestCase):

    def test_forward_pass_shapes(self):
        set_seed(42)
        graph = generate_synthetic_graph(num_processes=10, num_files=10, num_network=4, seed=42)
        data = provenance_to_pyg_data(graph)

        model = GraphSAGEForTamperDetection(in_channels=7, hidden_channels=32)
        model.eval()

        node_emb, edge_logits, node_logits = model(data.x, data.edge_index)

        num_nodes = len(graph.nodes)
        num_edges = len(graph.edges)

        self.assertEqual(node_emb.shape, (num_nodes, 32))
        self.assertEqual(edge_logits.shape, (num_edges,))
        self.assertEqual(node_logits.shape, (num_nodes,))

    def test_focal_loss(self):
        criterion = FocalLoss(alpha=0.75, gamma=2.0)
        logits = torch.tensor([1.5, -2.0, 0.5], dtype=torch.float)
        targets = torch.tensor([1.0, 0.0, 1.0], dtype=torch.float)
        loss = criterion(logits, targets)
        self.assertGreater(loss.item(), 0.0)


class TestThresholdSearchAndMetrics(unittest.TestCase):

    def test_threshold_sweep_and_best_selection(self):
        y_true = [0, 0, 0, 0, 1, 1]
        y_prob = [0.1, 0.2, 0.3, 0.4, 0.8, 0.9]

        sweep = threshold_sweep(y_true, y_prob)
        self.assertEqual(len(sweep), 20)

        best_t, best_m = find_best_threshold(y_true, y_prob)
        self.assertGreater(best_t, 0.4)
        self.assertLessEqual(best_t, 0.8)
        self.assertEqual(best_m.precision, 1.0)
        self.assertEqual(best_m.recall, 1.0)
        self.assertEqual(best_m.f1, 1.0)

    def test_calibration_stats(self):
        y_prob = [0.1, 0.2, 0.3, 0.8]
        calib = compute_calibration_stats(y_prob)
        self.assertAlmostEqual(calib["min_prob"], 0.1)
        self.assertAlmostEqual(calib["max_prob"], 0.8)
        self.assertAlmostEqual(calib["median_prob"], 0.25)
        self.assertAlmostEqual(calib["mean_prob"], 0.35)


    def test_mcc_computation(self):
        y_true = [1, 1, 0, 0]
        y_pred = [1, 1, 0, 0]
        mcc = compute_mcc(y_true, y_pred)
        self.assertEqual(mcc, 1.0)


class TestPlotAndReportGenerators(unittest.TestCase):

    def test_plots_and_reports(self):
        y_true = [0, 0, 0, 1, 1]
        y_prob = [0.1, 0.2, 0.3, 0.7, 0.9]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)

            pr_p = plot_precision_recall_curve(y_true, y_prob, out_dir / "pr.png")
            roc_p = plot_roc_curve(y_true, y_prob, out_dir / "roc.png")
            hist_p = plot_prediction_histogram(y_prob, out_dir / "hist.png")

            sweep = threshold_sweep(y_true, y_prob)
            csv_p = generate_threshold_metrics_csv(sweep, out_dir / "thresh.csv")
            md_p = generate_threshold_metrics_md(sweep, out_dir / "thresh.md")

            best_t, best_m = find_best_threshold(y_true, y_prob)
            diag_p = generate_graphsage_diagnostics_md(
                y_true, y_prob, best_t, best_m, [0.5, 0.3], [0.6, 0.4], out_dir / "diag.md"
            )

            self.assertTrue(pr_p.exists())
            self.assertTrue(roc_p.exists())
            self.assertTrue(hist_p.exists())
            self.assertTrue(csv_p.exists())
            self.assertTrue(md_p.exists())
            self.assertTrue(diag_p.exists())


class TestGraphSAGETrainingAndInference(unittest.TestCase):

    def setUp(self):
        set_seed(42)
        self.graph = generate_synthetic_graph(num_processes=10, num_files=10, num_network=4, seed=42)
        self.poison_res = inject_poisoning(self.graph, 2, 2, 2, 2, seed=42)
        self.data = provenance_to_pyg_data(self.poison_res.graph, poisoning_result=self.poison_res)

    def test_training_pipeline_with_threshold_search(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            chkpt_path = Path(tmpdir) / "checkpoint.pt"

            model, metrics, best_thresh, train_hist, val_hist = train_pipeline(
                self.data,
                epochs=5,
                lr=0.01,
                hidden_channels=16,
                seed=42,
                checkpoint_path=chkpt_path,
            )

            self.assertIsInstance(model, GraphSAGEForTamperDetection)
            self.assertTrue(chkpt_path.exists())
            self.assertGreater(best_thresh, 0.0)
            self.assertLessEqual(best_thresh, 1.0)
            self.assertGreater(len(train_hist), 0)

            # Test checkpoint loading
            new_model = GraphSAGEForTamperDetection(in_channels=7, hidden_channels=16)
            epoch, restored_metrics = load_checkpoint(new_model, filepath=chkpt_path)
            self.assertGreater(epoch, 0)

    def test_predictions(self):
        model = GraphSAGEForTamperDetection(in_channels=7, hidden_channels=16)

        edge_preds = predict_edges(model, self.data, threshold=0.3)
        self.assertIn("edge_probs", edge_preds)
        self.assertIn("edge_preds", edge_preds)
        self.assertIn("flagged_edge_ids", edge_preds)
        self.assertEqual(edge_preds["threshold"], 0.3)

        node_preds = predict_nodes(model, self.data, threshold=0.3)
        self.assertIn("node_probs", node_preds)
        self.assertIn("node_preds", node_preds)
        self.assertIn("flagged_node_ids", node_preds)
        self.assertEqual(node_preds["threshold"], 0.3)


if __name__ == "__main__":
    unittest.main()
