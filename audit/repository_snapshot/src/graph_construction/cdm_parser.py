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
    "FILE_OBJECT_BLOCK": NodeType.FILE,       # confirmed against real data
    "FILE_OBJECT_CHAR": NodeType.FILE,        # inferred, not yet seen
    "FILE_OBJECT_DIR": NodeType.FILE,         # inferred, not yet seen
    "FILE_OBJECT_FILE": NodeType.FILE,        # inferred, not yet seen
    "FILE_OBJECT_LINK": NodeType.FILE,        # inferred, not yet seen
    "FILE_OBJECT_NAMED_PIPE": NodeType.FILE,  # inferred, not yet seen
    "OBJECT_SOCKET": NodeType.NETWORK,
    "OBJECT_UNIXSOCKET": NodeType.NETWORK,
}

# CDM's sentinel for "no reference here" is a 16-byte all-zero UUID, not None.
# Confirmed against real Theia E3 data: EVENT_BOOT records carry this exact
# value in both `subject` and `predicateObject`. Must not be treated as a
# real node reference, or every "no target" event collapses onto one fake
# high-degree phantom node.
_NULL_UUID_HEX = "00" * 16


def _uuid_hex(raw: bytes | str | None) -> str | None:
    """
    Converts a raw CDM UUID into a stable string ID for use as a node/edge
    ID. Real CDM data gives us 16-byte binary UUIDs, which we hex-encode.
    Test fixtures may use plain strings directly as readable stand-in IDs,
    those pass through unchanged.
    """
    if raw is None:
        return None
    if isinstance(raw, bytes):
        return raw.hex()
    return raw


def _read_records(bin_path: Path) -> Iterator[dict]:
    """Yields raw deserialized TCCDMDatum records from a .bin file."""
    with open(bin_path, "rb") as f:
        for record in avro_reader(f):
            yield record


def parse_cdm_files_to_csv(
    bin_paths: list[Path],
    nodes_out: Path,
    edges_out: Path,
) -> tuple[int, int, int]:
    """
    Streams multiple CDM .bin segments to two CSV files instead of building
    an in-memory ProvenanceGraph. Necessary at real Theia scale: a single
    ~740MB segment already produces ~900K edges as live Python objects,
    which is too much to hold for 10 segments at once (confirmed via OOM
    kill on this exact dataset). Two-pass approach:

      pass 1: stream every segment, write every node to nodes_out as it's
              seen, keep only node IDs (not full objects) in memory to
              resolve edges against.
      pass 2: stream every segment again, write an edge to edges_out only
              if both endpoints are in the known node ID set.

    Returns (node_count, edge_count, skipped_count).
    """
    import csv

    known_node_ids: set[str] = set()
    node_count = 0

    with open(nodes_out, "w", newline="") as nf:
        writer = csv.writer(nf)
        writer.writerow(["node_id", "node_type", "label", "cdm_type"])
        for bin_path in bin_paths:
            for record in _read_records(bin_path):
                datum = record.get("datum", record)
                record_type = _infer_record_type(datum)
                node = None
                if record_type == "subject":
                    node = _subject_to_node(datum)
                elif record_type == "object":
                    node = _object_to_node(datum)
                if node and node.node_id not in known_node_ids:
                    known_node_ids.add(node.node_id)
                    writer.writerow([
                        node.node_id,
                        node.node_type.value,
                        node.label,
                        node.attributes.get("cdm_type", ""),
                    ])
                    node_count += 1

    edge_count = 0
    skipped = 0

    with open(edges_out, "w", newline="") as ef:
        writer = csv.writer(ef)
        writer.writerow(["edge_id", "source_id", "target_id", "edge_type", "timestamp", "sequence"])
        for bin_path in bin_paths:
            for record in _read_records(bin_path):
                datum = record.get("datum", record)
                if _infer_record_type(datum) != "event":
                    continue
                edge = _event_to_edge(datum)
                if edge is None:
                    continue
                if edge.source_id not in known_node_ids or edge.target_id not in known_node_ids:
                    skipped += 1
                    continue
                writer.writerow([
                    edge.edge_id,
                    edge.source_id,
                    edge.target_id,
                    edge.edge_type.value,
                    edge.timestamp,
                    edge.attributes.get("sequence", 0),
                ])
                edge_count += 1

    return node_count, edge_count, skipped


def parse_cdm_files(bin_paths: list[Path]) -> ProvenanceGraph:
    """
    Parses multiple CDM .bin segments (e.g. ta1-theia-e3-official-1r.bin,
    .bin.1, .bin.2, ...) into a single combined ProvenanceGraph.

    Nodes and edges are collected across all segments before any edge is
    resolved, since events in one segment can reference nodes recorded in
    another (a process seen in segment 3 might not spawn its first child
    until segment 5). Segment order matters for correctness of timestamps
    and sequence numbers but not for node/edge resolution, since resolution
    only depends on the union of all nodes being present before edges are
    added.
    """
    graph = ProvenanceGraph()
    unresolved_edges: list[ProvenanceEdge] = []

    for bin_path in bin_paths:
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

    skipped = 0
    for edge in unresolved_edges:
        try:
            graph.add_edge(edge)
        except ValueError:
            skipped += 1

    if skipped:
        print(f"parse_cdm_files: skipped {skipped} of {len(unresolved_edges)} "
              f"edges (missing endpoint across {len(bin_paths)} segments)")

    return graph


def parse_cdm_file(bin_path: Path) -> ProvenanceGraph:
    """
    Parses a single CDM .bin file into a ProvenanceGraph.

    Verified against a real Theia E3 sample (ta1-theia-e3-official-1r.bin):
    records are wrapped as {'datum': {...}, 'CDMVersion': ..., 'source': ...},
    the actual record lives under `datum`, and entity kind is discriminated
    by `datum['type']` rather than distinct top-level record shapes.
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
    names directly on the dict. Most branches carry a `type` enum string,
    but NetFlowObject (network socket) does not, confirmed against real
    Theia data, it's identified structurally by its address/port fields
    instead. MemoryObject and the Host record are also untyped but aren't
    needed for the current event taxonomy (no EVENT_MPROTECT/EVENT_MMAP
    mapping), so they're correctly left unmatched here.
    """
    cdm_type = datum.get("type")
    if cdm_type is not None:
        cdm_type = str(cdm_type)
        if cdm_type.startswith("SUBJECT_"):
            return "subject"
        if cdm_type.startswith("OBJECT_") or cdm_type.startswith("FILE_OBJECT_"):
            return "object"
        if cdm_type.startswith("EVENT_"):
            return "event"
        return None

    # Untyped NetFlowObject: identified by its distinctive address/port
    # fields rather than a type enum.
    if "localAddress" in datum and "remoteAddress" in datum:
        return "object"
    return None


def _subject_to_node(datum: dict) -> ProvenanceNode | None:
    node_type = CDM_NODE_TYPE_MAP.get(datum.get("type", ""), NodeType.PROCESS)
    uuid = _uuid_hex(datum.get("uuid"))
    if not uuid:
        return None
    return ProvenanceNode(
        node_id=uuid,
        node_type=node_type,
        label=datum.get("cmdLine", datum.get("type", "unknown_process")),
        attributes={"cdm_type": datum.get("type", "")},
    )


def _object_to_node(datum: dict) -> ProvenanceNode | None:
    cdm_type = datum.get("type")
    if cdm_type is None:
        # Untyped NetFlowObject, matched structurally in _infer_record_type.
        node_type = NodeType.NETWORK
        label = (
            f"{datum.get('localAddress', '?')}:{datum.get('localPort', '?')}"
            f" -> {datum.get('remoteAddress', '?')}:{datum.get('remotePort', '?')}"
        )
        cdm_type_label = "NetFlowObject"
    else:
        node_type = CDM_NODE_TYPE_MAP.get(cdm_type, NodeType.FILE)
        label = datum.get("path", cdm_type)
        cdm_type_label = cdm_type

    uuid = _uuid_hex(datum.get("uuid"))
    if not uuid:
        return None
    return ProvenanceNode(
        node_id=uuid,
        node_type=node_type,
        label=label,
        attributes={"cdm_type": cdm_type_label},
    )


def _event_to_edge(datum: dict) -> ProvenanceEdge | None:
    edge_type = CDM_EVENT_TYPE_MAP.get(datum.get("type", ""))
    if edge_type is None:
        return None  # event type not in our current taxonomy, skip

    subject_uuid = _uuid_hex(datum.get("subject"))
    object_uuid = _uuid_hex(datum.get("predicateObject"))

    if not subject_uuid or not object_uuid:
        return None
    if subject_uuid == _NULL_UUID_HEX or object_uuid == _NULL_UUID_HEX:
        # CDM's "no reference" sentinel, not a real node. Common on
        # EVENT_BOOT and similar system-level events with no process/file
        # on one side.
        return None

    edge_uuid = _uuid_hex(datum.get("uuid"))
    return ProvenanceEdge(
        edge_id=edge_uuid or f"{subject_uuid}->{object_uuid}",
        source_id=subject_uuid,
        target_id=object_uuid,
        edge_type=edge_type,
        timestamp=datum.get("timestampNanos", 0) / 1e9,
        attributes={"sequence": datum.get("sequence", 0)},
    )
