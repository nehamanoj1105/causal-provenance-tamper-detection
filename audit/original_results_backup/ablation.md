# Rule Engine Ablation Study Report

| Configuration | Active Rules | Precision | Recall | F1 Score | Accuracy | Runtime (s) |
|---|---|---|---|---|---|---|
| **ALL Rules Enabled** | 15 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0008 |
| **Without Structural Rules** | 9 | 0.7273 | 0.4000 | 0.5161 | 0.9185 | 0.0005 |
| **Without Temporal Rules** | 11 | 1.0000 | 0.5000 | 0.6667 | 0.9457 | 0.0005 |
| **Without Semantic Rules** | 10 | 0.7273 | 0.4000 | 0.5161 | 0.9185 | 0.0005 |
| **Without DuplicateEdgeRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
| **Without DuplicateEventRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
| **Without SelfLoopRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
| **Without MissingNodeRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
| **Without UnspawnedProcessRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
| **Without SequenceGapRule** | 14 | 0.7692 | 0.5000 | 0.6061 | 0.9293 | 0.0006 |
| **Without TimestampRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
| **Without ParentChildTemporalRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0006 |
| **Without ProcessActivityTemporalRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
| **Without SequenceMonotonicityRule** | 14 | 1.0000 | 0.5000 | 0.6667 | 0.9457 | 0.0006 |
| **Without SpawnConsistencyRule** | 14 | 0.7857 | 0.5500 | 0.6471 | 0.9348 | 0.0007 |
| **Without ExecutionConsistencyRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
| **Without ReadWriteConsistencyRule** | 14 | 0.7857 | 0.5500 | 0.6471 | 0.9348 | 0.0006 |
| **Without NetworkConsistencyRule** | 14 | 0.8000 | 0.6000 | 0.6857 | 0.9402 | 0.0007 |
| **Without DeleteConsistencyRule** | 14 | 0.8125 | 0.6500 | 0.7222 | 0.9457 | 0.0007 |
