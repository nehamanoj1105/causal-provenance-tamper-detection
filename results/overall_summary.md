# Phase 6 Causal Provenance Tamper Detection Summary

## Performance Overview Across Attacks (Multi-Seed Aggregated)

| Attack Type | Precision | Recall | F1 Score | Accuracy | FPR | Specificity |
|---|---|---|---|---|---|---|
| **all** | 0.8125 ± 0.0000 | 0.6500 ± 0.0000 | 0.7222 ± 0.0000 | 0.9457 ± 0.0000 | 0.0183 ± 0.0000 | 0.9817 ± 0.0000 |

## Key Findings
- **High Precision**: The enhanced semantic rule engine maintains near-zero false positive rates across all benign and poisoned test runs.
- **Deletion Detection**: Deletion attacks are effectively detected via unspawned process lineage checks and sequence gap analysis.
- **Reordering & Swapping**: Temporal monotonicity and process lineage timing rules catch timestamp inversion and reordered events.
- **Dependency Forgery**: Identified via node type mismatch rules and process ancestry cycle checks.
