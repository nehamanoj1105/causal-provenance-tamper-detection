import unittest

from src.eval.metrics import compute_metrics
from src.graph_construction.schema import EdgeType, NodeType, ProvenanceEdge, ProvenanceGraph, ProvenanceNode


def _build_graph(n_edges: int) -> ProvenanceGraph:
    g = ProvenanceGraph()
    g.add_node(ProvenanceNode("proc", NodeType.PROCESS, "proc"))
    for i in range(n_edges):
        fid = f"file_{i}"
        g.add_node(ProvenanceNode(fid, NodeType.FILE, fid))
        g.add_edge(ProvenanceEdge(f"e{i}", "proc", fid, EdgeType.WRITE, float(i)))
    return g


class TestMetrics(unittest.TestCase):
    def test_perfect_detection(self):
        graph = _build_graph(10)
        poisoned = {"e0", "e1", "e2"}
        flagged = {"e0", "e1", "e2"}
        m = compute_metrics(graph, poisoned, flagged)
        self.assertEqual(m.tdr, 1.0)
        self.assertEqual(m.precision, 1.0)
        self.assertEqual(m.false_positive_rate, 0.0)

    def test_no_detection(self):
        graph = _build_graph(10)
        poisoned = {"e0", "e1", "e2"}
        flagged: set[str] = set()
        m = compute_metrics(graph, poisoned, flagged)
        self.assertEqual(m.tdr, 0.0)
        self.assertEqual(m.precision, 0.0)

    def test_false_positives_only(self):
        graph = _build_graph(10)
        poisoned = {"e0"}
        flagged = {"e5", "e6"}  # both benign
        m = compute_metrics(graph, poisoned, flagged)
        self.assertEqual(m.tdr, 0.0)
        self.assertEqual(m.precision, 0.0)
        self.assertGreater(m.false_positive_rate, 0.0)

    def test_pis_reflects_valid_fraction(self):
        graph = _build_graph(10)  # 10 edges
        poisoned = {"e0", "e1"}  # 2 of 10 poisoned
        m = compute_metrics(graph, poisoned, set())
        self.assertAlmostEqual(m.pis, 0.8)

    def test_empty_graph_no_crash(self):
        graph = ProvenanceGraph()
        m = compute_metrics(graph, set(), set())
        self.assertEqual(m.pis, 0.0)
        self.assertEqual(m.tdr, 0.0)


if __name__ == "__main__":
    unittest.main()
