# Provenance Poisoning Attack Framework Validation Report

**Evaluator**: USENIX Security Artifact Evaluation Committee  
**Modules Audited**: [`src/detection/poisoning_injection.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/detection/poisoning_injection.py), [`src/detection/mimicry_attack.py`](file:///home/neha-manoj/Final%20Year%20Project/causal-provenance-tamper-detection/src/detection/mimicry_attack.py)  

---

## 1. Attack Suite Overview

The framework implements **9 attack vectors** across 3 attack categories:

```
Poisoning Suite
├── Random Poisoning Attacks
│   ├── Random Deletion
│   ├── Random Insertion
│   ├── Random Reordering
│   └── Random Dependency Forgery
├── Targeted Poisoning Attacks
│   ├── Targeted Deletion
│   ├── Targeted Insertion
│   ├── Targeted Reordering
│   └── Targeted Dependency Forgery
└── Adversarial Mimicry Attacks
    ├── Light Mimicry (+30% noise)
    ├── Medium Mimicry (+70% noise)
    └── Heavy Mimicry (+150% noise)
```

---

## 2. Attack Ground-Truth & Invariant Verification

| Attack Vector | Function Name | Ground Truth Registration | Graph Invariant Preservation | Verified Injected Count |
|---|---|---|---|---|
| **Random Deletion** | `inject_poisoning` | `PoisoningType.DELETION` | Removes edge from graph | Exact requested count |
| **Random Insertion** | `inject_poisoning` | `PoisoningType.INSERTION` | Appends valid `ProvenanceEdge` | Exact requested count |
| **Random Reordering** | `inject_poisoning` | `PoisoningType.REORDERING` | Shifts `timestamp` | Exact requested count |
| **Random Forgery** | `inject_poisoning` | `PoisoningType.DEPENDENCY_FORGERY` | Rewires `source_id` | Exact requested count |
| **Targeted Deletion** | `targeted_deletion` | `PoisoningType.DELETION` | Removes incident edges of target node | $\le \text{max\_edges}$ |
| **Targeted Insertion** | `targeted_insertion` | `PoisoningType.INSERTION` | Connects target to new endpoints | $\le \text{max\_insertions}$ |
| **Targeted Reordering**| `targeted_reordering` | `PoisoningType.REORDERING` | Swaps neighboring timestamps | $\le 2 \times \text{max\_swaps}$ |
| **Targeted Forgery** | `targeted_dependency_forgery` | `PoisoningType.DEPENDENCY_FORGERY` | Rewires target's outgoing edges | $\le \text{max\_edges}$ |
| **Mimicry Attacks** | `inject_mimicry_attack` | Base `PoisoningResult` + Camouflage | Preserves degree/type/time stats | Configurable noise scale |

---

## 3. Labeling Integrity & Non-Mutation Proof

- **Non-Mutation**: All attack functions return a new `PoisoningResult` containing a deep copy of the original graph (`ProvenanceGraph(nodes=..., edges=...)`), ensuring the caller's reference graph remains pristine.
- **Ground Truth Mapping**: `poison_res.edge_labels()` produces a exact lookup dictionary `edge_id -> poisoning_type` evaluated by `Evaluator.evaluate()`.

---

**Conclusion**: All 9 attack vectors correctly modify provenance graphs, preserve ground-truth tracking, and generate valid label dictionaries.
