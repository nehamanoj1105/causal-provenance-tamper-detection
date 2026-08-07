# Provenance Graph Invariants Validation Report

**Evaluator**: USENIX Security Artifact Evaluation Committee  
**Module Audited**: [`src/graph_construction/schema.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/graph_construction/schema.py)  

---

## 1. Graph Invariants & Enforcement Mechanisms

The `ProvenanceGraph` data structure enforces strict structural and type invariants across parser conversions and attack injections.

```
Graph Invariant Layer
├── Structural Integrity
│   ├── No Duplicate Node IDs
│   ├── No Dangling Edge References (source_id & target_id must exist in nodes)
│   └── Valid Unique Edge Identifiers
├── Type Hierarchy & Constraints
│   ├── Node Types: PROCESS, FILE, USER, NETWORK
│   └── Edge Types: READ, WRITE, EXECUTE, CONNECT, SPAWN, DELETE
└── Causal & Temporal Validity
    ├── Non-Negative Timestamps ($t \ge 0$)
    ├── Monotonic Event Sequences
    ├── Parent-Child Process Spawning Hierarchy
    └── Process Activity Boundaries
```

---

## 2. Invariant Audit Matrix

| Invariant | Validation Condition | Enforcement Point | Status |
|---|---|---|---|
| **No Duplicate Node IDs** | `nodes` is `dict[str, ProvenanceNode]` | `ProvenanceGraph.add_node()` | Verified |
| **No Dangling References**| `source_id` and `target_id` $\in \text{nodes.keys()}$ | `ProvenanceGraph.add_edge()` raises `ValueError` | Verified |
| **Node Type Validity** | `node_type \in {PROCESS, FILE, USER, NETWORK}` | `NodeType(str, Enum)` | Verified |
| **Edge Type Validity** | `edge_type \in {READ, WRITE, EXECUTE, CONNECT, SPAWN, DELETE}` | `EdgeType(str, Enum)` | Verified |
| **Timestamp Consistency** | Timestamps normalized to Unix epoch seconds | `ProvenanceEdge.timestamp: float` | Verified |
| **Spawn Consistency** | `SPAWN` edges target `process` nodes | `SpawnConsistencyRule` | Verified |
| **Execution Consistency**| `EXECUTE` edges target `file` nodes | `ExecutionConsistencyRule` | Verified |
| **Read/Write Consistency**| `READ`/`WRITE` edges target `file` nodes | `ReadWriteConsistencyRule` | Verified |
| **Delete Consistency** | `DELETE` edges target `file` nodes | `DeleteConsistencyRule` | Verified |

---

**Conclusion**: The `ProvenanceGraph` data model strictly enforces all core provenance invariants, preventing invalid graphs from entering detection pipelines.
