
from src.graph_construction.graph_loader import (
    available_datasets,
    dataset_exists,
    load_edges,
    load_graph,
    load_nodes,
)


def test_available_datasets():
    datasets = available_datasets()

    assert "1r" in datasets
    assert "3" in datasets
    assert "5m" in datasets
    assert "6r" in datasets


def test_dataset_exists():
    assert dataset_exists("1r")
    assert dataset_exists("3")
    assert dataset_exists("5m")
    assert dataset_exists("6r")


def test_load_nodes():
    nodes = load_nodes("3")

    assert len(nodes) > 0
    assert "node_id" in nodes.columns
    assert "node_type" in nodes.columns


def test_load_edges():
    edges = load_edges("3")

    assert len(edges) > 0
    assert "source_id" in edges.columns
    assert "target_id" in edges.columns


def test_load_graph():
    graph = load_graph("3")

    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0
