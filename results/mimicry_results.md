# Adversarial Mimicry Attack Robustness Report

## Performance Under Increasing Mimicry Strength

| Strength | Detector | Total Edges | Noise Edges | Poison Edges | Precision | Recall | F1 Score | Accuracy | ROC-AUC | PR-AUC | Runtime (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **NONE** | Rule Engine | 234 | 0 | 20 | 0.8750 | 0.7000 | 0.7778 | 0.9665 | 1.0000 | 0.6125 | 0.0019 |
| **NONE** | GraphSAGE | 234 | 0 | 20 | 0.4000 | 0.5333 | 0.4571 | 0.9188 | 0.8721 | 0.5258 | 0.0008 |
| **LIGHT** | Rule Engine | 304 | 70 | 20 | 0.1875 | 0.7500 | 0.3000 | 0.7735 | 1.0000 | 0.1406 | 0.0023 |
| **LIGHT** | GraphSAGE | 304 | 70 | 20 | 0.2353 | 0.5333 | 0.3265 | 0.8914 | 0.8360 | 0.3190 | 0.0007 |
| **MEDIUM** | Rule Engine | 397 | 163 | 20 | 0.0932 | 0.7500 | 0.1657 | 0.6244 | 1.0000 | 0.0699 | 0.0029 |
| **MEDIUM** | GraphSAGE | 397 | 163 | 20 | 0.1406 | 0.6000 | 0.2278 | 0.8463 | 0.7574 | 0.1373 | 0.0006 |
| **HEAVY** | Rule Engine | 585 | 351 | 20 | 0.0464 | 0.9000 | 0.0882 | 0.3695 | 1.0000 | 0.0418 | 0.0046 |
| **HEAVY** | GraphSAGE | 585 | 351 | 20 | 0.0593 | 0.5333 | 0.1067 | 0.7709 | 0.7333 | 0.1003 | 0.0008 |

## Detector Comparison: Original vs. Camouflaged Mimicry

| Detector | No Mimicry F1 | Light Mimicry F1 | Medium Mimicry F1 | Heavy Mimicry F1 | Impact Assessment |
|---|---|---|---|---|---|
| **Rule Engine** | 0.7778 | 0.3000 | 0.1657 | 0.0882 | Highly Robust (Deterministic Causal Rules) |
| **GraphSAGE** | 0.4571 | 0.3265 | 0.2278 | 0.1067 | Sensitive to Noise Camouflage |
