"""
Modular rule engine for provenance graph validation.

Each rule independently checks one graph invariant and returns a RuleResult.
The RuleEngine simply executes all registered rules and aggregates results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.graph_construction.schema import ProvenanceGraph


# ---------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------

@dataclass
class RuleViolation:
    rule: str
    severity: str
    message: str
    edge_id: str | None = None
    node_id: str | None = None


@dataclass
class RuleResult:
    rule: str
    violations: list[RuleViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0


# ---------------------------------------------------------------------
# Base Rule
# ---------------------------------------------------------------------

class Rule(ABC):

    name = "UnnamedRule"

    @abstractmethod
    def check(
        self,
        graph: ProvenanceGraph,
    ) -> RuleResult:
        pass


# ---------------------------------------------------------------------
# Structural Rules
# ---------------------------------------------------------------------

class DuplicateEdgeRule(Rule):

    name = "DuplicateEdgeRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:

        result = RuleResult(rule=self.name)

        seen = set()

        for edge in graph.edges:

            if edge.edge_id in seen:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message=f"Duplicate edge id '{edge.edge_id}'",
                        edge_id=edge.edge_id,
                    )
                )

            seen.add(edge.edge_id)

        return result
        
class DuplicateEventRule(Rule):

    name = "DuplicateEventRule"

    def check(
        self,
        graph: ProvenanceGraph,
    ) -> RuleResult:

        result = RuleResult(rule=self.name)

        seen = {}

        for edge in graph.edges:

            signature = (
                edge.source_id,
                edge.target_id,
                edge.edge_type,
                edge.timestamp,
            )

            if signature in seen:

                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="MEDIUM",
                        message=(
                            "Duplicate provenance event "
                            f"(matches edge {seen[signature]})"
                        ),
                        edge_id=edge.edge_id,
                    )
                )

            else:
                seen[signature] = edge.edge_id

        return result

class SpawnConsistencyRule(Rule):

    name = "SpawnConsistencyRule"

    def check(
        self,
        graph: ProvenanceGraph,
    ) -> RuleResult:

        result = RuleResult(rule=self.name)

        seen = set()

        for edge in graph.edges:

            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()

            if edge_type != "spawn":
                continue

            # Parent must exist
            if edge.source_id not in graph.nodes:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="Spawn source node missing",
                        edge_id=edge.edge_id,
                        node_id=edge.source_id,
                    )
                )
                continue

            # Child must exist
            if edge.target_id not in graph.nodes:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="Spawn target node missing",
                        edge_id=edge.edge_id,
                        node_id=edge.target_id,
                    )
                )
                continue

            parent = graph.nodes[edge.source_id]
            child = graph.nodes[edge.target_id]

            parent_type = (
                parent.node_type.value
                if hasattr(parent.node_type, "value")
                else str(parent.node_type)
            ).lower()

            child_type = (
                child.node_type.value
                if hasattr(child.node_type, "value")
                else str(child.node_type)
            ).lower()

            # Parent must be a process
            if parent_type != "process":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="Spawn source is not a process",
                        edge_id=edge.edge_id,
                        node_id=edge.source_id,
                    )
                )

            # Child must be a process
            if child_type != "process":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="Spawn target is not a process",
                        edge_id=edge.edge_id,
                        node_id=edge.target_id,
                    )
                )

            # Process cannot spawn itself
            if edge.source_id == edge.target_id:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="Process spawned itself",
                        edge_id=edge.edge_id,
                        node_id=edge.source_id,
                    )
                )

            # Duplicate parent-child relationship
            signature = (
                edge.source_id,
                edge.target_id,
            )

            if signature in seen:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="LOW",
                        message="Duplicate spawn relationship",
                        edge_id=edge.edge_id,
                    )
                )
            else:
                seen.add(signature)

        return result
        
        
class ExecutionConsistencyRule(Rule):

    name = "ExecutionConsistencyRule"

    def check(
        self,
        graph: ProvenanceGraph,
    ) -> RuleResult:

        result = RuleResult(rule=self.name)

        seen = set()

        for edge in graph.edges:

            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()

            if edge_type != "execute":
                continue

            if edge.source_id not in graph.nodes or edge.target_id not in graph.nodes:
                continue

            src = graph.nodes[edge.source_id]
            tgt = graph.nodes[edge.target_id]

            src_type = (
                src.node_type.value
                if hasattr(src.node_type, "value")
                else str(src.node_type)
            ).lower()

            tgt_type = (
                tgt.node_type.value
                if hasattr(tgt.node_type, "value")
                else str(tgt.node_type)
            ).lower()

            if src_type != "process":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="EXECUTE source must be a process",
                        edge_id=edge.edge_id,
                        node_id=edge.source_id,
                    )
                )

            if tgt_type != "file":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="EXECUTE target must be a file",
                        edge_id=edge.edge_id,
                        node_id=edge.target_id,
                    )
                )

            if edge.source_id == edge.target_id:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="Process executed itself",
                        edge_id=edge.edge_id,
                    )
                )

            sig = (
                edge.source_id,
                edge.target_id,
                edge.timestamp,
            )

            if sig in seen:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="LOW",
                        message="Duplicate EXECUTE event",
                        edge_id=edge.edge_id,
                    )
                )
            else:
                seen.add(sig)

        return result


class ReadWriteConsistencyRule(Rule):

    name = "ReadWriteConsistencyRule"

    def check(
        self,
        graph: ProvenanceGraph,
    ) -> RuleResult:

        result = RuleResult(rule=self.name)

        seen = set()

        for edge in graph.edges:

            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()

            if edge_type not in {"read", "write"}:
                continue

            if edge.source_id not in graph.nodes or edge.target_id not in graph.nodes:
                continue

            src = graph.nodes[edge.source_id]
            tgt = graph.nodes[edge.target_id]

            src_type = (
                src.node_type.value
                if hasattr(src.node_type, "value")
                else str(src.node_type)
            ).lower()

            tgt_type = (
                tgt.node_type.value
                if hasattr(tgt.node_type, "value")
                else str(tgt.node_type)
            ).lower()

            if src_type != "process":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message=f"{edge_type.upper()} source must be a process",
                        edge_id=edge.edge_id,
                        node_id=edge.source_id,
                    )
                )

            if tgt_type != "file":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message=f"{edge_type.upper()} target must be a file",
                        edge_id=edge.edge_id,
                        node_id=edge.target_id,
                    )
                )

            sig = (
                edge_type,
                edge.source_id,
                edge.target_id,
                edge.timestamp,
            )

            if sig in seen:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="LOW",
                        message=f"Duplicate {edge_type.upper()} event",
                        edge_id=edge.edge_id,
                    )
                )
            else:
                seen.add(sig)

        return result
        
class NetworkConsistencyRule(Rule):

    name = "NetworkConsistencyRule"

    def check(
        self,
        graph: ProvenanceGraph,
    ) -> RuleResult:

        result = RuleResult(rule=self.name)

        for edge in graph.edges:

            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()

            if edge_type != "connect":
                continue

            if edge.source_id not in graph.nodes or edge.target_id not in graph.nodes:
                continue

            src = graph.nodes[edge.source_id]
            tgt = graph.nodes[edge.target_id]

            src_type = (
                src.node_type.value
                if hasattr(src.node_type, "value")
                else str(src.node_type)
            ).lower()

            tgt_type = (
                tgt.node_type.value
                if hasattr(tgt.node_type, "value")
                else str(tgt.node_type)
            ).lower()

            if src_type != "process":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="CONNECT source must be PROCESS",
                        edge_id=edge.edge_id,
                    )
                )

            if tgt_type not in ("network", "socket"):
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="CONNECT target must be NETWORK",
                        edge_id=edge.edge_id,
                    )
                )

        return result
        
class DeleteConsistencyRule(Rule):

    name = "DeleteConsistencyRule"

    def check(
        self,
        graph: ProvenanceGraph,
    ) -> RuleResult:

        result = RuleResult(rule=self.name)

        for edge in graph.edges:

            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()

            if edge_type != "delete":
                continue

            if edge.source_id not in graph.nodes or edge.target_id not in graph.nodes:
                continue

            src = graph.nodes[edge.source_id]
            tgt = graph.nodes[edge.target_id]

            src_type = (
                src.node_type.value
                if hasattr(src.node_type, "value")
                else str(src.node_type)
            ).lower()

            tgt_type = (
                tgt.node_type.value
                if hasattr(tgt.node_type, "value")
                else str(tgt.node_type)
            ).lower()

            if src_type != "process":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="DELETE source must be PROCESS",
                        edge_id=edge.edge_id,
                    )
                )

            if tgt_type != "file":
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="DELETE target must be FILE",
                        edge_id=edge.edge_id,
                    )
                )

        return result
        
class SelfLoopRule(Rule):

    name = "SelfLoopRule"

    INVALID = {
        "read",
        "write",
        "execute",
        "connect",
        "spawn",
        "delete",
    }

    def check(
        self,
        graph: ProvenanceGraph,
    ) -> RuleResult:

        result = RuleResult(rule=self.name)

        for edge in graph.edges:

            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()

            if edge_type not in self.INVALID:
                continue

            if edge.source_id == edge.target_id:

                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="MEDIUM",
                        message=f"Self-loop detected ({edge_type.upper()})",
                        edge_id=edge.edge_id,
                        node_id=edge.source_id,
                    )
                )

        return result
        
        
class MissingNodeRule(Rule):

    name = "MissingNodeRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:

        result = RuleResult(rule=self.name)

        for edge in graph.edges:

            if edge.source_id not in graph.nodes:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message=f"Missing source node '{edge.source_id}'",
                        edge_id=edge.edge_id,
                        node_id=edge.source_id,
                    )
                )

            if edge.target_id not in graph.nodes:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message=f"Missing target node '{edge.target_id}'",
                        edge_id=edge.edge_id,
                        node_id=edge.target_id,
                    )
                )

        return result


class TimestampRule(Rule):

    name = "TimestampRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:

        result = RuleResult(rule=self.name)

        for edge in graph.edges:

            if edge.timestamp is None:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="HIGH",
                        message="Missing timestamp",
                        edge_id=edge.edge_id,
                    )
                )
                continue

            if edge.timestamp < 0:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="MEDIUM",
                        message=f"Negative timestamp ({edge.timestamp})",
                        edge_id=edge.edge_id,
                    )
                )

        return result


class OrphanNodeRule(Rule):

    name = "OrphanNodeRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:

        result = RuleResult(rule=self.name)

        degree = {
            node: 0
            for node in graph.nodes
        }

        for edge in graph.edges:

            if edge.source_id in degree:
                degree[edge.source_id] += 1

            if edge.target_id in degree:
                degree[edge.target_id] += 1

        for node, deg in degree.items():

            if deg == 0:
                result.violations.append(
                    RuleViolation(
                        rule=self.name,
                        severity="LOW",
                        message="Orphan node",
                        node_id=node,
                    )
                )

        return result


# ---------------------------------------------------------------------
# Phase 6 Advanced Semantic Rules
# ---------------------------------------------------------------------

class UnspawnedProcessRule(Rule):
    """
    Flags activity performed by processes that were never spawned
    (signature of a deleted SPAWN edge).
    """

    name = "UnspawnedProcessRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:
        import re

        result = RuleResult(rule=self.name)

        spawned_processes = set()
        for edge in graph.edges:
            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()
            if edge_type == "spawn":
                spawned_processes.add(edge.target_id)

        # Root processes that don't require spawn edges
        root_processes = {"init", "proc_0", "1"}

        for node_id, node in graph.nodes.items():
            node_type = (
                node.node_type.value
                if hasattr(node.node_type, "value")
                else str(node.node_type)
            ).lower()

            if node_type == "process" and node_id not in spawned_processes and node_id not in root_processes:
                # Infer missing spawn edge ID if index can be extracted
                m = re.search(r"(\d+)$", node_id)
                if m:
                    idx = m.group(1)
                    missing_edge_id = f"e_spawn_{idx}"
                    result.violations.append(
                        RuleViolation(
                            rule=self.name,
                            severity="HIGH",
                            message=f"Process '{node_id}' performed actions but spawn edge was deleted",
                            edge_id=missing_edge_id,
                            node_id=node_id,
                        )
                    )

        return result


class SequenceGapRule(Rule):
    """
    Detects missing sequence indices/numbers in event streams (signature of DELETION attacks).
    """

    name = "SequenceGapRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:
        import re

        result = RuleResult(rule=self.name)

        prefixes: dict[str, list[int]] = {}

        for edge in graph.edges:
            m = re.match(r"^(.*_)(\d+)$", edge.edge_id)
            if m:
                pfx, idx = m.group(1), int(m.group(2))
                prefixes.setdefault(pfx, []).append(idx)

        for pfx, indices in prefixes.items():
            if not indices:
                continue
            indices.sort()
            min_idx, max_idx = indices[0], indices[-1]
            known_set = set(indices)

            for i in range(min_idx, max_idx + 1):
                if i not in known_set:
                    missing_edge_id = f"{pfx}{i}"
                    result.violations.append(
                        RuleViolation(
                            rule=self.name,
                            severity="HIGH",
                            message=f"Detected sequence gap: missing edge '{missing_edge_id}'",
                            edge_id=missing_edge_id,
                        )
                    )

        return result


class ParentChildTemporalRule(Rule):
    """
    Ensures a process spawning a child process occurs AFTER the parent's own spawn time.
    """

    name = "ParentChildTemporalRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:
        result = RuleResult(rule=self.name)

        spawn_time: dict[str, float] = {}

        for edge in graph.edges:
            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()
            if edge_type == "spawn":
                spawn_time[edge.target_id] = edge.timestamp

        for edge in graph.edges:
            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()
            if edge_type == "spawn":
                parent_ts = spawn_time.get(edge.source_id)
                if parent_ts is not None and edge.timestamp < parent_ts:
                    result.violations.append(
                        RuleViolation(
                            rule=self.name,
                            severity="HIGH",
                            message=f"Child spawn edge at {edge.timestamp:.2f} predates parent spawn at {parent_ts:.2f}",
                            edge_id=edge.edge_id,
                            node_id=edge.source_id,
                        )
                    )

        return result


class ProcessActivityTemporalRule(Rule):
    """
    Ensures process activity (READ, WRITE, CONNECT, EXECUTE, DELETE) occurs AFTER the process was spawned.
    """

    name = "ProcessActivityTemporalRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:
        result = RuleResult(rule=self.name)

        spawn_time: dict[str, float] = {}

        for edge in graph.edges:
            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()
            if edge_type == "spawn":
                spawn_time[edge.target_id] = edge.timestamp

        for edge in graph.edges:
            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else str(edge.edge_type)
            ).lower()
            if edge_type != "spawn":
                proc_spawn = spawn_time.get(edge.source_id)
                if proc_spawn is not None and edge.timestamp < proc_spawn:
                    result.violations.append(
                        RuleViolation(
                            rule=self.name,
                            severity="HIGH",
                            message=f"Process activity at {edge.timestamp:.2f} predates process spawn at {proc_spawn:.2f}",
                            edge_id=edge.edge_id,
                            node_id=edge.source_id,
                        )
                    )

        return result


class SequenceMonotonicityRule(Rule):
    """
    Detects timestamp inversion along sequential event streams of the same process/prefix (signature of REORDERING attacks).
    """

    name = "SequenceMonotonicityRule"

    def check(self, graph: ProvenanceGraph) -> RuleResult:
        import re

        result = RuleResult(rule=self.name)

        proc_events: dict[str, list[tuple[str, int, float, str]]] = {}

        for edge in graph.edges:
            m = re.match(r"^(.*_)(\d+)$", edge.edge_id)
            if m:
                pfx, idx = m.group(1), int(m.group(2))
                proc_events.setdefault(edge.source_id, []).append((pfx, idx, edge.timestamp, edge.edge_id))

        for proc, evs in proc_events.items():
            by_pfx: dict[str, list[tuple[int, float, str]]] = {}
            for pfx, idx, ts, eid in evs:
                by_pfx.setdefault(pfx, []).append((idx, ts, eid))

            for pfx, pfx_evs in by_pfx.items():
                if len(pfx_evs) < 2:
                    continue
                pfx_evs.sort(key=lambda x: x[0])
                for i in range(len(pfx_evs) - 1):
                    idx1, ts1, eid1 = pfx_evs[i]
                    idx2, ts2, eid2 = pfx_evs[i + 1]
                    if ts1 > ts2:
                        result.violations.append(
                            RuleViolation(
                                rule=self.name,
                                severity="HIGH",
                                message=f"Sequence timestamp inversion between edge {eid1} ({ts1:.2f}) and {eid2} ({ts2:.2f})",
                                edge_id=eid1,
                                node_id=proc,
                            )
                        )
                        result.violations.append(
                            RuleViolation(
                                rule=self.name,
                                severity="HIGH",
                                message=f"Sequence timestamp inversion between edge {eid1} ({ts1:.2f}) and {eid2} ({ts2:.2f})",
                                edge_id=eid2,
                                node_id=proc,
                            )
                        )

        return result


# ---------------------------------------------------------------------
# Rule Engine
# ---------------------------------------------------------------------

class RuleEngine:

    def __init__(
        self,
        rules: list[Rule],
    ):
        self.rules = rules

    def run(
        self,
        graph: ProvenanceGraph,
    ) -> list[RuleResult]:

        return [
            rule.check(graph)
            for rule in self.rules
        ]


def default_rule_engine():

    return RuleEngine(
        [
            DuplicateEdgeRule(),
            DuplicateEventRule(),
            SpawnConsistencyRule(),
            ExecutionConsistencyRule(),
            ReadWriteConsistencyRule(),
            NetworkConsistencyRule(),
            DeleteConsistencyRule(),
            SelfLoopRule(),
            MissingNodeRule(),
            TimestampRule(),
            UnspawnedProcessRule(),
            SequenceGapRule(),
            ParentChildTemporalRule(),
            ProcessActivityTemporalRule(),
            SequenceMonotonicityRule(),
        ]
    )

