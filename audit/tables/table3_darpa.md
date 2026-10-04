| dataset | eval_type | edges_loaded | graph_edges | truncated | real_flagged | real_flag_rate | f1_mean | f1_std | roc_auc_mean | roc_auc_std | n_seeds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theia3 | real_data_rule_behaviour | 50000 | 50000 | True | 19 | 0.00038 |  |  |  |  |  |
| theia3 | synthetic_post_collection::rule_engine |  |  |  |  |  | 0.8347438002610417 | 0.04585120864494653 | 0.8833309992997901 | 0.03600483528954418 | 10 |
| theia3 | synthetic_post_collection::graphsage |  |  |  |  |  | 0.03395927596881325 | 0.10519851057720425 | 0.6608880271431262 | 0.20496906053450054 | 10 |
| theia5m | real_data_rule_behaviour | 50000 | 50000 | True | 7 | 0.00014 |  |  |  |  |  |
| theia5m | synthetic_post_collection::rule_engine |  |  |  |  |  | 0.8503707403707403 | 0.05991943376964189 | 0.8833285318929013 | 0.03239143583511807 | 10 |
| theia5m | synthetic_post_collection::graphsage |  |  |  |  |  | 0.009855111005265805 | 0.00932094278035494 | 0.6491788368442517 | 0.3113305408240646 | 10 |