"""
Parses DARPA Transparent Computing CDM (Common Data Model) Avro records into
our internal ProvenanceGraph representation.

CDM records are read as TCCDMDatum unions (see data/README.md for the format
overview and where the schema files live). Each record wraps one of five
entity kinds; we only care about three of them for graph construction:

    Subject  -> ProvenanceNode (process)
    Object   -> ProvenanceNode (file / network / other resource)
    Event    -> ProvenanceEdge (the actual causal link between the two)

Principal and Edge records exist in the schema too but aren't consumed yet,
Principal (identity) isn't needed for the poisoning-detection scope, and
explicit Edge records are only used by some performers for causality that
Events don't capture; Theia's Event records are expected to cover our needs
for now. Revisit if graph connectivity looks sparse once we're parsing real
files.

Requires: fastavro (added to requirements.txt)
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from fastavro import reader as avro_reader

from .schema import EdgeType, NodeType, ProvenanceEdge, ProvenanceGraph, ProvenanceNode

# CDM event type strings -> our internal EdgeType.
# CDM's taxonomy is wider than what we model (EVENT_MMAP, EVENT_SIGNAL, etc);
# anything not listed here is skipped rather than guessed at.
CDM_EVENT_TYPE_MAP: dict[str, EdgeType] = {
    "EVENT_READ": EdgeType.READ,
    "EVENT_WRITE": EdgeType.WRITE,
    "EVENT_EXECUTE": EdgeType.EXECUTE,
    "EVENT_CONNECT": EdgeType.CONNECT,
    "EVENT_SENDTO": EdgeType.CONNECT,
    "EVENT_RECVFROM": EdgeType.CONNECT,
    "EVENT_FORK": EdgeType.SPAWN,
    "EVENT_CLONE": EdgeType.SPAWN,
    "EVENT_UNLINK": EdgeType.DELETE,
}

# CDM object/subject type strings -> our internal NodeType.
CDM_NODE_TYPE_MAP: dict[str, NodeType] = {
    "SUBJECT_PROCESS": NodeType.PROCESS,
    "SUBJECT_THREAD": NodeType.PROCESS,
    "OBJECT_FILE": NodeType.FILE,
    "OBJECT_SOCKET": NodeType.NETWORK,
    "OBJECT_UNIXSOCKET": NodeType.NETWORK,
}


def _read_records(bin_path: Path) -> Iterator[dict]:
    """Yields raw deserialized TCCDMDatum records from a .bin file."""
    with open(bin_path, "rb") as f:
        for record in avro_reader(f):
            yield record


def parse_cdm_file(bin_path: Path) -> ProvenanceGraph:
    """
    Parses a single CDM .bin file into a ProvenanceGraph.

    NOTE: has not yet been run against real Theia .bin files (dataset
    download is the next step). Field paths below (e.g. record["datum"])
    follow the TCCDMDatum union structure as documented, but should be
    verified/adjusted against an actual parsed sample before trusting output.
    """
    graph = ProvenanceGraph()
    unresolved_edges: list[ProvenanceEdge] = []

    for record in _read_records(bin_path):
        datum = record.get("datum", record)
        record_type = _infer_record_type(datum)

        if record_type == "subject":
            node = _subject_to_node(datum)
            if node:
                graph.add_node(node)

        elif record_type == "object":
            node = _object_to_node(datum)
            if node:
                graph.add_node(node)

        elif record_type == "event":
            edge = _event_to_edge(datum)
            if edge:
                unresolved_edges.append(edge)

    # Events can reference nodes that appear later in the stream (or in a
    # different file, for cross-file dependencies), so edges are buffered
    # and added after all nodes are collected.
    for edge in unresolved_edges:
        try:
            graph.add_edge(edge)
        except ValueError:
            # Referenced node genuinely missing from this file, skip for now
            # rather than fabricating a placeholder node. Worth tracking how
            # often this happens once real data is in hand.
            continue

    return graph


def _infer_record_type(datum: dict) -> str | None:
    """
    TCCDMDatum is a union type; fastavro surfaces the active branch's field
    names directly on the dict. This checks for fields that are distinctive
    to each entity kind. Needs verification against a real parsed record,
    the exact field names/shape are inferred from the schema docs, not yet
    confirmed against actual output.
    """
    if "type" in datum and str(datum.get("type", "")).startswith("SUBJECT_"):
        return "subject"
    if "type" in datum and str(datum.get("type", "")).startswith("OBJECT_"):
        return "object"
    if "type" in datum and str(datum.get("type", "")).startswith("EVENT_"):
        return "event"
    return None


def _subject_to_node(datum: dict) -> ProvenanceNode | None:
    node_type = CDM_NODE_TYPE_MAP.get(datum.get("type", ""), NodeType.PROCESS)
    uuid = datum.get("uuid")
    if not uuid:
        return None
    return ProvenanceNode(
        node_id=uuid,
        node_type=node_type,
        label=datum.get("cmdLine", datum.get("type", "unknown_process")),
        attributes={"cdm_type": datum.get("type", "")},
    )


def _object_to_node(datum: dict) -> ProvenanceNode | None:
    node_type = CDM_NODE_TYPE_MAP.get(datum.get("type", ""), NodeType.FILE)
    uuid = datum.get("uuid")
    if not uuid:
        return None
    return ProvenanceNode(
        node_id=uuid,
        node_type=node_type,
        label=datum.get("path", datum.get("type", "unknown_object")),
        attributes={"cdm_type": datum.get("type", "")},
    )


def _event_to_edge(datum: dict) -> ProvenanceEdge | None:
    edge_type = CDM_EVENT_TYPE_MAP.get(datum.get("type", ""))
    if edge_type is None:
        return None  # event type not in our current taxonomy, skip

    subject_uuid = datum.get("subjectUuid")
    object_uuid = datum.get("predicateObjectUuid")
    if not subject_uuid or not object_uuid:
        return None

    return ProvenanceEdge(
        edge_id=datum.get("uuid", f"{subject_uuid}->{object_uuid}"),
        source_id=subject_uuid,
        target_id=object_uuid,
        edge_type=edge_type,
        timestamp=datum.get("timestampNanos", 0) / 1e9,
        attributes={"sequence": datum.get("sequence", 0)},
    )
