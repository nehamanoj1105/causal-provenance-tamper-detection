#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv
import subprocess

import pandas as pd


DATASETS = ["1r", "3", "5m", "6r"]

PARSED_DIR = Path("data/parsed")
RESULTS_DIR = Path("results")
DOCS_DIR = Path("docs")

RESULTS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)


def analyze_dataset(dataset):
    node_file = PARSED_DIR / f"{dataset}_nodes.csv"
    edge_file = PARSED_DIR / f"{dataset}_edges.csv"

    node_types = Counter()
    edge_types = Counter()

    node_ids = set()
    edge_ids = set()

    in_degree = Counter()
    out_degree = Counter()

    with node_file.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_ids.add(row["node_id"])
            node_types[row["node_type"]] += 1

    with edge_file.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            edge_ids.add(row["edge_id"])

            edge_types[row["edge_type"]] += 1

            src = row["source_id"]
            dst = row["target_id"]

            out_degree[src] += 1
            in_degree[dst] += 1

    all_nodes = node_ids | set(in_degree.keys()) | set(out_degree.keys())

    avg_in = (
        sum(in_degree.values()) / len(all_nodes)
        if all_nodes else 0
    )

    avg_out = (
        sum(out_degree.values()) / len(all_nodes)
        if all_nodes else 0
    )

    total_degree = {
        n: in_degree[n] + out_degree[n]
        for n in all_nodes
    }

    avg_total = (
        sum(total_degree.values()) / len(all_nodes)
        if all_nodes else 0
    )

    row = {
        "dataset": dataset,
        "nodes": len(node_ids),
        "edges": len(edge_ids),
        "unique_node_ids": len(node_ids),
        "unique_edge_ids": len(edge_ids),
        "avg_in_degree": round(avg_in, 3),
        "avg_out_degree": round(avg_out, 3),
        "avg_total_degree": round(avg_total, 3),
    }

    for k, v in sorted(node_types.items()):
        row[f"node_{k}"] = v

    for k, v in sorted(edge_types.items()):
        row[f"edge_{k}"] = v

    return row


def main():
    rows = []

    print("\nDataset Summary")
    print("-" * 65)
    print(f"{'Dataset':<8}{'Nodes':>15}{'Edges':>15}")
    print("-" * 65)

    for dataset in DATASETS:
        row = analyze_dataset(dataset)
        rows.append(row)

        print(
            f"{dataset:<8}"
            f"{row['nodes']:>15,}"
            f"{row['edges']:>15,}"
        )

    df = pd.DataFrame(rows)
    df.to_csv(
        RESULTS_DIR / "dataset_statistics.csv",
        index=False,
    )

    with open(DOCS_DIR / "dataset_statistics.md", "w") as f:
        f.write("# Dataset Statistics\n\n")
        f.write(df.to_markdown(index=False))

    print("\nSaved:")
    print("  results/dataset_statistics.csv")
    print("  docs/dataset_statistics.md")

    print("\nCommitting to git...")

    subprocess.run(
        ["git", "add", "results/dataset_statistics.csv",
         "docs/dataset_statistics.md",
         "scripts/dataset_statistics.py"],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "Add dataset characterization statistics",
        ],
        check=True,
    )

    subprocess.run(
        ["git", "push", "origin", "main"],
        check=True,
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
