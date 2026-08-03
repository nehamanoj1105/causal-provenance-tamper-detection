import unittest

from src.detection.poisoning_injection import (
    PoisoningType,
    inject_poisoning,
    targeted_deletion,
    targeted_dependency_forgery,
    targeted_insertion,
    targeted_reordering,
)
from src.graph_construction.schema import (
    ProvenanceEdge,
    ProvenanceGraph,
)
from src.graph_construction.synthetic import generate_synthetic_graph


class TestPoisoningInjection(unittest.TestCase):
    def setUp(self):
        self.graph = generate_synthetic_graph(
            num_processes=15, num_files=15, num_network=5, seed=1
        )
        self.original_edge_ids = {e.edge_id for e in self.graph.edges}

    def test_original_graph_untouched(self):
        inject_poisoning(self.graph, 2, 2, 2, 2, seed=1)
        # original graph object should be unchanged after injection
        current_ids = {e.edge_id for e in self.graph.edges}
        self.assertEqual(current_ids, self.original_edge_ids)

    def test_event_counts_match_request(self):
        result = inject_poisoning(self.graph, 3, 3, 3, 3, seed=1)
        counts = {}
        for e in result.events:
            counts[e.poisoning_type] = counts.get(e.poisoning_type, 0) + 1
        self.assertEqual(counts.get(PoisoningType.DELETION, 0), 3)
        self.assertEqual(counts.get(PoisoningType.INSERTION, 0), 3)

    def test_deleted_edges_actually_removed(self):
        result = inject_poisoning(self.graph, 5, 0, 0, 0, seed=2)
        deleted_ids = {
            e.edge_id for e in result.events if e.poisoning_type == PoisoningType.DELETION
        }
        remaining_ids = {e.edge_id for e in result.graph.edges}
        self.assertTrue(deleted_ids.isdisjoint(remaining_ids))

    def test_inserted_edges_present_in_graph(self):
        result = inject_poisoning(self.graph, 0, 4, 0, 0, seed=3)
        inserted_ids = {
            e.edge_id for e in result.events if e.poisoning_type == PoisoningType.INSERTION
        }
        remaining_ids = {e.edge_id for e in result.graph.edges}
        self.assertTrue(inserted_ids.issubset(remaining_ids))

    def test_edge_labels_cover_all_events(self):
        result = inject_poisoning(self.graph, 2, 2, 2, 2, seed=4)
        labels = result.edge_labels()
        self.assertEqual(len(labels), len(result.events))

    def test_targeted_deletion_existing_node(self):
        graph = ProvenanceGraph(
            nodes={
                "A": object(),
                "B": object(),
                "C": object(),
            },
            edges=[
                ProvenanceEdge(
                    edge_id="e1",
                    source_id="A",
                    target_id="B",
                    edge_type="READ",
                    timestamp=1.0,
                ),
                ProvenanceEdge(
                    edge_id="e2",
                    source_id="A",
                    target_id="C",
                    edge_type="WRITE",
                    timestamp=2.0,
                ),
                ProvenanceEdge(
                    edge_id="e3",
                    source_id="B",
                    target_id="C",
                    edge_type="READ",
                    timestamp=3.0,
                ),
            ],
        )

        result = targeted_deletion(
            graph,
            target_node="A",
            max_edges=2,
            seed=42,
        )

        self.assertEqual(len(result.events), 2)
        self.assertEqual(len(result.graph.edges), 1)

        for event in result.events:
            self.assertEqual(
                event.poisoning_type,
                PoisoningType.DELETION,
            )


    def test_targeted_deletion_unknown_node(self):
        graph = ProvenanceGraph(
            nodes={
                "A": object(),
            },
            edges=[],
        )

        result = targeted_deletion(
            graph,
            target_node="missing",
        )

        self.assertEqual(len(result.events), 0)
        self.assertEqual(len(result.graph.edges), 0)
    
    def test_targeted_dependency_forgery_existing_node(self):

        graph = ProvenanceGraph(
            nodes={
                "A": object(),
                "B": object(),
                "C": object(),
                "D": object(),
            },
            edges=[
                ProvenanceEdge(
                    edge_id="e1",
                    source_id="A",
                    target_id="B",
                    edge_type="READ",
                    timestamp=1.0,
                ),
                ProvenanceEdge(
                    edge_id="e2",
                    source_id="A",
                    target_id="C",
                    edge_type="WRITE",
                    timestamp=2.0,
                ),
            ],
        )

        result = targeted_dependency_forgery(
            graph,
            target_node="A",
            max_edges=2,
            seed=42,
        )

        self.assertEqual(len(result.events), 2)

        for event in result.events:
            self.assertEqual(
                event.poisoning_type,
                PoisoningType.DEPENDENCY_FORGERY,
            )

        forged_edges = {
            edge.edge_id: edge
            for edge in result.graph.edges
        }

        self.assertNotEqual(
            forged_edges["e1"].source_id,
            "A",
        )

        self.assertNotEqual(
            forged_edges["e2"].source_id,
            "A",
        )


    def test_targeted_dependency_forgery_unknown_node(self):

        graph = ProvenanceGraph(
            nodes={
                "A": object(),
            },
            edges=[],
        )

        result = targeted_dependency_forgery(
            graph,
            target_node="missing",
        )

        self.assertEqual(len(result.events), 0)
        self.assertEqual(len(result.graph.edges), 0)
        
    def test_targeted_insertion_existing_node(self):

        graph = ProvenanceGraph(
            nodes={
                "A": object(),
                "B": object(),
                "C": object(),
            },
            edges=[
                ProvenanceEdge(
                    edge_id="e1",
                    source_id="A",
                    target_id="B",
                    edge_type="READ",
                    timestamp=1.0,
                )
            ],
        )

        result = targeted_insertion(
            graph,
            target_node="A",
            max_insertions=1,
            seed=42,
        )

        self.assertEqual(len(result.events), 1)
        self.assertEqual(len(result.graph.edges), 2)

        inserted = result.graph.edges[-1]

        self.assertEqual(inserted.source_id, "A")
        self.assertEqual(inserted.target_id, "C")
        self.assertEqual(
            result.events[0].poisoning_type,
            PoisoningType.INSERTION,
        )


    def test_targeted_insertion_unknown_node(self):

        graph = ProvenanceGraph(
            nodes={
                "A": object(),
            },
            edges=[],
        )

        result = targeted_insertion(
            graph,
            target_node="missing",
        )

        self.assertEqual(len(result.events), 0)
        self.assertEqual(len(result.graph.edges), 0)
        
    def test_targeted_reordering_existing_node(self):

        graph = ProvenanceGraph(
            nodes={
                "A": object(),
                "B": object(),
            },
            edges=[
                ProvenanceEdge(
                    edge_id="e1",
                    source_id="A",
                    target_id="B",
                    edge_type="READ",
                    timestamp=1.0,
                ),
                ProvenanceEdge(
                    edge_id="e2",
                    source_id="A",
                    target_id="B",
                    edge_type="WRITE",
                    timestamp=2.0,
                ),
                ProvenanceEdge(
                    edge_id="e3",
                    source_id="A",
                    target_id="B",
                    edge_type="READ",
                    timestamp=3.0,
                ),
            ],
        )

        result = targeted_reordering(
            graph,
            target_node="A",
            max_swaps=1,
            seed=42,
        )

        self.assertEqual(len(result.graph.edges), 3)
        self.assertEqual(len(result.events), 2)

        original = {
            "e1": 1.0,
            "e2": 2.0,
            "e3": 3.0,
        }

        updated = {
            edge.edge_id: edge.timestamp
            for edge in result.graph.edges
        }

        changed = sum(
            original[eid] != updated[eid]
            for eid in original
        )

        self.assertEqual(changed, 2)

        for event in result.events:
            self.assertEqual(
                event.poisoning_type,
                PoisoningType.REORDERING,
            )


    def test_targeted_reordering_unknown_node(self):

        graph = ProvenanceGraph(
            nodes={
                "A": object(),
            },
            edges=[],
        )

        result = targeted_reordering(
            graph,
            target_node="missing",
        )

        self.assertEqual(len(result.events), 0)
        self.assertEqual(len(result.graph.edges), 0)

if __name__ == "__main__":
    unittest.main()
