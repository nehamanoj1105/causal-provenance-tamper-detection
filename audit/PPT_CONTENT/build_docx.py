"""Build the mid-review DOCX from the corrected slide content.

Produces a slide-by-slide document (title, content, verified numbers,
figure/table, speaker notes, source artifact) matching
audit/PPT_CONTENT/MID_REVIEW_PPT_CONTENT.md.
"""
from docx import Document
from docx.shared import Pt

OUT = "audit/PPT_CONTENT/MID_REVIEW_PPT_CONTENT.docx"
doc = Document()
doc.add_heading("Causal Consistency as a Defense: Detecting Provenance Graph Poisoning", 0)
doc.add_paragraph("S7 Project Mid Review — Corrected Content (Task B Phase 2)")
doc.add_paragraph("Presenter: Neha Manoj (AM.SC.U4CYS23030) | Guide: Devi Rajeev")
doc.add_paragraph("All numbers traced to audit/FINAL_RESEARCH_REPORT/verified_numbers.json "
                  "(549 verified claims; 226-check validation; deterministic re-runs).")

SLIDES = [
    ("Slide 1 — Title", [
        "Title: Causal Consistency as a Defense: Detecting Provenance Graph Poisoning",
        "Presenter: Neha Manoj — AM.SC.U4CYS23030 | Guide: Devi Rajeev",
        "Event: S7 Project Mid Review",
        "Repo: https://github.com/nehamanoj1105/causal-provenance-tamper-detection",
    ], "Title card (no data).",
       "One sentence: we test whether the provenance graph every forensic and ML detector trusts is itself internally consistent, and build a deterministic checker for it.",
       "repo README."),
    ("Slide 2 — Outline", [
        "Introduction, Problem Definition, Literature Review, Research Gap, "
        "Methodology, Design/Architecture, Algorithms, Result Analysis, Timeline, References.",
    ], "None.", "Follow the template's 10-minute structure.", "template slide 2."),
    ("Slide 3 — Introduction", [
        "Provenance graphs are the audit trail: nodes are processes, files, network sockets; edges are reads, writes, spawns, connects.",
        "PIDS assumes this graph is trustworthy; a privileged attacker can delete, forge, reorder or re-attach events.",
        "This project treats integrity of the evidence as a separate problem from intrusion detection.",
        "Approach: 15 deterministic causal/semantic OS invariants (a rule engine) vs a GraphSAGE GNN baseline, on synthetic graphs and real DARPA TC E3 audit data.",
    ], "Schematic of a provenance graph with a poisoned edge.",
       "Emphasise 'evidence integrity != intrusion detection'; the rule engine is an explainable pre-filter.",
       "template slide 3; README; src/detection/rule_engine.py."),
    ("Slide 4 — Problem Definition", [
        "Motivation: forensic reconstruction, root-cause analysis and every ML provenance detector assume the graph is ground truth — never tested against an adversary who can write to the log.",
        "Problem statement: given a possibly tampered graph (deletion, insertion, reordering, dependency forgery, possibly hidden with mimicry noise), flag exactly which edges are inconsistent with valid OS causal/semantic behaviour.",
        "Objectives: (1) formalise the OS-level invariants; (2) build a deterministic rule engine and compare to GraphSAGE; (3) evaluate on synthetic poisoning and real DARPA TC E3 traces, under mimicry and up to 1,000,000 edges.",
    ], "None.", "Distinguish the integrity question ('is this edge consistent?') from the anomaly question ('is this behaviour malicious?').",
       "template slide 4."),
    ("Slide 5 — Literature Review Summary", [
        "Table: Unicorn 2020; ThreaTrace 2022; Mimicry study 2023; FLASH 2024; Kairos 2024; ProvX 2025; Causal Rule Engine (ours) 2025-26.",
        "Ours: 15 deterministic causal/semantic invariants; explainable; runs before any learned detector. Demerit: cannot catch an attack that preserves all 15 invariants.",
    ], "The template's literature table (unchanged).",
       "State that these are cited systems with their reported metrics; we do NOT re-run them, so no head-to-head SOTA claim is made.",
       "template slide 5; SOTA.md."),
    ("Slide 6 — Research Gap", [
        "Rule/specification systems (Holmes, Sleuth, Poirot, RapSheet) need manual upkeep, cannot generalise, and never check whether the log is intact.",
        "Statistical detectors (NoDoze, PrioTracker, ProvDetector) use shallow topology and inherit high FPRs.",
        "GNN detectors (Unicorn, FLASH, ThreaTrace, MAGIC, ShadeWatcher) learn 'normal' from neighbourhood embeddings — exactly what mimicry dilutes (NDSS'23 reports ~100% evasion).",
        "Gap: a deterministic, explainable layer that checks provenance graph integrity itself, before any downstream detector, and survives mimicry.",
    ], "None.", "This slide motivates the integrity-layer contribution.", "template slide 6."),
    ("Slide 7 — Methodology", [
        "Datasets: synthetic provenance graphs (80 nodes / 179 edges, seeded) + real DARPA TC E3 traces Theia '3' and Theia '5m', parsed by the repo's CDM parser, TRUNCATED to the first 50,000 edges. 1r and 6r unavailable — not reported.",
        "Graph schema: directed multigraph; nodes process/file/network socket; edges spawn/execute/read/write/connect/delete with timestamps and sequence numbers.",
        "Detection: deterministic Causal Rule Engine (15 invariants) vs GraphSAGE (PyTorch Geometric).",
        "Stack: Python 3.13, PyTorch 2.14 (CPU), PyTorch Geometric 2.8, NetworkX, scikit-learn.",
        "Training: GraphSAGE 30 epochs, lr 0.01, hidden 64, weighted BCE, seed 42 (ORIGINAL). CORRECTED: disjoint 60/20/20 train/val/test, validation-only threshold.",
        "Metrics: Precision, Recall, F1, Accuracy, Balanced Accuracy, MCC, FPR, FNR, Specificity, ROC-AUC, PR-AUC.",
        "Scale: runtime, RSS and peak memory, throughput 10k-1M edges.",
        "Testing: pytest -q = 98 passed / 5 failed (5 failures are tests/test_graph_loader.py, caused only by absent gitignored data/parsed/*.csv).",
    ], "Methodology table.",
       "[CORRECTION] Template says '103 unit tests' and 'DARPA 4 scenarios'; verified state is 98/5 and 2 of 4 scenarios available. Call out the 50k-edge cap explicitly.",
       "verified_numbers.json (synthetic, real_theia); pytest; scripts/run_cross_dataset.py."),
    ("Slide 8 — Design / Architecture", [
        "Pipeline: raw log -> CDM parser -> provenance graph -> causal-consistency rule engine -> (optional) GraphSAGE -> evaluation.",
        "The rule engine is a deterministic, explainable integrity layer that sits before any learned detector.",
        "Novelty: verifies causal and semantic consistency of the graph itself, not just anomalous behaviour.",
    ], "Architecture diagram (data flow).", "Stress that the integrity layer is independent of and composable with any downstream detector.",
       "template slide 8; src/."),
    ("Slide 9 — Algorithms", [
        "Rule Engine — 15 deterministic invariants: Structural (6) duplicate edges, duplicate events, self-loops, missing nodes, unspawned processes, sequence gaps; Temporal (4) timestamp bounds, parent->child spawn ordering, process-activity ordering, sequence monotonicity; Semantic (5) spawn/execute/read-write/connect/delete must target the right node type.",
        "Edge flagged if it violates >=1 rule; violation score = number of rules broken (genuine continuous ranking score).",
        "GraphSAGE: 2-layer inductive GNN, weighted loss, 30 epochs, seed 42; threshold swept 0.05-1.00.",
        "Protocols: ORIGINAL trains and thresholds on the same graph (leaky). CORRECTED uses disjoint train/val/test, message passing on train+val only, threshold on validation only.",
    ], "Algorithm boxes / pseudo-code.",
       "Explain the leakage finding honestly; the corrected number is the defensible one.",
       "src/detection/rule_engine.py; audit/graphsage_leakage_audit.md; audit/experiments/corrected/harness.py."),
    ("Slide 10 — Result Analysis", [
        "Synthetic Rule Engine ORIGINAL (seed 42): P 0.8125 / R 0.6500 / F1 0.7222.",
        "Synthetic GraphSAGE ORIGINAL (leaky, tau*=0.70): P 0.7000 / R 0.4667 / F1 0.5600.",
        "Synthetic Rule Engine CORRECTED (10 seeds): P 0.7146+-0.0948 / R 0.9329+-0.0629 / F1 0.8048+-0.0627.",
        "Synthetic GraphSAGE CORRECTED (leakage-free): P 0.3416+-0.3093 / R 0.5017+-0.3637 / F1 0.3224+-0.1942.",
        "DARPA Theia-3 (50k cap, synthetic post-collection poison) Rule Engine: P 0.9195+-0.0070 / R 0.7667+-0.0720 / F1 0.8347+-0.0459.",
        "DARPA Theia-5m (50k cap, synthetic post-collection poison) Rule Engine F1 0.8504+-0.0599.",
        "Heavy mimicry CORRECTED (label-free): Rule Engine P 0.7146 / R 0.9329 / F1 0.8048 (unchanged none->heavy).",
        "Heavy mimicry ORIGINAL generator (attribute leak): P 0.0464 / R 0.9000 / F1 0.0882.",
        "Paired RuleEngine - GraphSAGE F1 difference +0.4824 (95% CI 0.3285-0.6363; Wilcoxon p=0.001953; dz=2.24). ROC-AUC difference +0.1239 NOT significant (p=0.1055).",
        "Rule Engine ROC-AUC CORRECTED = 0.9528+-0.0312 (genuine continuous score). 1.0000 is retracted (hard-coded fallback).",
        "Scalability 1M edges CORRECTED: inference 34.48 s, peak ~971 MB, end-to-end 187.17 s (~29,007 edges/s).",
    ], "Result table (ORIGINAL vs CORRECTED).",
       "[CORRECTION] Retract 'ROC-AUC stays 1.0000'; correct '1M edges in 15.26 s / 364 MB' to 34.48 s / ~971 MB. Present corrected numbers as authoritative.",
       "verified_numbers.json (synthetic, mimicry, real_theia, scalability, rule_score)."),
    ("Slide 11 — Project Timeline (Plan)", [
        "Completed: pipeline end-to-end; 15-rule engine + GraphSAGE baseline; full evaluation suite (synthetic, DARPA, mimicry, ablation, scalability to 1M); rigorous audit (leakage-free protocol, 10-seed statistics, poisoning & DARPA ground-truth audit); pytest 98/5.",
        "Planned before submission: full 4-scenario DARPA TC E3 data (1r, 6r currently unavailable); hybrid GraphSAGE + rule-score detector; post-quantum signing / Merkle anchoring integration.",
    ], "Timeline table.",
       "[CORRECTION] Template's 'Current Status / Future Plan' replaced by an actual timeline consistent with the audit. Be honest that 1r/6r are unavailable.",
       "audit/ artifacts; this report."),
    ("Slide 12 — References", [
        "The nine cited works plus the author's own paper and repository (unchanged from the template). No new references are invented.",
    ], "Reference list.", "None.", "template slide 12."),
]

for title, content, fig, notes, src in SLIDES:
    doc.add_heading(title, level=1)
    doc.add_heading("Content", level=2)
    for c in content:
        doc.add_paragraph(c, style="List Bullet")
    doc.add_heading("Figure / Table", level=2)
    doc.add_paragraph(fig)
    doc.add_heading("Speaker Notes", level=2)
    doc.add_paragraph(notes)
    doc.add_heading("Source Artifact", level=2)
    doc.add_paragraph(src)

doc.add_heading("Numbers that must NOT appear", level=1)
for bad in [
    "Rule Engine ROC-AUC = 1.0000 (hard-coded fallback, not computed).",
    "Synthetic Rule Engine P=0.8125 / R=0.6500 / F1=0.7222 as THE result (single-seed; corrected 10-seed is 0.7146/0.9329/0.8048).",
    "GraphSAGE F1 = 0.5600 as THE result (leaky; corrected 0.3224).",
    "'103 unit tests passing' (verified 98 pass / 5 fail).",
    "DARPA 4-scenario average (only Theia-3 and Theia-5m available).",
    "1M edges in 15.26 s / 364 MB (corrected 34.48 s / ~971 MB).",
    "Mimicry heavy Rule Engine F1 0.0882 as robustness (attribute-leak artifact).",
    "Any claim that DARPA provides ground-truth provenance poisoning (attacks are synthetic post-collection injections).",
]:
    doc.add_paragraph(bad, style="List Bullet")

doc.save(OUT)
print("saved", OUT)
