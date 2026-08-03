import unittest

from src.detection.rule_engine import (
    NetworkConsistencyRule,
    DeleteConsistencyRule,
    SelfLoopRule,
)

from src.graph_construction.schema import (
    ProvenanceGraph,
    ProvenanceNode,
    ProvenanceEdge,
    NodeType,
)


class TestAdditionalRules(unittest.TestCase):

    def test_valid_connect(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("P", NodeType.PROCESS, "proc")
        )

        graph.add_node(
            ProvenanceNode("N", NodeType.NETWORK, "net")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "P",
                "N",
                "connect",
                1.0,
            )
        )

        self.assertTrue(
            NetworkConsistencyRule().check(graph).passed
        )

    def test_invalid_connect(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("F", NodeType.FILE, "file")
        )

        graph.add_node(
            ProvenanceNode("N", NodeType.NETWORK, "net")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "F",
                "N",
                "connect",
                1.0,
            )
        )

        self.assertFalse(
            NetworkConsistencyRule().check(graph).passed
        )

    def test_valid_delete(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("P", NodeType.PROCESS, "proc")
        )

        graph.add_node(
            ProvenanceNode("F", NodeType.FILE, "file")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "P",
                "F",
                "delete",
                1.0,
            )
        )

        self.assertTrue(
            DeleteConsistencyRule().check(graph).passed
        )

    def test_self_loop(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("P", NodeType.PROCESS, "proc")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "P",
                "P",
                "read",
                1.0,
            )
        )

        self.assertFalse(
            SelfLoopRule().check(graph).passed
        )


if __name__ == "__main__":
    unittest.main()
