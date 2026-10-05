## STUDY CONTEXT (authoritative)
The study improves the official RelBench v1.1.0 graph neural network (heterogeneous GraphSAGE with
PyTorch Frame encoders) on dataset `rel-f1`, task `driver-top3` (binary classification: will a driver
qualify in the top 3 within 30 days; metric ROC-AUC; temporal splits with validation from 2005-01-01
and test from 2010-01-01). Two conditions are compared over >= 3 seeds: `baseline_graphsage` (official
configuration) and `proposed` (iteratively modified GNN: number of layers, GNN operator, feature /
column encoders, forward pass, regularisation, optimisation). Protocol: model selection uses the
validation ROC-AUC only; the test ROC-AUC is computed once per trained model from the validation-selected
checkpoint and is reported, never used for selection. Report only numbers that appear in the
experiment results; do not claim state-of-the-art, and state clearly that rel-f1 is a small benchmark
(results can have high variance across seeds). Do not describe components that were not actually run.
