
# Threat Model

## 1. Overview

This work assumes that provenance-based intrusion detection systems operate on
provenance graphs constructed from operating system audit logs. Existing systems
generally trust the integrity of these provenance graphs. This project instead
verifies that the provenance graph itself has not been maliciously modified
before downstream analysis.

---

## 2. Protected Assets

The system protects:

- Provenance graph integrity
- Causal relationships
- Event ordering
- Process lineage
- File dependency chains
- Network dependency chains

---

## 3. Trusted Components

Trusted:

- Operating system kernel
- Audit logging infrastructure
- Parser
- Detection engine

Not trusted:

- Stored provenance graph
- Intermediate graph representations
- Any attacker-accessible storage

---

## 4. Attacker Capabilities

The attacker may:

- Delete provenance events
- Insert fake events
- Reorder events
- Forge dependencies
- Modify node attributes
- Modify edge attributes

The attacker attempts to hide malicious activity while preserving as much graph
structure as possible.

---

## 5. Attacker Limitations

The attacker cannot:

- Modify the detector
- Disable the parser
- Compromise the trusted kernel
- Break future cryptographic integrity mechanisms (QuantumGuard+)

---

## 6. Attacker Knowledge

Assume a gray-box adversary.

The attacker knows:

- The graph schema
- General detector behavior

The attacker does not know:

- Internal detector parameters
- Learned model weights

---

## 7. Attack Goals

Primary goals:

- Hide malicious execution
- Hide file access
- Hide network communication
- Hide privilege escalation
- Fabricate benign causal paths

---

## 8. Supported Tampering Attacks

Current attack classes:

1. Edge deletion
2. Edge insertion
3. Event reordering
4. Dependency forgery

Future attack classes:

- Timestamp manipulation
- Attribute forgery
- Stealth poisoning
- Targeted poisoning

---

## 9. Security Assumptions

The detector executes after graph construction and before downstream intrusion
detection.

The detector validates graph integrity rather than detecting malware directly.

---

## 10. Out of Scope

- Kernel compromise
- Firmware attacks
- Hardware attacks
- Cryptographic attacks against QuantumGuard+
- Runtime memory corruption of the detector

---

## 11. Position Relative to Existing Work

Existing provenance intrusion detection systems generally assume that the input
provenance graph is trustworthy.

This work provides an integrity verification layer that operates before those
systems, allowing them to consume validated provenance graphs.
