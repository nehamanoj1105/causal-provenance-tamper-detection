#!/usr/bin/env python3

from pathlib import Path
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[1]

loader = ROOT / "src/graph_construction/graph_loader.py"
tests = ROOT / "tests/test_graph_loader.py"

loader.write_text(textwrap.dedent("""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/parsed")


@dataclass
class ProvenanceGraph:
    nodes: pd.DataFrame
    edges: pd.DataFrame


def available_datasets():
    datasets = []

    for file in DATA_DIR.glob("*_nodes.csv"):
        datasets.append(file.stem.replace("_nodes", ""))

    return sorted(datasets)


def dataset_exists(dataset: str):
    return (
        (DATA_DIR / f"{dataset}_nodes.csv").exists()
        and
        (DATA_DIR / f"{dataset}_edges.csv").exists()
    )


def load_nodes(dataset: str):
    path = DATA_DIR / f"{dataset}_nodes.csv"

    if not path.exists():
        raise FileNotFoundError(path)

    return pd.read_csv(path)


def load_edges(dataset: str):
    path = DATA_DIR / f"{dataset}_edges.csv"

    if not path.exists():
        raise FileNotFoundError(path)

    return pd.read_csv(path)


def load_graph(dataset: str):
    return ProvenanceGraph(
        nodes=load_nodes(dataset),
        edges=load_edges(dataset),
    )
"""))

tests.write_text(textwrap.dedent("""
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
"""))

print("Running tests...")

try:
    subprocess.run(["pytest", "-q"], check=True)
except FileNotFoundError:
    subprocess.run(["python3", "-m", "pytest", "-q"], check=True)

print("Adding files...")

subprocess.run(
    [
        "git",
        "add",
        "src/graph_construction/graph_loader.py",
        "tests/test_graph_loader.py",
        "scripts/setup_graph_loader.py",
    ],
    check=True,
)

print("Committing...")

subprocess.run(
    [
        "git",
        "commit",
        "-m",
        "Add graph loading API",
    ],
    check=True,
)

print("Pushing...")

subprocess.run(
    [
        "git",
        "push",
        "origin",
        "main",
    ],
    check=True,
)

