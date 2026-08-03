
import unittest

from src.detection.rule_engine import SpawnConsistencyRule

from src.graph_construction.schema import (
    ProvenanceGraph,
    ProvenanceNode,
    ProvenanceEdge,
    NodeType,
)


class TestSpawnRule(unittest.TestCase):

    def test_valid_spawn(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("P1", NodeType.PROCESS, "parent")
        )

        graph.add_node(
            ProvenanceNode("P2", NodeType.PROCESS, "child")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "P1",
                "P2",
                "spawn",
                1.0,
            )
        )

        result = SpawnConsistencyRule().check(graph)

        self.assertTrue(result.passed)

    def test_self_spawn(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("P1", NodeType.PROCESS, "proc")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "P1",
                "P1",
                "spawn",
                1.0,
            )
        )

        result = SpawnConsistencyRule().check(graph)

        self.assertEqual(
            len(result.violations),
            1,
        )

    def test_spawn_to_file(self):

        graph = ProvenanceGraph()

        graph.add_node(
            ProvenanceNode("P1", NodeType.PROCESS, "proc")
        )

        graph.add_node(
            ProvenanceNode("F1", NodeType.FILE, "file")
        )

        graph.add_edge(
            ProvenanceEdge(
                "e1",
                "P1",
                "F1",
                "spawn",
                1.0,
            )
        )

        result = SpawnConsistencyRule().check(graph)

        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
