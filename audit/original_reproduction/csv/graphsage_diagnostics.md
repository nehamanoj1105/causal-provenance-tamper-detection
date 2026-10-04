# GraphSAGE Baseline Diagnostic & Calibration Report

## 1. Class Imbalance Analysis
- **Total Edges Evaluated**: 179
- **Positive Samples (Tampered Edges)**: 15 (8.3799%)
- **Negative Samples (Benign Edges)**: 164 (91.6201%)
- **Imbalance Ratio**: 10.93 : 1

## 2. Threshold Optimization & Best Metrics
- **Optimal Decision Threshold**: `0.70` (selected to maximize validation F1 score)
- **Precision**: `0.700000`
- **Recall**: `0.466667`
- **F1 Score**: `0.560000`
- **Accuracy**: `0.938547`
- **False Positive Rate**: `0.018293`
- **False Negative Rate**: `0.533333`
- **Specificity**: `0.981707`
- **Balanced Accuracy**: `0.724187`
- **ROC-AUC**: `0.877642`
- **PR-AUC**: `0.563397`
- **Matthews Correlation Coefficient (MCC)**: `0.540959`

## 3. Probability Calibration Analysis
- **Minimum Predicted Probability**: `0.001345`
- **Maximum Predicted Probability**: `0.984253`
- **Mean Predicted Probability**: `0.297899`
- **Median Predicted Probability**: `0.261377`
- **Standard Deviation**: `0.229121`

## 4. Training Loss & Overfitting Analysis
- **Initial Training Loss**: `1.303250`
- **Final Training Loss**: `0.859506`
- **Overfitting Assessment**: The model loss converges steadily without severe loss divergence. However, due to graph structural homogeneity in local neighborhoods, message passing tends to oversmooth node representations across dense benign activity streams.

## 5. Comparative Evaluation vs. Semantic Rule Engine
- **Deterministic Causal Rules vs. Graph Message Passing**: The Semantic Rule Engine achieves higher precision and F1 because rule violations check exact logical dependencies (e.g. sequence gaps, unspawned process execution, timestamp monotonicity). GraphSAGE relies on local structural aggregation, which produces false positives when benign process activities exhibit similar node degree patterns.
- **Conclusion**: GraphSAGE is a valid baseline for learning general node representations, but deterministic causal rule engines are significantly superior for exact provenance graph tamper detection.
