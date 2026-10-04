# Ablation Audit (Phase 10)

Source: `audit/raw_runs/ablation_multiseed.json` / `.csv`. Configurations are the
repo's own (`src/eval/ablation.py`) run across 10 seeds
(1,7,13,21,42,99,123,256,512,1024) on fresh attack instances (intensity 5).

## 1. Category ablation — mean ± std over 10 seeds

| Configuration | Rules | Precision | Recall | F1 |
|---|---|---|---|---|
| ALL Rules Enabled | 15 | 0.8039 ± 0.0696 | 0.7900 ± 0.1022 | 0.7921 ± 0.0578 |
| Without Structural | 9 | 0.7394 ± 0.0884 | 0.5450 ± 0.1092 | 0.6203 ± 0.0789 |
| Without Temporal | 11 | 1.0000 ± 0.0000 | 0.6150 ± 0.0747 | 0.7592 ± 0.0569 |
| Without Semantic | 10 | 0.6967 ± 0.0915 | 0.4350 ± 0.0784 | 0.5293 ± 0.0619 |

The single-seed (42) committed values were 0.8125 / 0.7273 / 1.0000 / 0.7273
precision; the multi-seed means above are the defensible numbers.

## 2. Leave-one-rule-out — mean ± std over 10 seeds

| Removed rule | F1 (mean ± std) | ΔF1 vs ALL | Contributes? |
|---|---|---|---|
| (none — ALL) | 0.7921 ± 0.0578 | — | — |
| DuplicateEdgeRule | 0.7921 ± 0.0578 | 0.0000 | **No** |
| DuplicateEventRule | 0.7921 ± 0.0578 | 0.0000 | **No** |
| SelfLoopRule | 0.7921 ± 0.0578 | 0.0000 | **No** |
| MissingNodeRule | 0.7921 ± 0.0578 | 0.0000 | **No** |
| TimestampRule | 0.7921 ± 0.0578 | 0.0000 | **No** |
| ExecutionConsistencyRule | 0.7921 ± 0.0578 | 0.0000 | **No** |
| DeleteConsistencyRule | 0.7921 ± 0.0578 | 0.0000 | **No** |
| UnspawnedProcessRule | 0.7888 ± 0.0576 | -0.0033 | Marginal |
| ProcessActivityTemporalRule | 0.7998 ± 0.0572 | +0.0077 | **Negative** (hurts) |
| ParentChildTemporalRule | 0.7921 ± 0.0503 | 0.0000 | No (variance only) |
| SequenceMonotonicityRule | 0.7637 ± 0.0547 | -0.0284 | Weak |
| SpawnConsistencyRule | 0.7577 ± 0.0891 | -0.0344 | Weak |
| NetworkConsistencyRule | 0.7182 ± 0.0562 | -0.0739 | Moderate |
| ReadWriteConsistencyRule | 0.6619 ± 0.0852 | -0.1302 | **Yes** |
| SequenceGapRule | 0.6624 ± 0.0823 | -0.1297 | **Yes** |

## 3. Do the categories genuinely contribute?

- **Structural rules: yes, strongly.** Removing them drops F1 by 0.17
  (0.7921 → 0.6203), but the effect is carried almost entirely by
  `SequenceGapRule` (ΔF1 -0.13). The other five structural rules
  (`DuplicateEdge`, `DuplicateEvent`, `SelfLoop`, `MissingNode`,
  `UnspawnedProcess`) contribute ≈0 on this synthetic generator, because it never
  produces those violations.
- **Semantic rules: yes, strongly.** Removing them drops F1 by 0.26
  (0.7921 → 0.5293), driven by `ReadWriteConsistencyRule` (ΔF1 -0.13),
  `NetworkConsistencyRule` (-0.07), and `SpawnConsistencyRule` (-0.03).
- **Temporal rules: weakly, and one is harmful.** Removing all temporal rules
  *improves precision to 1.0* but lowers recall, net ΔF1 -0.03. Individually,
  `SequenceMonotonicityRule` contributes -0.03, while
  `ProcessActivityTemporalRule` **reduces** F1 when present (+0.008 when
  removed) — i.e. it fires on benign synthetic activity.
- **Seven of the fifteen rules contribute exactly zero** to F1 on this benchmark
  (DuplicateEdge, DuplicateEvent, SelfLoop, MissingNode, Timestamp, Execution,
  Delete). Reporting "15 deterministic semantic rules" overstates the effective
  rule set for this task.

## 4. Caveat

These conclusions are specific to the synthetic generator and the random attack
suite, which never exercise duplicate-ID, self-loop, missing-node, or
delete-type invariants. On DARPA data some of these rules do fire (the repo notes
`UnspawnedProcessRule` flags 27,149 nodes on full 1r), but no per-rule DARPA
ablation is runnable here because the data is absent.
