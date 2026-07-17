"""
Tests the CDM->ProvenanceGraph transformation logic in cdm_parser.py.

IMPORTANT CAVEAT: this tests the record-to-node/edge mapping logic using
hand-built dicts shaped like documented CDM fields. It does NOT test actual
Avro binary decoding against a real .bin file, since we don't have one yet
(dataset download is still manual, see data/README.md). Once a real Theia
.bin file is available, add a test that runs parse_cdm_file() against it and
compare node/edge counts to a manual spot-check, the exact field names here
(subjectUuid, predicateObjectUuid, timestampNanos, etc) are inferred from
schema docs and could be wrong.
"""

import unittest

from src.graph_construction.cdm_parser import (
    _event_to_edge,
    _infer_record_type,
    _object_to_node,
    _subject_to_node,
)
from src.graph_construction.schema import EdgeType, NodeType


class TestRecordTypeInference(unittest.TestCase):
    def test_subject_detected(self):
        self.assertEqual(_infer_record_type({"type": "SUBJECT_PROCESS"}), "subject")

    def test_object_detected(self):
        self.assertEqual(_infer_record_type({"type": "OBJECT_FILE"}), "object")

    def test_event_detected(self):
        self.assertEqual(_infer_record_type({"type": "EVENT_READ"}), "event")

    def test_unknown_type_returns_none(self):
        self.assertIsNone(_infer_record_type({"type": "PRINCIPAL_LOCAL"}))
        self.assertIsNone(_infer_record_type({}))


class TestSubjectToNode(unittest.TestCase):
    def test_basic_process_subject(self):
        datum = {
            "uuid": "subj-1",
            "type": "SUBJECT_PROCESS",
            "cmdLine": "/usr/bin/bash -c whoami",
        }
        node = _subject_to_node(datum)
        self.assertEqual(node.node_id, "subj-1")
        self.assertEqual(node.node_type, NodeType.PROCESS)
        self.assertEqual(node.label, "/usr/bin/bash -c whoami")

    def test_missing_uuid_returns_none(self):
        self.assertIsNone(_subject_to_node({"type": "SUBJECT_PROCESS"}))


class TestObjectToNode(unittest.TestCase):
    def test_file_object(self):
        datum = {"uuid": "obj-1", "type": "OBJECT_FILE", "path": "/etc/passwd"}
        node = _object_to_node(datum)
        self.assertEqual(node.node_type, NodeType.FILE)
        self.assertEqual(node.label, "/etc/passwd")

    def test_socket_object(self):
        datum = {"uuid": "obj-2", "type": "OBJECT_SOCKET", "path": "10.0.0.5:443"}
        node = _object_to_node(datum)
        self.assertEqual(node.node_type, NodeType.NETWORK)


class TestEventToEdge(unittest.TestCase):
    def test_read_event(self):
        datum = {
            "uuid": "evt-1",
            "type": "EVENT_READ",
            "subjectUuid": "subj-1",
            "predicateObjectUuid": "obj-1",
            "timestampNanos": 1_700_000_000_000_000_000,
            "sequence": 42,
        }
        edge = _event_to_edge(datum)
        self.assertEqual(edge.source_id, "subj-1")
        self.assertEqual(edge.target_id, "obj-1")
        self.assertEqual(edge.edge_type, EdgeType.READ)
        self.assertAlmostEqual(edge.timestamp, 1_700_000_000.0)

    def test_unknown_event_type_skipped(self):
        datum = {
            "uuid": "evt-2",
            "type": "EVENT_MMAP",  # not in our current taxonomy
            "subjectUuid": "subj-1",
            "predicateObjectUuid": "obj-1",
        }
        self.assertIsNone(_event_to_edge(datum))

    def test_missing_endpoints_skipped(self):
        datum = {"uuid": "evt-3", "type": "EVENT_READ", "subjectUuid": "subj-1"}
        self.assertIsNone(_event_to_edge(datum))


if __name__ == "__main__":
    unittest.main()
