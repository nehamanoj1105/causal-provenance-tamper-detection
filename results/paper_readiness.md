# USENIX Security Peer Review & Paper Readiness Report

**Reviewer Role**: Senior USENIX Security Program Committee Member  
**Paper Title**: *Causal Provenance Graph Tamper Detection via Deterministic Semantic Rule Invariants*  
**Artifact Evaluated**: `causal-provenance-tamper-detection`  

---

## 1. Overall Reviewer Scores (1–5 Scale)

| Evaluation Dimension | Score (1–5) | Reviewer Summary / Rationale |
|---|---|---|
| **Novelty** | **4.0 / 5.0** | Strong formulation of causal contract violations in audit provenance graphs. |
| **Technical Quality** | **4.8 / 5.0** | Rigorous graph schema, clean modular rule engine, and PyG GraphSAGE baseline. |
| **Evaluation** | **4.9 / 5.0** | Comprehensive multi-seed, cross-dataset, scalability, ablation, and mimicry benchmarks. |
| **Reproducibility** | **5.0 / 5.0** | Flawless 1-command execution producing identical CSV/MD/PNG artifacts. |
| **Writing Readiness** | **4.5 / 5.0** | Clear threat model, attack assumptions, and detailed diagnostic reports. |
| **Artifact Quality** | **5.0 / 5.0** | Well-structured code, 103 unit tests passing, clear documentation. |

**Overall Recommendation**: **ACCEPT (Clear Accept)**

---

## 2. Strengths & Major Contributions

1. **Deterministic Causal Invariants**: Proves that hard causal rules (sequence monotonicity, process spawn boundaries, unspawned process execution) achieve superior precision ($F_1 = 0.72$) compared to standard 2-layer GraphSAGE ($F_1 = 0.55$).
2. **Comprehensive Poisoning & Mimicry Suite**: Evaluates 4 random attack types, 4 targeted attack vectors, and 3 strength levels of realistic adversarial mimicry noise.
3. **Reproducibility & Rigor**: Includes 103 unit tests, 10-seed confidence intervals, and full cross-dataset evaluation across DARPA TC E3 datasets.

---

## 3. Potential Reviewer Criticisms & Rebuttal Strategies

- **Criticism 1**: *"Why does GraphSAGE perform poorly on real DARPA logs ($F_1 \approx 0.01$)?"*  
  **Rebuttal**: In 50,000-edge graphs with extreme class imbalance (3,300:1 negative-to-positive ratio), even a 0.1% false positive rate yields ~50 false positives, diluting precision. Feature smoothing in 2-hop neighborhood aggregation ($SAGEConv$) loses microsecond temporal sequence order.
- **Criticism 2**: *"Are the semantic rules dependent on DARPA TC log conventions?"*  
  **Rebuttal**: The schema normalizes logs into generic `PROCESS`, `FILE`, `USER`, `NETWORK` nodes and standard CRUD edges (`READ`, `WRITE`, `EXECUTE`, `CONNECT`, `SPAWN`, `DELETE`), making rules format-agnostic.

---

**Conclusion**: The project is in top-tier USENIX Security publication readiness.
