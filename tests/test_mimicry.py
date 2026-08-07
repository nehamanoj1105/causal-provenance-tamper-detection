"""
Unit tests for Phase 10 adversarial mimicry attack generator and camouflage operations.
"""

import unittest

from src.detection.mimicry_attack import (
    MimicryAttackResult,
    MimicryStrength,
    _calculate_graph_stats,
    inject_mimicry_attack,
)
from src.detection.poisoning_injection import inject_poisoning
from src.graph_construction.synthetic import generate_synthetic_graph


class TestMimicryAttackGenerator(unittest.TestCase):

    def setUp(self):
        self.graph = generate_synthetic_graph(num_processes=10, num_files=10, num_network=4, seed=42)
        self.base_poisoning = inject_poisoning(self.graph, 2, 2, 2, 2, seed=42)

    def test_calculate_graph_stats(self):
        stats = _calculate_graph_stats(self.graph)
        self.assertIn("in_deg", stats)
        self.assertIn("out_deg", stats)
        self.assertIn("type_ratios", stats)
        self.assertGreaterEqual(stats["max_ts"], stats["min_ts"])

    def test_inject_mimicry_attack_light(self):
        res = inject_mimicry_attack(
            self.graph,
            base_poisoning=self.base_poisoning,
            strength="light",
            seed=42,
        )
        self.assertIsInstance(res, MimicryAttackResult)
        self.assertEqual(res.mimicry_strength, "light")
        self.assertGreater(res.num_noise_edges, 0)
        self.assertGreater(len(res.graph.edges), len(self.base_poisoning.graph.edges))

    def test_inject_mimicry_attack_heavy(self):
        res_light = inject_mimicry_attack(self.graph, base_poisoning=self.base_poisoning, strength="light", seed=42)
        res_heavy = inject_mimicry_attack(self.graph, base_poisoning=self.base_poisoning, strength="heavy", seed=42)

        self.assertGreater(res_heavy.num_noise_edges, res_light.num_noise_edges)

    def test_camouflage_operations_presence(self):
        res = inject_mimicry_attack(self.graph, base_poisoning=self.base_poisoning, strength="medium", seed=42)
        noise_edge_types = {e.edge_type.value for e in res.graph.edges if e.edge_id.startswith("mimicry_")}
        self.assertGreater(len(noise_edge_types), 0)


if __name__ == "__main__":
    unittest.main()
