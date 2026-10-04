# Limitations

1. **Two datasets unavailable.** Theia E3 scenarios 1r and 6r could not be
   downloaded (Google Drive HTTP 403 quota). No results for them are reported or
   estimated. The real-data evaluation therefore covers scenarios 3 and 5m only.

2. **Real attacks are not evaluated.** The repository contains no real DARPA
   attack labels in a usable form. All "DARPA" detection numbers are real
   provenance graphs with **synthetic post-collection poisoning** injected. They
   must never be described as detection of naturally occurring attacks.

3. **Deleted edges are structurally undetectable under edge matching.** A deleted
   edge leaves no record in the final graph, so it cannot be assigned a false
   positive or true positive by edge-level matching. Five of the twenty injected
   events per seed are deletions; they are reported as undetectable and excluded
   from the scored positives. Aggregate detection quality on deletion is
   therefore not claimed.

4. **Scoring-universe sensitivity.** Reported F1 depends on whether absent
   deleted-edge ids are added to the universe (0.8048 corrected vs 0.8453
   repo-style). The paper uses the final-graph universe and states this.

5. **GraphSAGE cross-graph transfer is not implemented.** The generalization
   table reports a target-trained GraphSAGE, not a genuine transfer across a
   shared feature space; no cross-graph transfer claim is made.

6. **50k-edge cap on real data.** Real-Theia experiments use the first 50,000
   edges (silent truncation in the original loader). This cap is stated
   explicitly; it is not the full graph.

7. **Class imbalance on real graphs.** Positives are 15 out of 50,015 edges;
   precision is highly sensitive to even a few false positives.

8. **Original repository defects (documented, not used).** GraphSAGE
   train/test leakage; a fabricated Rule-Engine ROC-AUC fallback of 1.0;
   single-seed results reported as multi-seed; a mimicry generator whose noise
   both carries a `mimicry` attribute and violates the rule invariants. All are
   recorded in `audit/` and are excluded from the corrected results.
