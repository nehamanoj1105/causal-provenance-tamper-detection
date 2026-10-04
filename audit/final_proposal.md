# Final Manuscript Proposal

Summary of what is being proposed for publication, based only on the corrected
audit. This is the plan that the two manuscripts realize.

## Working titles

* Conference: *Causal Consistency as a Defense: Detecting Provenance Graph Poisoning*
* Journal: *Causal Consistency as a Defense: Detecting and Auditing Provenance
  Graph Poisoning*

## Problem

Provenance-based intrusion detection trusts the stored provenance graph. An
adversary with storage access can delete, insert, reorder or forge events,
causing downstream detectors to reason over a tampered history. Existing work
mostly assumes a trusted graph.

## Proposed approach

A deterministic, training-free rule engine over fifteen causal-consistency
invariants, grouped as structural, temporal and semantic, plus a genuine
continuous severity-weighted anomaly score for ranking and AUC. Compared against
a GraphSAGE baseline under a leakage-free protocol.

## Key claims (all supported by the corrected audit)

1. On controlled synthetic poisoning (10 seeds), the rule engine reaches
   F1 0.805 ± 0.063, versus 0.322 ± 0.194 for leakage-free GraphSAGE; paired
   F1 difference +0.482 (95% CI [0.328, 0.636], Wilcoxon p = 0.002, dz = 2.24).
2. With a genuine continuous score the rule engine attains ROC-AUC
   0.953 ± 0.031 and PR-AUC 0.740 ± 0.080.
3. Rule-engine accuracy is invariant under invariant-preserving mimicry from
   none to heavy (F1 0.805 at every strength).
4. On real Theia provenance with synthetic post-collection poisoning, the rule
   engine reaches F1 0.835 ± 0.046 (scenario 3) and 0.850 ± 0.060 (scenario 5m);
   GraphSAGE is near chance.
5. The conventional GraphSAGE protocol (train on all edges, threshold on the
   scored labels) inflates F1 by 0.342 absolute (0.588 vs 0.246); this is an
   evaluation-design result, presented as a contribution.

## Category separation (strict)

* Real data only: dataset parse statistics (Table 1).
* Real data + synthetic post-collection poisoning: Theia 3 and 5m (Table 9).
* Synthetic controlled: main detection, mimicry, ablation, scalability, and the
  synthetic generalization rows.

No table pools these categories, and no text describes injected attacks as real
DARPA ground truth.

## Scope and non-claims

* No claim of detecting naturally occurring DARPA attacks.
* No deletion detection rate (deleted edges cannot be edge-matched).
* No GraphSAGE cross-graph transfer (target-trained only).
* Two of four Theia scenarios unavailable; reported as missing, not estimated.
* Rules check well-formedness, not intent; a consistency-preserving edit is not
  caught by this layer.

## Publication plan

1. Conference submission (6 pp) as the primary venue paper.
2. Journal extension (9 pp) adding parsing detail, cross-dataset
   generalization, ground-truth validity, leakage integrity, AUC verification and
   a full reproducibility section.
3. Artifact release: corrected protocol, raw per-seed results, validation and
   aggregation scripts.

## Rejected in this pass (do not submit)

* Any number from the original protocol that conflicts with the corrected audit:
  leaked GraphSAGE F1 (0.588 used as a result), fabricated rule-engine ROC-AUC
  = 1.000, single-seed results reported as multi-seed, and 1r/6r numbers backed
  by a silent fallback to synthetic graphs.
