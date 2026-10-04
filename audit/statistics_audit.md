# Multi-Seed Statistics and Statistical Validity (Phases 5, 12)

Source: `audit/raw_runs/corrected_multiseed.json`,
`audit/raw_runs/corrected_multiseed_per_seed.csv`.

## 1. Protocol

Per seed `s ∈ {1,7,13,21,42,99,123,256,512,1024}`:

```
base       = generate_synthetic_graph(seed=s)
train_inst = inject_poisoning(base, seed=f(s,1))
val_inst   = inject_poisoning(base, seed=f(s,2))   # threshold only
test_inst  = inject_poisoning(base, seed=f(s,3))   # reported metrics
```

- GraphSAGE weights ← train only; threshold ← validation only; metrics ← test.
- Rule Engine is deterministic; evaluated on the test instance.
- Both detectors see the **same** test instances, enabling paired tests.
- Rule Engine ROC/PR-AUC use the continuous violation-count score (Phase 6);
  GraphSAGE ROC/PR-AUC use sigmoid probabilities.

## 2. CORRECTED results — mean, sample std, median, min, max, 95% CI (n=10)

### Rule Engine (clean protocol)

| Metric | Mean | Std | Median | Min | Max | 95% CI |
|---|---|---|---|---|---|---|
| Precision | 0.3394 | 0.0465 | 0.3344 | 0.2647 | 0.4118 | [0.3106, 0.3682] |
| Recall | 0.7267 | 0.1063 | 0.7000 | 0.6000 | 0.9333 | [0.6608, 0.7926] |
| F1 | 0.4620 | 0.0621 | 0.4369 | 0.3673 | 0.5714 | [0.4235, 0.5005] |
| Accuracy | 0.8581 | 0.0190 | 0.8575 | 0.8268 | 0.8827 | [0.8463, 0.8699] |
| Balanced Accuracy | 0.7984 | 0.0556 | 0.7799 | 0.7238 | 0.9057 | [0.7639, 0.8328] |
| MCC | 0.4310 | 0.0775 | 0.3980 | 0.3162 | 0.5732 | [0.3829, 0.4790] |
| FPR | 0.1299 | 0.0163 | 0.1311 | 0.1037 | 0.1524 | [0.1198, 0.1400] |
| FNR | 0.2733 | 0.1063 | 0.3000 | 0.0667 | 0.4000 | [0.2074, 0.3392] |
| Specificity | 0.8701 | 0.0163 | 0.8689 | 0.8476 | 0.8963 | [0.8600, 0.8802] |
| ROC-AUC (count score) | 0.8046 | 0.0555 | 0.7839 | 0.7299 | 0.9122 | [0.7702, 0.8390] |
| PR-AUC (count score) | 0.3243 | 0.0725 | 0.3502 | 0.2237 | 0.4275 | [0.2794, 0.3693] |

### GraphSAGE (clean protocol)

| Metric | Mean | Std | Median | Min | Max | 95% CI |
|---|---|---|---|---|---|---|
| Precision | 0.2056 | 0.1006 | 0.1917 | 0.1094 | 0.4444 | [0.1432, 0.2679] |
| Recall | 0.4000 | 0.1257 | 0.4000 | 0.2000 | 0.6000 | [0.3221, 0.4779] |
| F1 | 0.2461 | 0.0580 | 0.2592 | 0.1772 | 0.3333 | [0.2101, 0.2820] |
| Accuracy | 0.7788 | 0.1033 | 0.7989 | 0.5978 | 0.9106 | [0.7148, 0.8428] |
| Balanced Accuracy | 0.6067 | 0.0438 | 0.6105 | 0.5573 | 0.6963 | [0.5795, 0.6339] |
| MCC | 0.1682 | 0.0796 | 0.1805 | 0.0689 | 0.2995 | [0.1189, 0.2176] |
| FPR | 0.1866 | 0.1210 | 0.1738 | 0.0305 | 0.3963 | [0.1116, 0.2616] |
| FNR | 0.6000 | 0.1257 | 0.6000 | 0.4000 | 0.8000 | [0.5221, 0.6779] |
| Specificity | 0.8134 | 0.1210 | 0.8262 | 0.6037 | 0.9695 | [0.7384, 0.8884] |
| ROC-AUC | 0.6634 | 0.0619 | 0.6590 | 0.5754 | 0.7453 | [0.6250, 0.7017] |
| PR-AUC | 0.2427 | 0.0547 | 0.2359 | 0.1738 | 0.3506 | [0.2088, 0.2766] |

### GraphSAGE — ORIGINAL leaky protocol (train + threshold on test)

| Metric | Mean | Std |
|---|---|---|
| Precision | 0.6021 | 0.1827 |
| Recall | 0.6133 | 0.0932 |
| F1 | 0.5876 | 0.0884 |
| Accuracy | 0.9246 | 0.0294 |
| ROC-AUC | 0.9113 | 0.0251 |
| PR-AUC | 0.5836 | 0.1065 |
| MCC | 0.5588 | 0.0991 |

The leaky protocol inflates GraphSAGE F1 from 0.2461 (clean) to 0.5876
(+0.3415 absolute), ROC-AUC from 0.6634 to 0.9113, and MCC from 0.1682 to
0.5588.

## 3. Paired statistical comparison (Rule Engine vs. GraphSAGE, same test instances)

Paired differences in F1 (Rule Engine − GraphSAGE), n = 10:

| Statistic | Value |
|---|---|
| Mean difference | 0.21593 |
| Std of differences | 0.09784 |
| 95% CI | [0.15529, 0.27658] |
| Wilcoxon signed-rank statistic | 0.0 |
| Wilcoxon p-value | 0.001953 |
| Paired t statistic | 6.979 |
| Paired t p-value | 6.47e-05 |
| Cohen's d_z | 2.207 |

Per-seed F1:

| Seed | Rule Engine | GraphSAGE (clean) | Difference |
|---|---|---|---|
| 1 | 0.4314 | 0.3333 | 0.0980 |
| 7 | 0.5333 | 0.1905 | 0.3429 |
| 13 | 0.4390 | 0.1875 | 0.2515 |
| 21 | 0.4898 | 0.2727 | 0.2171 |
| 42 | 0.4348 | 0.2456 | 0.1892 |
| 99 | 0.3673 | 0.2759 | 0.0915 |
| 123 | 0.4167 | 0.2857 | 0.1310 |
| 256 | 0.4255 | 0.1772 | 0.2483 |
| 512 | 0.5714 | 0.1818 | 0.3896 |
| 1024 | 0.5106 | 0.3103 | 0.2003 |

**Interpretation.** Under a clean protocol, the Rule Engine significantly
outperforms GraphSAGE in F1 (Wilcoxon p = 0.00195, Cohen's d_z = 2.21, all 10
paired differences positive). The effect is large but the absolute performance
of both detectors is modest: Rule Engine F1 ≈ 0.46, GraphSAGE F1 ≈ 0.25. The
paper's implied "near-perfect deterministic detection" is not supported once
train/test separation and honest thresholding are enforced.

**Caveat on the Rule Engine's apparent advantage.** The Rule Engine's precision
here (0.34) is far below its reported value because the corrected protocol
counts every flagged edge, including the many mimicry/insertion false positives,
against a small 20-event ground truth. This is an honest operating point, not a
tuned one.
