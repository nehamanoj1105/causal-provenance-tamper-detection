"""
Reproduce the corrected audit end-to-end.

Stages (each writes to audit/raw_runs/ and is resumable):
  1. synthetic   : 10-seed Rule Engine vs GraphSAGE (leakage-free)
  2. ablation    : rule-group + leave-one-rule-out, 10 seeds
  3. mimicry     : none/light/medium/heavy, invariant-preserving
  4. darpa       : real Theia 3 / 5m, 50k-edge cap, synthetic post-collection poisoning
  5. generalization : cross-source pairs
  6. scalability : 10k..1M, 5 reps
  7. reports     : tables + plots + reconciliation

Real DARPA raw files are required for stage 4; if absent the stage is skipped
with an explicit message (no silent synthetic fallback).

Usage: python3 audit/experiments/run_all.py [stage ...]
"""
import subprocess
import sys
from pathlib import Path

STAGES = ["synthetic", "ablation", "darpa", "generalization", "scalability", "reports"]
PY = sys.executable


def run(cmd):
    print(">>>", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=False)


def main(stages):
    if "synthetic" in stages:
        run([PY, "audit/experiments/synthetic/run_synthetic.py"])
    if "ablation" in stages:
        run([PY, "audit/experiments/ablation/run_ablation.py"])
    if "darpa" in stages:
        raw = Path("audit/data/raw/theia")
        if not (raw / "theia3_edges.csv").exists():
            print("SKIP darpa: real Theia CSVs not present at", raw, flush=True)
        else:
            run([PY, "audit/experiments/darpa/run_darpa.py", "theia3", "50000"])
            run([PY, "audit/experiments/darpa/run_darpa.py", "theia5m", "50000"])
    if "generalization" in stages:
        run([PY, "audit/experiments/generalization/run_generalization.py"])
    if "scalability" in stages:
        run([PY, "audit/experiments/scalability/run_scalability.py"])
    if "reports" in stages:
        run([PY, "audit/scripts/make_final.py"])


if __name__ == "__main__":
    main(sys.argv[1:] or STAGES)
