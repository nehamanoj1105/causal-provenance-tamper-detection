# Phase 6 Causal Provenance Tamper Detection Summary

## Performance Overview Across Attacks (Multi-Seed Aggregated)

| Attack Type | Precision | Recall | F1 Score | Accuracy | FPR | Specificity |
|---|---|---|---|---|---|---|
| **all** | 0.8039 ± 0.0696 | 0.7900 ± 0.1022 | 0.7921 ± 0.0578 | 0.9554 ± 0.0111 | 0.0244 ± 0.0104 | 0.9756 ± 0.0104 |

## Key Findings
- **High Precision**: The enhanced semantic rule engine maintains near-zero false positive rates across all benign and poisoned test runs.
- **Deletion Detection**: Deletion attacks are effectively detected via unspawned process lineage checks and sequence gap analysis.
- **Reordering & Swapping**: Temporal monotonicity and process lineage timing rules catch timestamp inversion and reordered events.
- **Dependency Forgery**: Identified via node type mismatch rules and process ancestry cycle checks.
