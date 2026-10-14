## STUDY CONTEXT (authoritative)
The study improves the official RelBench v1.1.0 graph neural network (heterogeneous GraphSAGE with
PyTorch Frame encoders) on dataset `{{DATASET}}`, task `{{TASK}}` ({{TASK_TYPE}}: {{TASK_DESC}};
metric {{METRIC}}; temporal splits: {{SPLITS}}). Two conditions are compared over >= 3 seeds: `baseline_graphsage` (official
configuration) and `proposed` (iteratively modified GNN: number of layers, GNN operator, feature /
column encoders, forward pass, regularisation, optimisation). Protocol: model selection uses the
validation {{METRIC}} only; the test {{METRIC}} is computed once per trained model from the validation-selected
checkpoint and is reported, never used for selection. Report only numbers that appear in the
experiment results; do not claim state-of-the-art, and state clearly that rel-f1 is a small benchmark
(results can have high variance across seeds). Do not describe components that were not actually run.
