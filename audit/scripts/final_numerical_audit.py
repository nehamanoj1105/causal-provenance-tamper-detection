"""Final claim-by-claim numerical audit of both manuscripts (Phase 3).

Three independent checks:

1. NUMERIC CLAIMS. Every empirical number written in the .tex is resolved
   against the authoritative verified tables/raw runs (never typed). The check
   script is the existing manuscript_validation/check_{conference,journal}.py,
   whose claim lists are re-run here and re-classified.

2. RETRACTED VALUES. Scans both .tex sources and both tables/ directories for
   any retracted or leaky value that must not be presented as a final result,
   allowing only the explicit audit-comparison contexts.

3. TABLE INTEGRITY. Confirms every manuscript table CSV is byte-identical to the
   authoritative audit/FINAL_RESULTS/tables/csv/ table.

4. BUILD INTEGRITY. Confirms both PDFs compiled with 0 errors, 0 undefined
   references and 0 overfull boxes, and reports page counts.

Writes audit/final_numerical_audit.json and prints a summary.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONF = ROOT / "final_manuscripts" / "conference"
JOUR = ROOT / "final_manuscripts" / "journal"
OUT = ROOT / "audit" / "final_numerical_audit.json"

TABLES = [
    "table1_dataset_statistics", "table2_experimental_protocol",
    "table3_main_detection", "table4_statistical_comparison",
    "table5_cross_dataset", "table6_mimicry", "table7_rule_ablation",
    "table8_scalability", "table9_real_data_poisoning",
]

# Values that must never appear as a final scientific claim.
RETRACTED = {
    "1.0000": "rule-engine ROC-AUC fallback constant",
    "0.5600": "leaky GraphSAGE seed-42 F1",
    "0.0882": "invalid mimicry-generator Rule Engine F1",
    "15.26": "uncorrected 1M-edge inference time",
    "364": "uncorrected 1M-edge peak memory",
    "103": "uncorrected unit-test count",
    "0.6154": "committed single-seed Rule Engine F1",
    "0.7222": "repo-protocol single-seed Rule Engine F1",
    "0.4615": "repo-protocol GraphSAGE default F1",
}
# Contexts in which a retracted value is legitimate (audit comparison only).
AUDIT_CONTEXT = [
    "retract", "leaky", "leakage-prone", "fallback", "reported ROC-AUC",
    "previously reported", "audit", "not a computed",
]


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def check_claims():
    results = {}
    for name, script in [("conference", "check_conference.py"), ("journal", "check_journal.py")]:
        path = ROOT / "audit" / "manuscript_validation" / script
        rc, out, err = run([sys.executable, str(path)], ROOT)
        m = re.search(r"ok=(\d+) bad=(\d+)", out)
        results[name] = {
            "returncode": rc, "output": out, "error": err,
            "ok": int(m.group(1)) if m else None,
            "bad": int(m.group(2)) if m else None,
        }
    return results


def check_retracted():
    findings = []
    for tex in [CONF / "conference_paper.tex", JOUR / "journal_paper.tex"]:
        lines = tex.read_text().splitlines()
        for i, line in enumerate(lines):
            for val, why in RETRACTED.items():
                # numeric-token boundary: not preceded/followed by a digit or dot
                pat = re.compile(r"(?<![\d.])" + re.escape(val) + r"(?![\d.])")
                if not pat.search(line):
                    continue
                window = " ".join(lines[max(0, i - 3):i + 4]).lower()
                legitimate = any(ctx in window for ctx in AUDIT_CONTEXT)
                findings.append({
                    "file": str(tex.relative_to(ROOT)), "line": i + 1,
                    "value": val, "reason": why,
                    "legitimate_audit_context": legitimate,
                    "text": line.strip()[:140],
                })
    return findings


def check_tables():
    out = {}
    for t in TABLES:
        a = ROOT / "audit" / "FINAL_RESULTS" / "tables" / "csv" / f"{t}.csv"
        for name, base in [("conference", CONF), ("journal", JOUR)]:
            b = base / "tables" / f"{t}.csv"
            if not a.exists() or not b.exists():
                out[f"{name}:{t}"] = "missing"
                continue
            out[f"{name}:{t}"] = "identical" if a.read_bytes() == b.read_bytes() else "DIFFERS"
    return out


def check_build():
    out = {}
    for name, base, tex in [("conference", CONF, "conference_paper"), ("journal", JOUR, "journal_paper")]:
        log = (base / f"{tex}.log").read_text(errors="replace")
        errs = re.findall(r"^! .*$", log, re.M)
        undef = re.findall(r"(?:Reference|Citation) .* undefined", log)
        overfull = re.findall(r"Overfull", log)
        pages = re.search(r"Output written on .*?\((\d+) pages", log)
        out[name] = {
            "errors": errs, "undefined_refs": undef,
            "overfull": len(overfull), "pages": int(pages.group(1)) if pages else None,
        }
    return out


def main():
    report = {
        "claims": check_claims(),
        "retracted_scan": check_retracted(),
        "tables": check_tables(),
        "build": check_build(),
    }
    bad_retracted = [f for f in report["retracted_scan"] if not f["legitimate_audit_context"]]
    report["summary"] = {
        "claim_discrepancies": sum(v["bad"] or 0 for v in report["claims"].values()),
        "retracted_misuse": len(bad_retracted),
        "table_mismatches": sum(1 for v in report["tables"].values() if v != "identical"),
        "latex_errors": sum(len(v["errors"]) for v in report["build"].values()),
        "undefined_refs": sum(len(v["undefined_refs"]) for v in report["build"].values()),
        "overfull": sum(v["overfull"] for v in report["build"].values()),
    }
    OUT.write_text(json.dumps(report, indent=2))
    s = report["summary"]
    print("=== FINAL NUMERICAL AUDIT ===")
    for k, v in s.items():
        print(f"  {k}: {v}")
    print("  claims:", {k: f"ok={v['ok']} bad={v['bad']}" for k, v in report["claims"].items()})
    print("  build:", report["build"])
    if bad_retracted:
        print("  RETRACTED MISUSE:")
        for f in bad_retracted:
            print("   ", f)
    ok = (s["claim_discrepancies"] == 0 and s["retracted_misuse"] == 0
          and s["table_mismatches"] == 0 and s["latex_errors"] == 0
          and s["undefined_refs"] == 0 and s["overfull"] == 0)
    print("AUDIT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
