import unittest

from src.detection.rule_engine import (
    ExecutionConsistencyRule,
    ReadWriteConsistencyRule,
)

from src.graph_construction.schema import (
    ProvenanceGraph,
    ProvenanceNode,
    ProvenanceEdge,
    NodeType,
)


class TestSemanticRules(unittest.TestCase):

    def test_valid_execute(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("P", NodeType.PROCESS, "proc")
        )

        graph.add_node(
            ProvenanceNode("F", NodeType.FILE, "bin")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "P",
                "F",
                "execute",
                1.0,
            )
        )

        self.assertTrue(
            ExecutionConsistencyRule().check(graph).passed
        )

    def test_invalid_execute(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("F1", NodeType.FILE, "file")
        )

        graph.add_node(
            ProvenanceNode("F2", NodeType.FILE, "file")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "F1",
                "F2",
                "execute",
                1.0,
            )
        )

        self.assertFalse(
            ExecutionConsistencyRule().check(graph).passed
        )

    def test_valid_read(self):

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
                "read",
                1.0,
            )
        )

        self.assertTrue(
            ReadWriteConsistencyRule().check(graph).passed
        )

    def test_invalid_write(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("F1", NodeType.FILE, "file")
        )

        graph.add_node(
            ProvenanceNode("F2", NodeType.FILE, "file")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "F1",
                "F2",
                "write",
                1.0,
            )
        )

        self.assertFalse(
            ReadWriteConsistencyRule().check(graph).passed
        )


if __name__ == "__main__":
    unittest.main()

