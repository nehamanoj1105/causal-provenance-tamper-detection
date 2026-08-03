import unittest

from src.detection.rule_engine import (
    DuplicateEventRule,
)

from src.graph_construction.schema import (
    ProvenanceEdge,
    ProvenanceGraph,
    ProvenanceNode,
    NodeType,
)


class TestRuleEngine(unittest.TestCase):

    def test_duplicate_event_detected(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode(
                "A",
                NodeType.PROCESS,
                "A",
            )
        )

        graph.add_node(
            ProvenanceNode(
                "B",
                NodeType.FILE,
                "B",
            )
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "A",
                "B",
                "read",
                1.0,
            )
        )

        graph.add_edge(
            ProvenanceEdge(
                "e2",
                "A",
                "B",
                "read",
                1.0,
            )
        )

        result = DuplicateEventRule().check(graph)

        self.assertEqual(
            len(result.violations),
            1,
        )

    def test_unique_events_pass(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode(
                "A",
                NodeType.PROCESS,
                "A",
            )
        )

        graph.add_node(
            ProvenanceNode(
                "B",
                NodeType.FILE,
                "B",
            )
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "A",
                "B",
                "read",
                1.0,
            )
        )

        graph.add_edge(
            ProvenanceEdge(
                "e2",
                "A",
                "B",
                "write",
                2.0,
            )
        )

        result = DuplicateEventRule().check(graph)

        self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
