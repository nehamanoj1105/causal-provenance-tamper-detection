# Mid-Review Presentation — Corrected Content (Task B Phase 2)

Structural template: `Causal_Provenance_Mid_Review.pptx.pptx` (12 slides, 16:9).
Every number below is traced to `audit/FINAL_RESEARCH_REPORT/verified_numbers.json`
(recomputed from `audit/raw_runs/`; 549 verified claims, 226-check validation,
deterministic re-runs). No number is invented. Where the template's existing
slide carried a number that is **not** supported by the corrected audit, the
correction is flagged in `[CORRECTION]` and the slide is rebuilt in the PPTX.

Naming convention used throughout:
- **ORIGINAL** = the repository's shipped protocol (leaky GraphSAGE, hard-coded
  ROC-AUC, mimicry with a `mimicry:True` attribute leak). Kept as an audit finding.
- **CORRECTED** = the authoritative leakage-free / label-free protocol used for
  all manuscript and presentation claims.

---

## Slide 1 — Title

- **Title:** Causal Consistency as a Defense: Detecting Provenance Graph Poisoning
- **Presenter:** Neha Manoj — AM.SC.U4CYS23030
- **Guide:** Devi Rajeev
- **Event:** S7 Project Mid Review
- **Repo:** https://github.com/nehamanoj1105/causal-provenance-tamper-detection
- **Figure/table:** title card (no data)
- **Speaker notes:** One sentence: we test whether the provenance graph that
  every forensic and ML detector trusts is itself internally consistent, and
  build a deterministic checker for it.
- **Source:** repo README.

---

## Slide 2 — Outline

- **Content:** Introduction → Problem Definition → Literature Review → Research
  Gap → Methodology → Design/Architecture → Algorithms → Result Analysis →
  Timeline → References.
- **Source:** template slide 2.

---

## Slide 3 — Introduction

- **Content:**
  - Provenance graphs are the audit trail of a system: nodes are processes,
    files and network sockets; edges are reads, writes, spawns and connects.
    They are the primary evidence for reconstructing an attack.
  - Provenance-based intrusion detection (PIDS) assumes this graph is
    trustworthy — but an attacker with privileged log access can delete, forge,
    reorder or re-attach events.
  - This project treats **integrity of the evidence** as a separate problem from
    intrusion detection: verify the graph before any downstream detector uses it.
  - Approach: 15 deterministic causal/semantic OS invariants (a rule engine),
    benchmarked head-to-head against a GraphSAGE GNN baseline on synthetic
    graphs and on real DARPA Transparent Computing (TC E3) audit data.
- **Figure/table:** schematic of a provenance graph with a poisoned edge.
- **Speaker notes:** Emphasise the "evidence integrity ≠ intrusion detection"
  framing; the rule engine is an explainable pre-filter.
- **Source:** template slide 3; README; `src/detection/rule_engine.py`.

---

## Slide 4 — Problem Definition

- **Content:**
  - **Motivation:** forensic reconstruction, root-cause analysis and every
    ML-based provenance detector assume the graph is ground truth — an
    assumption never tested against an adversary who can write to the log.
  - **Problem statement:** given a provenance graph that may have been tampered
    with (edge deletion, insertion, reordering, or dependency forgery, possibly
    hidden with mimicry noise), flag exactly which edges are inconsistent with
    valid OS causal/semantic behaviour.
  - **Objectives:** (1) formalise the OS-level invariants a genuine provenance
    graph must satisfy; (2) build a deterministic rule engine that scores
    violations and compare it to a learned GraphSAGE baseline; (3) evaluate both
    on synthetic poisoning and real DARPA TC E3 traces, under mimicry noise and
    at scale (up to 1,000,000 edges).
- **Speaker notes:** Distinguish the integrity question ("is this edge
  consistent?") from the anomaly question ("is this behaviour malicious?").
- **Source:** template slide 4.

---

## Slide 5 — Literature Review Summary

- **Content (table, unchanged from template except the last row):**

| Year | Approach | Key contribution | Demerit | Dataset | Metric |
|---|---|---|---|---|---|
| 2020 | Unicorn | Graph-kernel embeddings for whole-system provenance | Graph-level, coarse; hard to localise root cause | DARPA TC | Detection / similarity |
| 2022 | ThreaTrace | Node-level GNN classification | Still trusts the input graph; mimicry-vulnerable | DARPA TC | P / R / F1 |
| 2023 | Mimicry study | Formalised adversarial mimicry vs GNN PIDS | ~100 % evasion by diluting node embeddings | DARPA TC | Evasion rate |
| 2024 | FLASH | Sequence + graph representation learning | Black box; no per-edge violation | DARPA TC E3 | F1 / PR |
| 2024 | Kairos | Practical whole-system PIDS + investigation | Assumes the graph is untampered | DARPA TC E3 | F1, FPR |
| 2025 | ProvX | Counterfactual subgraph explanations | Explains the decision, not the input integrity | DARPA TC | Explanation fidelity |
| 2025–26 | Causal Rule Engine (ours) | 15 deterministic causal/semantic invariants; explainable; runs before any learned detector | Cannot catch an attack that preserves all 15 invariants | Synthetic + DARPA TC E3 | P/R/F1/ROC-AUC, runtime & memory |

- **Speaker notes:** State explicitly that these are the cited systems and their
  reported metrics from the literature; we do **not** re-run them, so no head-to-head
  SOTA claim is made.
- **Source:** template slide 5; `SOTA.md`.

---

## Slide 6 — Research Gap

- **Content:**
  - Rule/specification systems (Holmes, Sleuth, Poirot, RapSheet) need manual
    upkeep, cannot generalise, and never ask whether the log itself is intact.
  - Statistical detectors (NoDoze, PrioTracker, ProvDetector) use shallow
    topological signals and inherit high false-positive rates from rare-but-benign
    behaviour.
  - GNN detectors (Unicorn, FLASH, ThreaTrace, MAGIC, ShadeWatcher) learn
    "normal" from neighbourhood embeddings — exactly what mimicry noise dilutes
    (NDSS'23 reports close to 100 % evasion).
  - Every one of these assumes the provenance graph is already trustworthy; none
    verify that its causal structure is internally consistent.
  - **Gap:** a deterministic, explainable layer that checks provenance graph
    integrity itself, before any downstream detector consumes it, and keeps
    working even when mimicry breaks GNN approaches.
- **Speaker notes:** This slide motivates the integrity-layer contribution.
- **Source:** template slide 6.

---

## Slide 7 — Methodology

- **Content (table; corrected against verified artifacts):**

| Category | Details |
|---|---|
| Datasets | (a) synthetic provenance graphs (80 nodes / 179 edges, seeded); (b) real DARPA TC E3 traces — Theia "3" and Theia "5m", parsed by the repo's CDM parser, **truncated to the first 50,000 edges**. Scenarios 1r and 6r were not available and are **not** reported. |
| Graph schema | Directed multigraph; nodes = process / file / network socket; edges = spawn / execute / read / write / connect / delete with timestamps and sequence numbers. |
| Detection methods | Deterministic Causal Rule Engine (15 invariants) vs. GraphSAGE (PyTorch Geometric) baseline. |
| Technology stack | Python 3.13, PyTorch 2.14 (CPU), PyTorch Geometric 2.8, NetworkX, scikit-learn. |
| Training config | GraphSAGE: 30 epochs, lr 0.01, hidden 64, weighted BCE, seed 42 (original); corrected protocol uses disjoint 60/20/20 train/val/test and a validation-only threshold. |
| Evaluation metrics | Precision, Recall, F1, Accuracy, Balanced Accuracy, MCC, FPR, FNR, Specificity, ROC-AUC, PR-AUC. |
| Scale / profiling | Runtime, RSS and peak memory, throughput from 10k to 1M edges. |
| Testing | `pytest -q`: **98 passed, 5 failed** — the 5 failures are `tests/test_graph_loader.py` and are caused only by the absence of gitignored `data/parsed/*.csv` (environmental, not a code defect). |

- **`[CORRECTION]`** The template says "103 unit tests" and "DARPA 4 scenarios".
  The verified current state is **98 passed / 5 failed** and **2 of 4 DARPA
  scenarios available**. 1r and 6r are not available in this environment and
  must not be fabricated.
- **Speaker notes:** Call out the 50k-edge cap explicitly; it is a subgraph
  slice, not the full dataset.
- **Source:** `verified_numbers.json` (`synthetic`, `real_theia`); pytest run;
  `scripts/run_cross_dataset.py`.

---

## Slide 8 — Design / Architecture

- **Content:**
  - Pipeline: raw log → CDM parser → provenance graph → **causal-consistency
    rule engine** → (optional) GraphSAGE → evaluation.
  - The rule engine is a deterministic, explainable integrity layer that sits
    **before** any learned detector.
  - Novelty: it verifies the causal and semantic consistency of the graph
    itself, not just anomalous behaviour.
- **Figure/table:** architecture diagram (data flow).
- **Speaker notes:** Stress that the integrity layer is independent of and
  composable with any downstream detector.
- **Source:** template slide 8; `src/`.

---

## Slide 9 — Algorithms

- **Content:**
  - **Rule Engine — 15 deterministic invariants:**
    - Structural (6): duplicate edges, duplicate events, self-loops, missing
      nodes, unspawned processes, sequence gaps.
    - Temporal (4): timestamp bounds, parent→child spawn ordering,
      process-activity ordering, sequence monotonicity.
    - Semantic (5): spawn / execute / read-write / connect / delete edges must
      target the right node type.
  - An edge is flagged anomalous if it violates ≥ 1 rule; the violation score =
    number of rules broken (a genuine continuous ranking score).
  - **GraphSAGE baseline:** 2-layer inductive GNN, weighted loss for class
    imbalance, 30 epochs, seed 42; decision threshold swept 0.05→1.00.
  - **Protocols:** the shipped repo trains and thresholds on the same graph
    (**ORIGINAL**, leaky). The corrected protocol uses disjoint train/val/test
    edges, restricts message passing to train+val edges, and selects the
    threshold on validation only (**CORRECTED**).
- **Speaker notes:** Explain the leakage finding honestly — the corrected number
  is the defensible one.
- **Source:** `src/detection/rule_engine.py`; `audit/graphsage_leakage_audit.md`;
  `audit/experiments/corrected/harness.py`.

---

## Slide 10 — Result Analysis

- **Content (table; ORIGINAL vs CORRECTED shown where they differ):**

| Benchmark | Detector | Precision | Recall | F1 |
|---|---|---|---|---|
| Synthetic (ORIGINAL, seed 42) | Rule Engine | 0.8125 | 0.6500 | 0.7222 |
| Synthetic (ORIGINAL, seed 42) | GraphSAGE (τ*=0.70, leaky) | 0.7000 | 0.4667 | 0.5600 |
| **Synthetic (CORRECTED, 10 seeds)** | **Rule Engine** | **0.7146 ± 0.0948** | **0.9329 ± 0.0629** | **0.8048 ± 0.0627** |
| **Synthetic (CORRECTED, 10 seeds)** | **GraphSAGE (leakage-free)** | **0.3416 ± 0.3093** | **0.5017 ± 0.3637** | **0.3224 ± 0.1942** |
| DARPA Theia-3 (50k cap, synthetic post-collection poison) | Rule Engine | 0.9195 ± 0.0070 | 0.7667 ± 0.0720 | 0.8347 ± 0.0459 |
| DARPA Theia-5m (50k cap, synthetic post-collection poison) | Rule Engine | — | — | 0.8504 ± 0.0599 |
| Heavy mimicry (CORRECTED, label-free) | Rule Engine | 0.7146 | 0.9329 | 0.8048 (unchanged none→heavy) |
| Heavy mimicry (ORIGINAL generator, attribute leak) | Rule Engine | 0.0464 | 0.9000 | 0.0882 |

- **Key points to state:**
  - Paired RuleEngine − GraphSAGE F1 difference = **+0.4824** (95 % CI
    0.3285–0.6363; Wilcoxon p = 0.001953; Cohen's dz = 2.24) on identical test
    instances. The ROC-AUC difference (+0.1239) is **not** significant
    (p = 0.1055).
  - Rule Engine ROC-AUC is a genuine continuous violation-score AUC =
    **0.9528 ± 0.0312** (corrected), **not** 1.0000. The 1.0000 in the template
    is a hard-coded `getattr(..., 1.0)` fallback and is retracted.
  - Scalability: 1M edges, corrected protocol, Rule Engine inference
    **34.48 s** (throughput ≈ **29,007 edges/s**), peak Python allocation
    ≈ **971 MB**, end-to-end **187.17 s**.
- **`[CORRECTION]`** Retract "ROC-AUC stays 1.0000"; correct "1M edges in 15.26 s
  / 364 MB" to the corrected 34.48 s / ≈971 MB.
- **Speaker notes:** Present the corrected numbers as authoritative and label the
  original ones as audit findings.
- **Source:** `verified_numbers.json` (`synthetic`, `mimicry`, `real_theia`,
  `scalability`, `rule_score`); `audit/rule_engine_roc_audit.md`.

---

## Slide 11 — Project Timeline (Plan)

- **Content (timeline table):**

| Phase | Milestone | Status |
|---|---|---|
| 1 | Schema, CDM parser, synthetic + DARPA loader | Complete |
| 2 | 15-rule engine + GraphSAGE baseline | Complete |
| 3 | Evaluation suite (synthetic, DARPA, mimicry, ablation, scalability) | Complete |
| 4 | Rigorous audit: leakage-free protocol, multi-seed statistics, poisoning & DARPA ground-truth audit | Complete |
| 5 | Corrected manuscripts (conference + journal) and journal-ready tables | Complete |
| 6 | Remaining before submission: full 4-scenario DARPA data; hybrid GraphSAGE + rule-score detector; post-quantum signing / Merkle anchoring integration | Planned |

- **`[CORRECTION]`** The template's "Current Status / Future Plan" slide is
  replaced by an actual timeline consistent with the audit.
- **Speaker notes:** Be honest that 1r/6r are unavailable and are planned work.
- **Source:** `audit/` artifacts; this report.

---

## Slide 12 — References

- **Content (unchanged from template):** the nine cited works plus the author's
  own paper and repository. No new references are invented.
- **Source:** template slide 12.

---

## Numbers that must NOT appear in the presentation

| Value | Why |
|---|---|
| Rule Engine ROC-AUC = 1.0000 | Hard-coded fallback, not computed. |
| Synthetic Rule Engine P=0.8125 / R=0.6500 / F1=0.7222 as *the* result | Single-seed committed value; corrected 10-seed is 0.7146/0.9329/0.8048. |
| GraphSAGE F1 = 0.5600 as *the* result | Leaky protocol; corrected 0.3224. |
| "103 unit tests passing" | Verified: 98 pass / 5 fail. |
| DARPA 4-scenario average | Only Theia-3 and Theia-5m available; 1r/6r absent. |
| 1M edges in 15.26 s / 364 MB | Corrected: 34.48 s / ≈971 MB. |
| Mimicry "Rule Engine 0.0882 F1 under heavy" as robustness | Attribute-leak artifact of the invalid original generator. |
| Any claim that DARPA provides ground-truth provenance poisoning | Attacks are synthetic post-collection injections. |
