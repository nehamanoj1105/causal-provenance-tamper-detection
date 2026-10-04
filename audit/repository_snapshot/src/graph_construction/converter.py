"""
Converts the DataFrame-based graph loaded from CSV into the schema-based
ProvenanceGraph used by the rule engine and synthetic attack framework.
"""

from src.graph_construction.graph_loader import (
    ProvenanceGraph as DataFrameGraph,
)

from src.graph_construction.schema import (
    EdgeType,
    NodeType,
    ProvenanceEdge,
    ProvenanceGraph,
    ProvenanceNode,
)


def dataframe_to_schema(graph: DataFrameGraph) -> ProvenanceGraph:

    schema_graph = ProvenanceGraph()

    # -------------------------
    # Nodes
    # -------------------------

    for _, row in graph.nodes.iterrows():

        try:
            node_type = NodeType(row["node_type"])
        except ValueError:
            continue

        schema_graph.add_node(
            ProvenanceNode(
                node_id=str(row["node_id"]),
                node_type=node_type,
                label=str(row.get("label", "")),
                attributes={
                    "cdm_type": row.get("cdm_type"),
                },
            )
        )

    # -------------------------
    # Edges
    # -------------------------

    for _, row in graph.edges.iterrows():

        try:
            edge_type = EdgeType(row["edge_type"])
        except ValueError:
            continue

        # Skip malformed edges
        if (
            row["source_id"] not in schema_graph.nodes
            or
            row["target_id"] not in schema_graph.nodes
        ):
            continue

        schema_graph.add_edge(
            ProvenanceEdge(
                edge_id=str(row["edge_id"]),
                source_id=str(row["source_id"]),
                target_id=str(row["target_id"]),
                edge_type=edge_type,
                timestamp=float(row["timestamp"]),
            )
        )

    return schema_graph
