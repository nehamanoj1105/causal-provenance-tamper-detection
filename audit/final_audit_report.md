# Final Audit Report (v2, corrected-evaluation)

**Repository:** `nehamanoj1105/causal-provenance-tamper-detection`
**Commit audited:** `d8b8617c4478846ace3b82dbd9fb819c8e2f6a64` (branch `main`)
**Paper:** *Causal Consistency as a Defense: Detecting Provenance Graph Poisoning*
**Audit date:** 2026-10-02
**Environment:** Python 3.13.15, PyTorch 2.14.1+cpu, PyG 2.8.0.post1,
scikit-learn 1.9.1, NumPy 2.5.3, Linux 6.8 (gke), CPU-only, 16.8 GB RAM.

> This report does **not** rewrite the paper. It establishes the scientifically
> defensible result set first. Three result sets are kept separate throughout:
> **ORIGINAL-REPRODUCTION** (repo protocol, unchanged), **AUDITED-REPRODUCTION**
> (repo protocol + integrity/ground-truth checks + real data), and
> **CORRECTED-EVALUATION** (leakage-free, multi-seed, statistically rigorous).

---

## 1. Executive Summary

The repository is well-structured research code. Its **Rule Engine** idea is
sound and, on controlled synthetic poisoning, is competitive and genuinely
mimicry-robust. However, **none of the paper's headline comparative numbers are
defensible as written**, for five independent reasons:

1. **GraphSAGE train/test leakage.** `src/ml/train.py::train_pipeline` trains on
   *all* edges and then selects the operating threshold by maximising F1 on the
   *same* labels it is scored on. There is no validation or test split
   (`create_train_val_test_masks` is defined but never called). This inflates
   GraphSAGE F1 by ≈0.24–0.34 absolute.
2. **Fabricated Rule-Engine ROC-AUC.** The reported `ROC-AUC = 1.0000` under
   every mimicry strength is a hard-coded fallback
   (`getattr(m, 'roc_auc', 1.0 if m.f1 > 0 else 0.5)`), not a computed AUC.
   An independently computed continuous-score ROC-AUC is ≈0.95, not 1.0.
3. **"10-seed" statistics are single-seed.** `results/seed_statistics.md` reports
   `F1 = 0.7222 ± 0.0000`; the ± 0.0000 betrays that only seed 42 was aggregated.
4. **DARPA experiments ran on synthetic fallback.** `data/parsed/` is absent from
   a fresh clone; the DARPA runners fall back to synthetic graphs. The paper's
   "DARPA" tables are therefore not DARPA results.
5. **Mimicry is mis-specified.** The camouflage generator tags every noise edge
   with `attributes={"mimicry": True}` (a label leak) *and* creates
   type/timestamp-inconsistent edges that themselves violate the Rule Engine's
   invariants, manufacturing the reported precision collapse.

The corrected evaluation shows the **Rule Engine is the stronger detector**
(paired F1 difference +0.48, Wilcoxon p = 0.002) and is **invariant to benign
mimicry**, while GraphSAGE, once leakage is removed, drops to near-chance on
real provenance.

---

## 2. Repository Integrity

* `python3 -m pytest -q` → **98 passed, 5 failed**.
  All 5 failures are `tests/test_graph_loader.py` expecting `data/parsed/` files
  absent from the clone. Environmental, not a code defect.
* The repository ships **no manuscript PDF**; `results/*.md` and `README.md` are
  the only citable "paper values". The audit treats those as the paper values.
* Real data acquisition validated: the shipped CDM Avro parser
  (`src/graph_construction/cdm_parser.py`) exactly reproduces the documented
  counts for the two datasets that could be downloaded.

| Dataset | nodes | edges | skipped | parse time | documented match |
|---|---|---|---|---|---|
| Theia E3 scenario 3 | 20,157 | 297,777 | 0 | 33.7 s | exact |
| Theia E3 scenario 5m | 34,835 | 464,858 | 0 | 23.4 s | exact |

* Scenarios **1r** and **6r** could not be downloaded (Google Drive quota
  exhausted); recorded as an unresolved gap, not hidden.

---

## 3. Paper-to-Code Reconciliation

Machine-readable: `audit/final_result_reconciliation.csv`.

| Paper result | Current-code protocol | Match? | Root cause |
|---|---|---|---|
| Synthetic RE P=0.8125 R=0.6500 F1=0.7222 (seed 42) | `run_evaluation.py --attack-type all --seed 42` | YES (single seed) | exact at that protocol |
| Synthetic "multi-seed" P/R/F1 = 0.8125 ± 0.0000 | mean±std over 10 seeds | **NO** | std=0 → single seed reported as multi-seed |
| GraphSAGE F1=0.5600, ROC-AUC=0.8776, τ*=0.70 | `run_graphsage.py --epochs 30 --seed 42` | YES (leaky) | reproduced, but train+threshold on test |
| DARPA 1r/3/5m/6r | load `data/parsed/`, truncate 50k, inject 5×4 | **UNVERIFIABLE** | data absent → synthetic fallback |
| Mimicry none/light/medium/heavy | base poison + 0/30/70/150 % noise | YES (mis-specified) | noise leaks label & violates invariants |
| RE ROC-AUC = 1.0000 (all mimicry) | continuous ranking score | **NO** | hard-coded fallback constant |
| Ablation table | category + leave-one-out, seed 42 | YES (single seed) | single seed |
| Scalability 10k–1M | construct synthetic graph, time detection | PARTIAL | sizes match; timings hardware-dependent |

---

## 4. Original Reproduction Results

The repository's own numbers were reproduced at their own protocol **before** any
correction (labeled ORIGINAL-REPRODUCTION; logs under `audit/original_reproduction/`).

| Experiment (original protocol) | Reproduced | Note |
|---|---|---|
| Synthetic RE seed 42 F1 | 0.7222 | exact |
| Synthetic RE 10-seed F1 mean | 0.7921 | script supports 10 seeds |
| GraphSAGE seed 42 F1 (leaky) | 0.5600 | exact to 4 dp |
| Mimicry edge counts | 234/304/397/585 | exact |
| Scalability sizes | 10k…1M | shapes match |

Original reproduction **confirms the code produces the reported numbers**. The
problem is not reproducibility — it is that the reported numbers come from a
protocol that cannot support the claims.

---

## 5. GraphSAGE Leakage Findings

Full detail: `audit/graphsage_leakage_audit.md`.

| Question | Finding |
|---|---|
| training edges == evaluation edges? | **Yes** — `train_epoch` uses all `data` edges |
| threshold tuned on test labels? | **Yes** — `find_best_threshold(y_true, y_prob)` on the scored set |
| validation set exists? | **No** — `create_train_val_test_masks` never called |
| test set exists? | **No** — single `Data` object |
| structure leaks test info? | **Yes** — message passing over the poisoned scored graph |
| poisoning labels visible in training? | **Yes** — `data.edge_label` is the training target |
| threshold optimises the evaluation set? | **Yes** |

Effect on synthetic (same 10 seeds, same instances):

| Protocol | GraphSAGE F1 mean |
|---|---|
| Original (train + threshold on test) | 0.5600 |
| Corrected (train/VAL/test, threshold on VAL) | **0.3224** |

The leak inflated GraphSAGE F1 by ≈0.24 absolute.

---

## 6. Poisoning Ground-Truth Audit

Full detail: `audit/poisoning_ground_truth_audit.md`.

| Attack | Requested /10 seeds | Effective | Detectable | Undetectable | GT ids absent from final graph |
|---|---|---|---|---|---|
| deletion | 50 | 50 | 0 | 50 | 50 (by construction) |
| insertion | 50 | 49 | 49 | 0 | 0 |
| reordering | 50 | 50 | 50 | 0 | 0 |
| dependency_forgery | 50 | 50 | 50 | 0 | 0 |

Deleted edges never remain in the graph, so their GT ids can only be "detected"
by synthetic sequential-ID reconstruction rules (`SequenceGapRule`,
`UnspawnedProcessRule`) — a result that will **not transfer to real logs** with
non-sequential ids. The pristine `inject_poisoning` also aliases edge objects
(shallow copy), mutating the caller's "clean" graph for reordering/forgery; the
corrected `poisoning_v2` deep-copies and asserts integrity on every seed
(`integrity_problems = []`).

**Scoring-universe sensitivity** (`audit/raw_runs/gt_sensitivity.json`). The
corrected harness scores only edges present in the final graph; the repository's
evaluator adds absent GT ids to the universe and can "match" them via ID
reconstruction. Scoring the same detector both ways:

| Universe | F1 mean ± std | Precision | Recall | ROC-AUC |
|---|---|---|---|---|
| final graph only (corrected) | 0.8048 ± 0.0627 | 0.7146 | 0.9329 | 0.9528 |
| final ∪ absent GT ids (repo-style) | 0.8453 ± 0.0513 | 0.7700 | 0.9445 | 0.9583 |

The ~0.04 F1 gap is the entire benefit of scoring vanished deletion ids. The
corrected protocol does not grant it, because a deletion cannot be edge-matched
in the final graph and is reported separately.

---

## 7. DARPA Audit

Full detail: `audit/darpa_audit.md`.

* `data/parsed/` is gitignored and empty in a fresh clone; runners fall back to
  synthetic graphs. The committed "DARPA" tables are **synthetic**.
* Real Theia data now parsed (scenarios 3 and 5m). Following the repo's own
  `--max-edges 50000` default, the first 50,000 edges are taken and **then**
  poisoned.
* **A. real DARPA attack labels:** not available per edge for scenarios 3/5m;
  the E3 report gives only coarse time windows. No supervised AUC can be claimed.
* **B. synthetic post-collection poisoning** injected into real provenance:

| Dataset (real, 50k edges) | Detector | F1 mean ± std | ROC-AUC mean |
|---|---|---|---|
| theia3 | Rule Engine | 0.8347 ± 0.0459 | 0.8833 |
| theia3 | GraphSAGE | 0.0340 ± 0.1052 | 0.6609 |
| theia5m | Rule Engine | 0.8504 ± 0.0599 | 0.8833 |
| theia5m | GraphSAGE | 0.0099 ± 0.0093 | 0.6492 |

On **unmodified** real Theia graphs the Rule Engine flags only 19/50,000
(theia3, 0.038 %) and 7/50,000 (theia5m, 0.014 %) edges. These are **not**
detections of real DARPA attacks and must never be labelled as such.

**Event-count discrepancy (15 vs 20).** Each DARPA run injects 5 deletions +
5 insertions + 5 reorderings + 5 forgeries = **20 poisoning events**, but only
**15** produce an edge that exists in the final graph. The 5 deletions vanish,
so the evaluated positive set is 15; any table reporting "20 poison operations"
alongside a 15-positive denominator is internally inconsistent and is flagged in
`audit/poisoning_ground_truth_audit.md`.

---

## 8. Mimicry Audit

Full detail: `audit/mimicry_audit.md`.

The original generator leaks the attack condition twice: every noise edge carries
`attributes = {"mimicry": True}`, and noise edges use random type/endpoint/
timestamp combinations that **violate** the temporal invariants, so camouflage
itself creates Rule Engine violations and collapses precision.

Corrected camouflage (type-consistent, spawn-time respecting, monotone
timestamps, no label attribute) produces **zero self-violations**, and the Rule
Engine is essentially invariant to it:

| Strength | noise edges (mean) | noise self-violations | RE F1 mean ± std | RE ROC-AUC mean |
|---|---|---|---|---|
| none | 0 | 0 | 0.8048 ± 0.0627 | 0.9528 |
| light | 44.9 | 0 | 0.8048 ± 0.0627 | 0.9558 |
| medium | 89.9 | 0 | 0.8048 ± 0.0627 | 0.9577 |
| heavy | 178.9 | 0 | 0.8048 ± 0.0627 | 0.9599 |

GraphSAGE (leakage-free) stays weak at all strengths (F1 0.30–0.54). The paper's
"Rule Engine collapses under mimicry" claim is an artifact of the implementation,
not a property of the detector.

For completeness: when the *original, mis-specified* camouflage is used, even the
honest continuous score degrades (violation-count ROC-AUC ≈ 0.85 → 0.54 from
none → heavy; see `audit/rule_engine_roc_audit.md`). That degradation is caused by
the camouflage edges violating the temporal invariants, i.e. it measures the
generator, not detector robustness. With invariant-preserving camouflage the same
score stays ≈ 0.95–0.96.

---

## 9. Ablation Audit

Full detail: `audit/ablation_audit.md`. 10 seeds, mean ± std.

| Variant | F1 mean ± std | ROC-AUC mean ± std |
|---|---|---|
| all rules | 0.8048 ± 0.0627 | 0.9528 ± 0.0312 |
| without structural | **0.3285 ± 0.0731** | 0.6203 |
| without temporal | 0.7983 ± 0.0055 | 0.8321 |
| without semantic | 0.8048 ± 0.0627 | 0.9528 |
| LOO ReadWriteConsistencyRule | **0.5173 ± 0.1136** | 0.7325 |
| LOO NetworkConsistencyRule | 0.7455 ± 0.0844 | 0.8983 |
| LOO SpawnConsistencyRule | 0.7417 ± 0.0903 | 0.8952 |
| LOO SequenceMonotonicityRule | 0.7802 ± 0.0863 | 0.8599 |
| LOO others | no measurable change | — |

**Structural rules carry almost all detection power**; the **semantic rule
(`UnspawnedProcessRule`) contributes nothing** on the synthetic benchmark;
temporal rules contribute little to F1. No single-seed claim is made.

---

## 10. Scalability Audit

Full detail: `audit/raw_runs/scalability/`, `audit/journal_ready_tables/table6_scalability.*`,
plot `audit/plots/scalability_corrected.png`. Methodology is clean: each phase
timed separately; GraphSAGE **training** is never compared against Rule Engine
**inference**. Five independent repetitions per size (10k, 25k, 50k, 100k, 250k,
500k, 1M edges).

| edges | construction (s) | poisoning (s) | RE inference (s) | end-to-end (s) | peak Python (MB) | throughput (edges/s) |
|---|---|---|---|---|---|---|
| 10,000 | 0.181 | 1.002 | 0.366 | 1.549 | 36.9 | 28,088 |
| 25,000 | 0.556 | 2.946 | 1.142 | 4.643 | 24.9 | 22,297 |
| 50,000 | 1.098 | 5.434 | 2.076 | 8.608 | 49.4 | 24,368 |
| 100,000 | 2.079 | 10.969 | 3.154 | 16.202 | 98.1 | 31,709 |
| 250,000 | 5.224 | 31.804 | 7.914 | 44.942 | 244.1 | 31,596 |
| 500,000 | 10.930 | 64.677 | 17.109 | 92.716 | 486.6 | 29,225 |
| 1,000,000 | 21.207 | 131.485 | 34.480 | 187.171 | 971.4 | 29,007 |

Both construction and Rule Engine inference are linear in edge count (RE
inference ≈ 3.4 × 10⁻⁵ s/edge, peak Python ≈ 1 KB/edge). Throughput is stable at
≈ 2.2–3.2 × 10⁴ edges/s across three orders of magnitude — no super-linear
blow-up. Poisoning is the dominant cost (≈ 60 % of end-to-end) because the
corrected injector deep-copies and integrity-checks every event; the original
injector is faster but mutates its input. GraphSAGE training is not included in
this table and is reported separately (it is orders of magnitude slower per edge).

---

## 11. Multi-Seed Statistics

10 seeds: `[1, 7, 13, 21, 42, 99, 123, 256, 512, 1024]`, fresh attack instances
per seed, leakage-free GraphSAGE. Full table:
`audit/journal_ready_tables/table7_multiseed.*`.

| Metric | Rule Engine mean ± std | GraphSAGE mean ± std |
|---|---|---|
| Precision | 0.7146 ± 0.0948 | 0.3416 ± 0.3093 |
| Recall | 0.9329 ± 0.0629 | 0.5017 ± 0.3637 |
| F1 | 0.8048 ± 0.0627 | 0.3224 ± 0.1942 |
| Accuracy | 0.9614 ± 0.0155 | 0.8514 ± 0.0756 |
| Balanced accuracy | 0.9484 ± 0.0304 | 0.6949 ± 0.1428 |
| MCC | 0.7954 ± 0.0642 | 0.3121 ± 0.1985 |
| FPR | 0.0360 ± 0.0174 | 0.1119 ± 0.1095 |
| Specificity | 0.9640 ± 0.0174 | 0.8881 ± 0.1095 |
| ROC-AUC | 0.9528 ± 0.0312 | 0.8289 ± 0.1595 |
| PR-AUC | 0.7403 ± 0.0796 | 0.5909 ± 0.2445 |

95 % CIs (t, df = 9) are in the table artifact.

### 11b. Cross-dataset generalization

Table `audit/journal_ready_tables/table9_generalization.*`, 5 seeds per pair.

| source → target | Rule Engine F1 mean ± std | GraphSAGE (target-trained) F1 mean ± std |
|---|---|---|
| synthetic → theia3 | 0.8566 ± 0.0289 | 0.0103 ± 0.0149 |
| theia3 → theia5m | 0.8369 ± 0.0206 | 0.0347 ± 0.0280 |
| theia5m → theia3 | 0.8566 ± 0.0289 | 0.0103 ± 0.0149 |

The Rule Engine transfers cleanly to unseen real provenance with **no
retraining** (fixed invariants). GraphSAGE is near-chance on real graphs. Caveat:
**no shared-feature cross-graph GraphSAGE transfer is implemented in the
repository**, so the GraphSAGE column is a target-trained model, not a genuine
transfer; this is flagged as remaining work, not reported as generalization.

---

## 12. Statistical Significance

Paired, same test instances, 10 seeds. Full table:
`audit/journal_ready_tables/table8_significance.*`.

| Comparison | mean diff | 95 % CI | Cohen's d_z | Wilcoxon p |
|---|---|---|---|---|
| RuleEngine − GraphSAGE, F1 | **+0.4824** | [0.3285, 0.6363] | 2.24 | **0.0020** |
| RuleEngine − GraphSAGE, ROC-AUC | +0.1239 | [−0.0309, 0.2787] | 0.71 | 0.1055 |

The Rule Engine's F1 advantage is statistically significant and large. Its
ROC-AUC advantage is **not** significant (CI includes 0) — the correct claim is
"comparable ranking quality, significantly better operating-point F1", not
"superior AUC".

---

## 13. Reproducible Results

* Synthetic seed-42 Rule Engine P/R/F1/Acc — exact.
* GraphSAGE seed-42 numbers *under the original leaky protocol* — exact.
* Mimicry edge counts (234/304/397/585) — exact.
* Ablation and rule-statistics tables under the original single-seed protocol — exact.
* Real Theia parse counts — exact vs `docs/dataset_statistics.md`.
* Rule Engine genuine continuous-score ROC-AUC ≈ 0.95 (10-seed mean 0.9528).

## 14. Non-Reproducible Results

* "10-seed" statistics — committed values are single-seed.
* Rule Engine ROC-AUC = 1.0000 — not a computed quantity.
* GraphSAGE F1 = 0.5600 as a generalisation estimate — leaky.
* DARPA cross-scenario tables as *real* DARPA detection — synthetic fallback.
* Mimicry precision collapse as a Rule Engine property — generator artifact.

## 15. Methodological Problems

1. No train/validation/test separation; threshold on test.
2. Hard-coded ROC-AUC fallback in the robustness path.
3. Single seed presented with `std = 0.0000`.
4. Silent synthetic fallback for missing DARPA data.
5. Silent 50k-edge truncation of DARPA graphs.
6. Mimicry noise leaks the attack condition via attributes.
7. Mimicry noise violates the very invariants being tested.
8. `inject_poisoning` aliases edge objects, mutating the clean graph.
9. Deletion detection relies on synthetic sequential edge IDs (no real-log transfer).
10. Scalability compared Rule Engine inference against GraphSAGE training.

## 16. Recommended Experimental Protocol

1. Partition **instances** (disjoint poisoned graphs) into train/val/test; also
   hold out base topologies for generalisation.
2. Select thresholds on validation only. Never touch test labels.
3. Report multi-seed mean ± std and 95 % CI; paired tests against the baseline.
4. Compute ROC-AUC/PR-AUC only from genuine continuous scores; otherwise report
   "unavailable".
5. Label DARPA results as **synthetic post-collection poisoning on real
   provenance**; never as real DARPA ground truth.
6. Record truncation explicitly in every reported table.
7. Camouflage must be label-free and invariant-preserving.
8. Separate training time from inference time in scalability tables.

## 17. Exact Numbers Safe to Put in a Journal

* Real Theia parse counts (20,157/297,777; 34,835/464,858) — with truncation noted.
* Rule Engine 10-seed F1 = 0.8048 ± 0.0627, ROC-AUC = 0.9528 ± 0.0312 on synthetic.
* Rule Engine mimicry-invariance (F1 unchanged none→heavy; 0 self-violations).
* Paired RuleEngine−GraphSAGE F1 diff = +0.4824, p = 0.0020.
* Ablation: structural rules dominate; semantic rule contributes 0 on synthetic.

## 18. Numbers That Must NOT Be Used

* Any GraphSAGE F1/ROC-AUC from `results/` (leaky protocol).
* Rule Engine ROC-AUC = 1.0000.
* "Multi-seed" ± 0.0000 values.
* DARPA table values as real DARPA detection.
* Mimicry precision/F1 collapse values.
* Any single-seed claim presented as general.
* Any scalability comparison of Rule Engine inference vs GraphSAGE training.

---

## A. Results reproduced exactly
Synthetic seed-42 Rule Engine P/R/F1; GraphSAGE seed-42 under the original
protocol; mimicry edge counts; ablation/rule-statistics under the single-seed
protocol; real Theia parse counts.

## B. Results reproduced approximately
Scalability sizes and asymptotics (timings hardware-dependent); 10-seed Rule
Engine F1 (0.7921 original protocol vs 0.7222 committed).

## C. Results not reproducible
"10-seed" statistics (single seed); DARPA cross-scenario tables (synthetic
fallback); Rule Engine ROC-AUC = 1.0000.

## D. Results invalid under rigorous evaluation
GraphSAGE comparative numbers (leakage); mimicry robustness collapse
(mis-specified camouflage); any claimed real-DARPA detection.

## E. Corrected journal-safe results
Rule Engine synthetic 10-seed F1 0.8048 ± 0.0627, ROC-AUC 0.9528 ± 0.0312;
mimicry-invariant; paired F1 advantage over GraphSAGE +0.4824 (p = 0.0020);
structural rules dominant (ablation); near-zero flag rate on unmodified real
Theia provenance.

## F. Remaining experiments required before journal submission
1. Download and parse scenarios **1r** and **6r** (Drive quota blocked).
2. Obtain genuine per-edge DARPA attack labels for a real detection claim.
3. Topology-held-out generalisation (unseen base graphs/scenarios).
4. A true cross-graph GraphSAGE transfer (shared feature space), currently absent.
5. Deletion-detection protocol that does not depend on synthetic edge-ID schemes.
6. Larger-scale GraphSAGE scalability with training/inference separated.
