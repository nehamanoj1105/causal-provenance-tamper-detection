# Experimental State

**Repo:** `nehamanoj1105/causal-provenance-tamper-detection`
**Commit:** `d8b8617c4478846ace3b82dbd9fb819c8e2f6a64` (2026-08-09)
**Snapshot:** `audit/repository_snapshot/` (code, docs, committed results, env)
**Preserved committed results:** `audit/original_results_backup/` and
`audit/repository_snapshot/committed_results/`

## 1. What the repository claims

Headline numbers committed in `results/`:

| Claim | Committed value |
|---|---|
| Synthetic Rule Engine (seed 42) | P 0.8125 / R 0.6500 / F1 0.7222 / Acc 0.9457 |
| "Multi-seed" stats | `± 0.0000` on every metric |
| GraphSAGE (seed 42) | F1 0.5600, ROC-AUC 0.8776, PR-AUC 0.5634, tau* 0.70 |
| DARPA 1r/3/5m/6r (Rule Engine F1) | 0.4783 / 0.4706 / 0.4571 / 0.3438 |
| Mimicry (none/light/medium/heavy) RE F1 | 0.7778 / 0.3000 / 0.1657 / 0.0882 |
| Rule Engine ROC-AUC (all mimicry) | 1.0000 |
| Ablation (ALL/not-Struct/not-Temp/not-Sem) F1 | 0.7222 / 0.5161 / 0.6667 / 0.5161 |
| Scalability 1M edges RE detect | 16.99 s, 58,857 edges/s |

## 2. What is actually implemented

| Component | Reality |
|---|---|
| Synthetic graph | `src/graph_construction/synthetic.py`, deterministic by seed |
| DARPA parser | `src/graph_construction/cdm_parser.py` — real CDM Avro, streaming. **Verified correct on real Theia E3 data** |
| DARPA loader | `graph_loader.py` reads `data/parsed/*.csv`; `cross_dataset.py` silently falls back to synthetic if absent |
| Poisoning | `poisoning_injection.py` — shallow copy mutates input for reorder/forgery; deletion labels inferred from naming |
| Mimicry | `mimicry_attack.py` — noise tagged `mimicry=True`, 52-80% violate rules |
| Rule engine | `rule_engine.py` + `rule_based.py` — 15 rules, binary violations only |
| GraphSAGE | `src/ml/train.py::train_pipeline` — trains & thresholds on the same graph; no split |
| Metrics | `src/eval/metrics.py` — no `roc_auc`; robustness uses a `getattr` default of 1.0 |
| Scalability | `src/eval/scalability.py` — mixes RE detection with GS inference |

## 3. Reproducible (verified in previous audit, unchanged)

- Synthetic Rule Engine @ seed 42 (exact).
- GraphSAGE @ seed 42 (exact, but leaky).
- Mimicry table @ seed 42 (exact).
- Rule statistics and ablation @ seed 42 (exact).
- Real parsing counts: Theia 3 = 20,157/297,777; Theia 5m = 34,835/464,858
  (**exact match to committed `docs/dataset_statistics.md`**).

## 4. Invalid / not defensible

- **"Multi-seed" = single seed** `± 0.0000`.
- **GraphSAGE train/test leakage** (no val/test; threshold on test).
- **Rule Engine ROC-AUC = 1.0** fabricated by fallback.
- **DARPA numbers** not reproducible from the repo (data absent + silent
  synthetic fallback + first-50k truncation + synthetic post-hoc attacks).
- **Mimicry** not invariant-preserving and attribute-tagged.
- **Deletion/reorder/forgery ground truth** partially undefined or
  undetectable.
- **Scalability** compares RE inference vs GS inference; GS training cost not
  made explicit.

## 5. Requires replacement (new work in this audit)

| Old | Replacement |
|---|---|
| Single-seed "multi-seed" table | Real 10-seed corrected multi-seed study |
| Leaky GraphSAGE | Disjoint train/val/test GraphSAGE with validation-only threshold |
| Fabricated RE ROC-AUC | Violation-count continuous score to genuine ROC/PR-AUC |
| Synthetic-fallback DARPA table | Real Theia 3 & 5m results (1r/6r marked unavailable), explicitly synthetic-controlled poisoning on real graphs |
| Flawed poisoning | Immutable ground truth + assertions, fixed shallow copy |
| Invalid mimicry | Invariant-preserving, attribute-free mimicry |
| Mixed scalability | Separate RE inference / GS training / GS inference / preprocessing |

## 6. Real data status

| Dataset | Status |
|---|---|
| theia-3 | obtained & parsed |
| theia-5m | obtained & parsed |
| theia-1r | **unavailable** (Drive quota 403) |
| theia-6r | **unavailable** (Drive quota 403) |
| Ground-truth PDF / schema / op-log | obtained |

Details: `audit/DATASET_MANIFEST.md`.
