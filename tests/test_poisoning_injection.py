import unittest

from src.detection.poisoning_injection import PoisoningType, inject_poisoning
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


if __name__ == "__main__":
    unittest.main()
