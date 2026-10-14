# Run report: RUN-008

> Generated automatically by `rb_task/tools/run_report.py` from the run directory. Facts only; interpretation is in the last section.

## 1. Overview

| field | value |
|---|---|
| run id | `rc-20261013-131020-9b9601` |
| final status | done (29/29 stage executions done, 0 failed, degraded=False) |
| generated | 2026-10-14T04:23:56+00:00 |
| total stage time | 15.16 h |
| topic | Improving graph neural networks for relational deep learning on RelBench: architecture and feature-encoding modifications of the official GraphSAGE baseline on rel-f1 driver-top3 (binary classification) |
| llm | qwen3.6-35b |
| experiment | mode=sandbox, time_budget_sec=1800, max_iterations=300, metric=primary_metric (maximize) |
| checkpoint | {"last_completed_stage": 23, "last_completed_name": "CITATION_VERIFY", "run_id": "rc-20261013-131020-9b9601", "timestamp": "2026-10-14T04:23:54+00:00"} |

Pipeline decisions after the analysis: [('refine', 'ITERATIVE_REFINE'), ('refine', 'ITERATIVE_REFINE')]

### Stage durations

| stage | status | seconds |
|---|---|---|
| stage-01 | done | 19 |
| stage-02 | done | 24 |
| stage-03 | done | 17 |
| stage-04 | done | 126 |
| stage-05 | done | 62 |
| stage-06 | done | 285 |
| stage-07 | done | 24 |
| stage-08 | done | 88 |
| stage-09 | done | 35 |
| stage-10 | done | 0 |
| stage-11 | done | 17 |
| stage-12 | done | 110 |
| stage-13 | done | 15059 |
| stage-13_v1 | done | 20785 |
| stage-13_v2 | done | 16354 |
| stage-14 | done | 288 |
| stage-14_v1 | done | 215 |
| stage-14_v2 | done | 177 |
| stage-15 | done | 12 |
| stage-15_v1 | done | 11 |
| stage-15_v2 | done | 13 |
| stage-16 | done | 29 |
| stage-17 | done | 563 |
| stage-18 | done | 28 |
| stage-19 | done | 115 |
| stage-20 | done | 14 |
| stage-21 | done | 18 |
| stage-22 | done | 76 |
| stage-23 | done | 15 |

## 2. Reference evaluation (stage 12)

status=completed, elapsed=108 s, peak GPU memory 3.4947 GB

| condition | seeds | val ROC-AUC | test ROC-AUC |
|---|---|---|---|
| baseline_graphsage | 10 | 0.6970 ± 0.0551 | 0.7631 ± 0.0352 |
| baseline_tuned | 10 | 0.7664 ± 0.0201 | 0.7935 ± 0.0160 |
| proposed | 10 | 0.7677 ± 0.0187 | 0.7911 ± 0.0295 |

primary_metric (selection metric) = 0.7677

## 3. Iterative refinement (stage 13)

### stage-13_v1  (mode: code; generated 2026-10-13T13:23:51+00:00)

baseline_metric=0.7677, best_metric=0.8787 (experiment_v19/), stop_reason=no_improvement_for_2_iterations, iterations=151

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | 0.7323 | False | 0 | 110 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 2 | 0.7569 | False | 0 | 110 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 3 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 4 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 5 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_lightrdl_model] |
| 6 | 0.7399 | False | 0 | 110 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 7 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 8 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 9 | 0.7391 | False | 0 | 133 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 10 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 11 | 0.8315 | True | 0 | 114 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [re-check seeds+200: 0.8295 / 0.8334] [proposed seeds=10] |
| 12 | 0.6779 | False | 0 | 114 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 13 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 14 | 0.8252 | False | 0 | 113 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 15 | 0.7679 | False | 0 | 110 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 16 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 17 | 0.8295 | False | 0 | 114 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 18 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 19 | 0.8787 | True | 0 | 115 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [re-check seeds+200: 0.8804 / 0.8771] [proposed seeds=10] |
| 20 | 0.8664 | False | 0 | 116 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 21 | 0.8827 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 22 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 23 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 24 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 25 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 26 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 27 | 0.7621 | False | 0 | 112 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 28 | 0.8766 | False | 0 | 116 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 29 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 30 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 31 | 0.8836 | False | 0 | 118 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 32 | 0.8573 | False | 0 | 125 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 33 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 34 | 0.8644 | False | 0 | 125 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 35 | 0.7494 | False | 0 | 114 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 36 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 37 | 0.6802 | False | 0 | 106 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 38 | 0.7242 | False | 0 | 112 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] (runtime-repaired) [proposed seeds=10] |
| 39 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 40 | n/a | False | 1 | 14 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model, vendor_relgnn_relgnn_nn] (runtime-repaired) |
| 41 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 42 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 43 | 0.8395 | False | 0 | 127 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 44 | 0.7312 | False | 0 | 111 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 45 | 0.7263 | False | 0 | 102 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 46 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 47 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 48 | 0.6845 | False | 0 | 117 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 49 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 50 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 51 | 0.6812 | False | 0 | 106 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 52 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 53 | 0.7431 | False | 0 | 133 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 54 | 0.7749 | False | 0 | 115 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 55 | 0.6801 | False | 0 | 123 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 56 | 0.7707 | False | 0 | 121 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 57 | 0.7389 | False | 0 | 113 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 58 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 59 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 60 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 61 | 0.7358 | False | 0 | 106 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 62 | 0.8064 | False | 0 | 117 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 63 | 0.7790 | False | 0 | 135 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 64 | 0.8003 | False | 0 | 105 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 65 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 66 | 0.7446 | False | 0 | 133 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 67 | 0.7497 | False | 0 | 105 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 68 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 69 | 0.6697 | False | 0 | 105 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 70 | 0.7639 | False | 0 | 105 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 71 | 0.7594 | False | 0 | 106 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 72 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 73 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 74 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 75 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 76 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 77 | 0.7584 | False | 0 | 107 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 78 | 0.7282 | False | 0 | 133 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 79 | 0.6797 | False | 0 | 104 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 80 | 0.6805 | False | 0 | 106 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 81 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 82 | n/a | False | 0 | 115 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2', 'K3'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 83 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 84 | n/a | False | 0 | 103 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** (runtime-repaired) [proposed seeds=10] |
| 85 | 0.6999 | False | 0 | 116 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 86 | 0.7717 | False | 0 | 106 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 87 | 0.7627 | False | 0 | 104 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 88 | 0.7506 | False | 0 | 112 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 89 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 90 | 0.7380 | False | 0 | 111 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 91 | 0.7319 | False | 0 | 111 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 92 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 93 | 0.7204 | False | 0 | 120 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 94 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 95 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 96 | 0.7456 | False | 0 | 112 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 97 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 98 | 0.7572 | False | 0 | 113 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 99 | 0.8090 | False | 0 | 145 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 100 | 0.7466 | False | 0 | 111 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 101 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 102 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 103 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 104 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 105 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 106 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] (runtime-repaired) |
| 107 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 108 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 109 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 110 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 111 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] |
| 112 | n/a | False | 0 | 103 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_model] **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 113 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 114 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 115 | n/a | False | 0 | 102 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_model] **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 116 | 0.7409 | False | 0 | 132 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 117 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 118 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_relgnn_model] (runtime-repaired) |
| 119 | 0.7288 | False | 0 | 103 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 120 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 121 | 0.7516 | False | 0 | 133 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 122 | n/a | False | 1 | 12 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 123 | 0.7654 | False | 0 | 105 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 124 | 0.7764 | False | 0 | 133 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 125 | 0.7585 | False | 0 | 122 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 126 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 127 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 128 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 129 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 130 | 0.7456 | False | 0 | 113 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 131 | 0.7493 | False | 0 | 133 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 132 | 0.7442 | False | 0 | 133 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 133 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 134 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 135 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 136 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 137 | n/a | False | 1 | 14 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] (runtime-repaired) |
| 138 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 139 | 0.7408 | False | 0 | 111 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 140 | 0.7562 | False | 0 | 134 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 141 | 0.6890 | False | 0 | 114 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 142 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 143 | 0.7612 | False | 0 | 112 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 144 | 0.7496 | False | 0 | 111 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 145 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 146 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 147 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 148 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 149 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 150 | 0.7521 | False | 0 | 114 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 151 | 0.7347 | False | 0 | 111 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.09789468026016379, 'se': 0.002945503287243509, 'ci95': [0.09305504291268746, 0.10366249484868578], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': -0.0015625000000000111, 'se': 0.010003112112313039, 'ci95': [-0.01990423808528432, 0.017091591110994942], 'p_signflip': 0.873046875, 'seeds_better': 4}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.1601118059163964, 'se': 0.017338543170480395, 'ci95': [0.12750326996470226, 0.19144205443371382], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.04074323265050166, 'se': 0.010779259976539403, 'ci95': [0.01952590993415545, 0.059791329170150474], 'p_signflip': 0.01171875, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.06221712565623261, 'se': 0.016278103516608734, 'ci95': [0.03220064145061006, 0.09188417157907931], 'p_signflip': 0.00390625, 'seeds_better': 9}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.04230573265050167, 'se': 0.010821794804831635, 'ci95': [0.021725331182065166, 0.06256764083403014], 'p_signflip': 0.0078125, 'seeds_better': 8}}}
### stage-13_v2  (mode: code; generated 2026-10-13T19:15:58+00:00)

baseline_metric=0.7677, best_metric=0.8836 (experiment_v0/), stop_reason=no_improvement_for_2_iterations, iterations=111

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 0 | 0.8836 | False | 0 | 118 | overrides `{"aggr": "sum", "dropout": 0.1, "gnn_type": "attention", "heads": 4, "norm": "graph_norm", "pre_norm": true, "residual": true}` (None) [proposed seeds=10] |
| 1 | 0.7507 | False | 0 | 110 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 2 | 0.6725 | False | 0 | 91 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_nn] (runtime-repaired) [proposed seeds=10] |
| 3 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 4 | 0.8810 | False | 0 | 118 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 5 | 0.8693 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 6 | 0.7453 | False | 0 | 132 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 7 | 0.7337 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 8 | 0.7532 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 9 | 0.8654 | False | 0 | 122 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 10 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 11 | 0.6897 | False | 0 | 105 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 12 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 13 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 14 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 15 | 0.8658 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 16 | n/a | False | 0 | 102 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 17 | 0.7597 | False | 0 | 110 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 18 | 0.8694 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 19 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 20 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 21 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 22 | 0.7423 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 23 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 24 | 0.8776 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 25 | 0.7770 | False | 0 | 110 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 26 | 0.7259 | False | 0 | 110 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 27 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 28 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 29 | n/a | False | 0 | 118 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2', 'K3'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 30 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 31 | 0.7356 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 32 | 0.7961 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 33 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 34 | 0.8859 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [re-check seeds+200: 0.8892 / 0.8826] [proposed seeds=10] |
| 35 | 0.8822 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 36 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 37 | 0.8822 | False | 0 | 115 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 38 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 39 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 40 | 0.7580 | False | 0 | 134 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 41 | 0.7160 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 42 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 43 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 44 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 45 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 46 | 0.8847 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 47 | 0.7454 | False | 0 | 132 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 48 | 0.8845 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 49 | 0.8847 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 50 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 51 | 0.8822 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 52 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 53 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 54 | 0.8672 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 55 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 56 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 57 | 0.8056 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 58 | n/a | False | 1 | 2 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 59 | 0.8728 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 60 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 61 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 62 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 63 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 64 | 0.7566 | False | 0 | 110 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 65 | 0.8827 | False | 0 | 118 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 66 | 0.8825 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 67 | 0.8735 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 68 | 0.8007 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 69 | 0.8519 | False | 0 | 127 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 70 | 0.8125 | False | 0 | 120 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 71 | n/a | False | 0 | 118 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2', 'K3'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 72 | 0.8799 | False | 0 | 118 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 73 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 74 | 0.8844 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 75 | 0.8687 | False | 0 | 122 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 76 | 0.7336 | False | 0 | 112 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 77 | 0.7275 | False | 0 | 113 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 78 | n/a | False | 1 | 2 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 79 | 0.7544 | False | 0 | 133 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] (runtime-repaired) [proposed seeds=10] |
| 80 | 0.8764 | False | 0 | 120 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 81 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 82 | 0.8677 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 83 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 84 | 0.7315 | False | 0 | 133 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 85 | 0.8505 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 86 | 0.8183 | False | 0 | 115 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 87 | 0.8789 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 88 | 0.8733 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 89 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 90 | 0.7462 | False | 0 | 110 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 91 | n/a | False | 1 | 2 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 92 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 93 | 0.7627 | False | 0 | 115 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 94 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 95 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 96 | n/a | False | 1 | 12 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 97 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 98 | 0.7769 | False | 0 | 120 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model, vendor_relgnn_relgnn_nn] (runtime-repaired) [proposed seeds=10] |
| 99 | 0.8753 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 100 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 101 | n/a | False | 1 | 2 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 102 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 103 | 0.8804 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 104 | 0.8712 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 105 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 106 | n/a | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2', 'K3'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 107 | n/a | False | 0 | 102 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 108 | 0.8719 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 109 | 0.8843 | False | 0 | 117 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 110 | 0.8764 | False | 0 | 116 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.09745211517442803, 'se': 0.008164010419240302, 'ci95': [0.0809875293400943, 0.11109826019960233], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': -0.07252038043478261, 'se': 0.03189753004008971, 'ci95': [-0.13634347564799323, -0.018122746394230786], 'p_signflip': 0.0546875, 'seeds_better': 4}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.15723154933615238, 'se': 0.01610073191329845, 'ci95': [0.12781702979699341, 0.18775288473598392], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': -0.03533327236622073, 'se': 0.02916404212555176, 'ci95': [-0.09214840483904678, 0.015406400240384536], 'p_signflip': 0.26171875, 'seeds_better': 5}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.05977943416172434, 'se': 0.0177818172359195, 'ci95': [0.026566044328179005, 0.09207566608733037], 'p_signflip': 0.01953125, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.03718710806856187, 'se': 0.010831195086508398, 'ci95': [0.01770026063440632, 0.058833710022993334], 'p_signflip': 0.00390625, 'seeds_better': 9}}}
### stage-13  (mode: code; generated 2026-10-13T23:52:39+00:00)

baseline_metric=0.7677, best_metric=0.8859 (experiment_v0/), stop_reason=no_improvement_for_2_iterations, iterations=106

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 0 | 0.8859 | False | 0 | 121 | overrides `{"aggr": "mean", "channels": 128, "dropout": 0.2, "gnn_type": "gatv2_stable", "heads": 4, "norm": "graph_norm", "num_layers": 2, "residual": true}` (None) [proposed seeds=10] |
| 1 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_model] |
| 2 | 0.7664 | False | 0 | 104 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 3 | 0.8875 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 4 | 0.8361 | False | 0 | 112 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 5 | 0.6664 | False | 0 | 91 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] (runtime-repaired) [proposed seeds=10] |
| 6 | 0.7438 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model, vendor_relgnn_relgnn_nn] [proposed seeds=10] |
| 7 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 8 | 0.8877 | False | 0 | 122 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 9 | 0.7573 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 10 | 0.7897 | False | 0 | 112 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 11 | 0.8877 | False | 0 | 122 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 12 | n/a | False | 1 | 12 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 13 | 0.7277 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 14 | 0.6624 | False | 0 | 131 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 15 | 0.8085 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 16 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 17 | 0.6725 | False | 0 | 90 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_nn] [proposed seeds=10] |
| 18 | 0.8136 | False | 0 | 123 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 19 | 0.6725 | False | 0 | 91 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_nn] [proposed seeds=10] |
| 20 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 21 | 0.6850 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 22 | 0.7826 | False | 0 | 120 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 23 | 0.8018 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 24 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 25 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 26 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 27 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_model] |
| 28 | 0.7365 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 29 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 30 | 0.7182 | False | 0 | 90 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 31 | 0.7841 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 32 | 0.7343 | False | 0 | 133 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 33 | 0.7297 | False | 0 | 113 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 34 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 35 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 36 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 37 | 0.8809 | False | 0 | 120 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 38 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 39 | n/a | False | 1 | 12 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 40 | 0.6971 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 41 | 0.8809 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 42 | 0.7890 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 43 | 0.7409 | False | 0 | 132 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 44 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 45 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 46 | 0.7390 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 47 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 48 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_model] |
| 49 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 50 | 0.6725 | False | 0 | 91 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_nn] [proposed seeds=10] |
| 51 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] (runtime-repaired) |
| 52 | 0.7721 | False | 0 | 104 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 53 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 54 | 0.7407 | False | 0 | 133 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 55 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 56 | 0.7495 | False | 0 | 110 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 57 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 58 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 59 | 0.7417 | False | 0 | 133 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 60 | n/a | False | 1 | 14 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] (runtime-repaired) |
| 61 | n/a | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2', 'K3'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 62 | n/a | False | 1 | 2 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 63 | 0.7418 | False | 0 | 133 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 64 | 0.7594 | False | 0 | 110 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 65 | n/a | False | 1 | 2 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 66 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 67 | n/a | False | 1 | 2 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 68 | 0.7320 | False | 0 | 133 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 69 | n/a | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2', 'K3'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 70 | n/a | False | 1 | 2 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 71 | 0.7586 | False | 0 | 105 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 72 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 73 | 0.8902 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 74 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 75 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 76 | 0.7536 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 77 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 78 | 0.8873 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 79 | 0.7726 | False | 0 | 135 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model, vendor_relgnn_relgnn_nn] [proposed seeds=10] |
| 80 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 81 | 0.7424 | False | 0 | 134 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 82 | 0.7017 | False | 0 | 107 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 83 | 0.7341 | False | 0 | 111 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] [proposed seeds=10] |
| 84 | 0.8881 | False | 0 | 122 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) [proposed seeds=10] |
| 85 | 0.8847 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 86 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 87 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 88 | 0.8848 | False | 0 | 122 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 89 | 0.8414 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 90 | 0.6660 | False | 0 | 90 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_nn] [proposed seeds=10] |
| 91 | 0.8860 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 92 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 93 | n/a | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2', 'K3'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 94 | 0.6882 | False | 0 | 91 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 95 | 0.8398 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 96 | 0.8886 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 97 | 0.8825 | False | 0 | 123 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 98 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_atomic_routes, vendor_relgnn_relgnn_model] |
| 99 | n/a | False | 1 | 11 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py (runtime-repaired) |
| 100 | 0.8584 | False | 0 | 122 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 101 | 0.8461 | False | 0 | 119 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 102 | 0.7032 | False | 0 | 91 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [official code: vendor_relgnn_relgnn_nn] [proposed seeds=10] |
| 103 | n/a | False | 0 | 0 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py |
| 104 | 0.8863 | False | 0 | 121 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |
| 105 | 0.8426 | False | 0 | 118 | files: vendor_relgnn_model.py, rb_model.py, vendor_relgnn_relgnn_hetero_conv.py, vendor_relgnn_relgnn_conv.py, vendor_relgnn_relgnn_nn.py, rb_model_official.py, vendor_relgnn_utils.py [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.10948200175592629, 'se': 0.0036167938711717303, 'ci95': [0.10277718550106613, 0.11620478041963059], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': -0.012317098662207315, 'se': 0.014529056035698021, 'ci95': [-0.041367742736203916, 0.012618167328595355], 'p_signflip': 0.43359375, 'seeds_better': 5}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.1692327677339593, 'se': 0.0168594266809459, 'ci95': [0.13720861478919932, 0.19980046496210419], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.022485106605351256, 'se': 0.009087043420422294, 'ci95': [0.005665858852424856, 0.03905438375313549], 'p_signflip': 0.041015625, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.05975076597803299, 'se': 0.01779106057722715, 'ci95': [0.02638388937664615, 0.09207170181505435], 'p_signflip': 0.021484375, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.034802205267558575, 'se': 0.009598756433128863, 'ci95': [0.016913082671404657, 0.0530454379180603], 'p_signflip': 0.0078125, 'seeds_better': 8}}}

### Confirmation on fresh seeds (stage-13_v1/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7171 ± 0.0569 | 0.7553 ± 0.0212 |
| baseline_tuned | 0.7793 ± 0.0097 | 0.7976 ± 0.0202 |
| proposed | 0.8772 ± 0.0067 | 0.7961 ± 0.0250 |

### Confirmation on fresh seeds (stage-13_v2/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7173 ± 0.0569 | 0.7551 ± 0.0208 |
| baseline_tuned | 0.7770 ± 0.0125 | 0.7923 ± 0.0204 |
| proposed | 0.8745 ± 0.0230 | 0.7198 ± 0.0916 |

### Confirmation on fresh seeds (stage-13/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7170 ± 0.0568 | 0.7549 ± 0.0208 |
| baseline_tuned | 0.7768 ± 0.0120 | 0.7897 ± 0.0202 |
| proposed | 0.8863 ± 0.0104 | 0.7773 ± 0.0327 |

## 4. Analysis, paper and checks

- quality report: score 5/10 — Major revisions required due to critical data inconsistencies and misrepresentation of empirical results.
- fabrication flags: suspected=False, verified values=417
- citations: 15/15 verified
- weaknesses: Critical inconsistency between reported results and the provided experiment summary JSON: the manuscript claims RAGN underperforms the tuned baseline on the tes; The core narrative and conclusion heavily rely on a test performance deficit that the ground truth data does not support, fundamentally misrepresenting the empi; Heavy reliance on numerous `vendor_` auxiliary files obscures the actual architectural contribution and complicates reproducibility, contradicting the '306 modi; The ablation study is mentioned but lacks detailed results or a component-wise breakdown in the provided text and tables.
- required_actions: Reconcile all reported metrics in the manuscript strictly with the provided experiment summary JSON. Update tables, text, and statistical claims to reflect the ; Revise the main conclusion and discussion to accurately reflect that the proposed model achieves comparable or slightly better test performance, rather than cla; Provide a complete ablation study table detailing the performance contribution of each architectural component (GATv2 attention, GraphNorm, residual connections; Clarify the dependency structure: either minimize external vendor files to isolate the core contribution or provide a fully self-contained, minimal reproducible
- paper PDF: `/tmp/claude-0/-home-claude/fb9a7f77-3423-597d-b557-18c3d9ac905a/scratchpad/run13/sesto_esperimento_relbench_f1_drivertop3_24h/stage-22/paper.pdf`
- paper length: 5010 words
- numbers (0.5–1.0, 3–4 decimals) in the paper: 10; **without a match among the run's aggregated results: 4** → ['0.7030', '0.7140', '0.7210', '0.999']
- seed counts claimed in the paper text: ['10']

<details><summary>abstract (as written by the pipeline)</summary>

Abstract  Relational deep learning on platforms like RelBench relies heavily on sum-aggregation GraphSAGE, a design that treats all neighbors equally and often suffers from optimization instability on sparse, imbalanced tasks. To address these limitations, we introduce RAGN (Residual Attention and GraphNorm Network), a streamlined heterogeneous graph neural network that replaces uniform aggregation with GATv2 edge-aware attention, integrates GraphNorm within the readout head for stable normalization, and employs residual connections to preserve gradient flow. Evaluated on the rel-f1 driver-top3 binary classification task, RAGN achieves a validation ROC-AUC of 0.8863, representing a +0.1095 absolute improvement over a rigorously tuned GraphSAGE baseline (p=0.002). On the test split, RAGN attains a ROC-AUC of 0.7773, matching the tuned baseline within statistical variance (p=0.434). These results demonstrate that architectural refinements significantly enhance validation generalization but yield marginal test gains over optimized training recipes. Our findings underscore that for sparse relational benchmarks, validation improvements do not always translate to test superiority, highlighting the critical primacy of training protocols over architectural complexity. This empirical investigation provides a transparent benchmark for future relational deep learning studies, establishing
</details>

## 5. Interpretation (to be written by a human)

- **What was done:** 
- **Results that can be trusted (and why):** 
- **What went wrong / limitations:** 
- **Decision / next step:** 

