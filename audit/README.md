# Audit workspace

Reproducibility audit for *Causal Consistency as a Defense: Detecting Provenance
Graph Poisoning* (`nehamanoj1105/causal-provenance-tamper-detection`).

## Result-set labels

Every number in this tree belongs to exactly one of:

| Label | Meaning |
|---|---|
| ORIGINAL-REPRODUCTION | repo protocol, unchanged |
| AUDITED-REPRODUCTION | repo protocol + integrity/ground-truth checks + real data |
| CORRECTED-EVALUATION | leakage-free, multi-seed, statistically rigorous |

## Layout

```
audit/
  final_audit_report.md            # main deliverable
  final_result_reconciliation.csv  # paper vs reproduced vs audited
  original_reproduction_report.md
  graphsage_leakage_audit.md
  poisoning_ground_truth_audit.md
  darpa_audit.md  mimicry_audit.md  ablation_audit.md
  rule_engine_roc_audit.md  statistics_audit.md  safety_check.md
  paper_protocol.md  repository_audit.md  DATASET_MANIFEST.md
  journal_ready_tables/            # Table 1..8 (csv + md + tex)
  plots/                           # ROC/PR + scalability figures
  raw_runs/                        # per-seed JSON/CSV (full precision)
    synthetic/ ablation/ darpa/ generalization/ scalability/
  experiments/                     # corrected harness + runners
  scripts/                         # report/table builders
  parsing/                         # real Theia parse manifests
  data/raw/theia/                  # parsed real Theia CSVs (gitignored)
```

## Reproduce

```bash
pip install -r requirements.txt fastavro pytest
python3 -m pytest -q                 # 98 pass / 5 fail (missing data/parsed)
python3 audit/experiments/run_all.py # all stages (resumable)
```

`run_all.py` never substitutes synthetic data for DARPA; if the real Theia CSVs
are absent it skips the DARPA stage with an explicit message.

## Key corrected-protocol entry points

| File | Purpose |
|---|---|
| `experiments/corrected/harness.py` | leakage-free GraphSAGE + continuous Rule Engine scoring |
| `experiments/corrected/metrics.py` | metrics + multi-seed summariser + paired tests |
| `experiments/poisoning/poisoning_v2.py` | immutable ground truth + integrity assertions |
| `experiments/mimicry/mimicry_v2.py` | label-free, invariant-preserving camouflage |
| `experiments/darpa/run_darpa.py` | real Theia + explicit real-vs-synthetic split |
