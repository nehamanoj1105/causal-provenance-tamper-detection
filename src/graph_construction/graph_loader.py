
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
