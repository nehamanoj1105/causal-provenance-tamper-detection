# Reproducibility

## Environment

| Component | Version |
|---|---|
| OS | Linux 6.8 (gke), x86-64 |
| Python | 3.13.15 |
| PyTorch | 2.14.1+cpu |
| PyTorch Geometric | 2.8.0.post1 |
| scikit-learn | 1.9.1 |
| NumPy | 2.5.3 |
| SciPy | 1.16.x |
| GPU | none (CPU-only) |
| RAM | 16.8 GB |

Install: `pip install -r requirements.txt` plus `scipy` and `matplotlib`.

## Determinism

The corrected pipeline is deterministic: re-running seeds 1, 42 and 1024 in
memory reproduces the stored raw runs bit-for-bit
(`audit/final_validation/independent_recheck.json`). GraphSAGE uses fixed seeds;
CPU execution avoids non-deterministic kernels.

## From raw results to the manuscript

```
audit/experiments/*            -> audit/raw_runs/*.json       (per-seed records)
audit/scripts/make_final.py    -> audit/journal_ready_tables/* (aggregation)
audit/scripts/final_validation.py -> audit/final_validation/*  (verification)
audit/scripts/build_final_results.py -> audit/FINAL_RESULTS/*
audit/scripts/gen_final_figures.py   -> audit/FINAL_RESULTS/figures/*
audit/scripts/make_manuscript_tables.py -> audit/FINAL_RESULTS/tables/*
```

## Verification

| Check | Result |
|---|---|
| Metric recomputation (tp/fp/tn/fn → metrics) | 1,890 cells, 0 mismatches |
| Number cross-check vs tables/report | 226 checks, 0 discrepancies |
| In-memory determinism (seeds 1/42/1024) | exact match |
| `python3 -m pytest -q` | 98 passed, 5 failed (missing `data/parsed`, environmental) |

## Notes

* Raw datasets are excluded from version control (size, safety). The manifests
  in `DATASET_SUMMARY.md` give source file ids and the parser path.
* The repository's original results are preserved unmodified in
  `audit/original_results_backup/`.
