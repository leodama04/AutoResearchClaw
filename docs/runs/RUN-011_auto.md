# Run report: RUN-011

> Generated automatically by `rb_task/tools/run_report.py` from the run directory. Facts only; interpretation is in the last section.

## 1. Overview

| field | value |
|---|---|
| run id | `rc-20261014-152719-4d33ce` |
| final status | done (29/29 stage executions done, 0 failed, degraded=False) |
| generated | 2026-10-15T14:59:01+00:00 |
| total stage time | 23.47 h |
| topic | Improving graph neural networks for relational deep learning on RelBench: architecture and feature-encoding modifications of the official GraphSAGE baseline on rel-f1 driver-dnf (binary classification) |
| llm | qwen3.6-35b |
| experiment | mode=sandbox, time_budget_sec=1800, max_iterations=300, metric=primary_metric (maximize) |
| checkpoint | {"last_completed_stage": 23, "last_completed_name": "CITATION_VERIFY", "run_id": "rc-20261014-152719-4d33ce", "timestamp": "2026-10-15T14:58:59+00:00"} |

Pipeline decisions after the analysis: [('refine', 'ITERATIVE_REFINE'), ('refine', 'ITERATIVE_REFINE')]

### Stage durations

| stage | status | seconds |
|---|---|---|
| stage-01 | done | 19 |
| stage-02 | done | 31 |
| stage-03 | done | 21 |
| stage-04 | done | 84 |
| stage-05 | done | 57 |
| stage-06 | done | 174 |
| stage-07 | done | 19 |
| stage-08 | done | 87 |
| stage-09 | done | 39 |
| stage-10 | done | 0 |
| stage-11 | done | 24 |
| stage-12 | done | 518 |
| stage-13 | done | 528 |
| stage-13_v1 | done | 80173 |
| stage-13_v2 | done | 1271 |
| stage-14 | done | 213 |
| stage-14_v1 | done | 227 |
| stage-14_v2 | done | 232 |
| stage-15 | done | 13 |
| stage-15_v1 | done | 12 |
| stage-15_v2 | done | 12 |
| stage-16 | done | 28 |
| stage-17 | done | 437 |
| stage-18 | done | 28 |
| stage-19 | done | 109 |
| stage-20 | done | 15 |
| stage-21 | done | 22 |
| stage-22 | done | 74 |
| stage-23 | done | 19 |

## 2. Reference evaluation (stage 12)

status=completed, elapsed=516 s, peak GPU memory 2.9661 GB

| condition | seeds | val ROC-AUC | test ROC-AUC |
|---|---|---|---|
| baseline_graphsage | 10 | 0.7130 ± 0.0083 | 0.7271 ± 0.0139 |
| baseline_tuned | 10 | 0.7618 ± 0.0238 | 0.7418 ± 0.0120 |
| proposed | 10 | 0.7687 ± 0.0177 | 0.7307 ± 0.0112 |

primary_metric (selection metric) = 0.7687

## 3. Iterative refinement (stage 13)

### stage-13_v1  (mode: code; generated 2026-10-14T15:45:14+00:00)

baseline_metric=0.7687, best_metric=0.8155 (experiment_v88/), stop_reason=no_improvement_for_2_iterations, iterations=206

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | 0.7016 | False | 0 | 546 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 2 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 3 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 4 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 5 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 6 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 7 | 0.6996 | False | 0 | 513 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 8 | 0.7022 | False | 0 | 507 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 9 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 10 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 11 | 0.7022 | False | 0 | 513 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 12 | 0.6952 | False | 0 | 522 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 13 | n/a | False | 1 | 34 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 14 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 15 | 0.7241 | False | 0 | 514 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 16 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 17 | 0.6803 | False | 0 | 513 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 18 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 19 | 0.7262 | False | 0 | 576 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 20 | n/a | False | 1 | 34 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 21 | n/a | False | 1 | 39 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 22 | 0.7362 | False | 0 | 527 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 23 | n/a | False | 1 | 205 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 24 | 0.7986 | True | 0 | 525 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [re-check seeds+200: 0.7969 / 0.8002] (runtime-repaired) [proposed seeds=10] |
| 25 | 0.8004 | False | 0 | 499 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 26 | 0.7959 | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 27 | 0.7278 | False | 0 | 525 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 28 | 0.6851 | False | 0 | 516 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 29 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 30 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 31 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 32 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 33 | 0.7975 | False | 0 | 529 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 34 | 0.8097 | True | 0 | 560 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [re-check seeds+200: 0.8060 / 0.8135] (runtime-repaired) [proposed seeds=10] |
| 35 | 0.8037 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 36 | 0.8064 | False | 0 | 532 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 37 | 0.8059 | False | 0 | 497 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 38 | 0.7584 | False | 0 | 529 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 39 | 0.7979 | False | 0 | 534 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 40 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 41 | 0.7987 | False | 0 | 537 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 42 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 43 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 44 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 45 | 0.8072 | False | 0 | 567 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 46 | 0.7250 | False | 0 | 528 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 47 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 48 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 49 | 0.8119 | False | 0 | 536 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 50 | 0.7896 | False | 0 | 534 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 51 | 0.8096 | False | 0 | 528 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 52 | n/a | False | 1 | 38 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 53 | 0.7940 | False | 0 | 536 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 54 | 0.8012 | False | 0 | 496 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 55 | n/a | False | 1 | 39 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 56 | 0.7921 | False | 0 | 606 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 57 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 58 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 59 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 60 | 0.6763 | False | 0 | 513 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 61 | 0.8041 | False | 0 | 532 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 62 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 63 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 64 | 0.8083 | False | 0 | 532 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 65 | 0.7974 | False | 0 | 590 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 66 | 0.6680 | False | 0 | 536 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 67 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 68 | 0.7950 | False | 0 | 608 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 69 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 70 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 71 | 0.7323 | False | 0 | 527 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 72 | 0.8114 | False | 0 | 528 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 73 | 0.6648 | False | 0 | 518 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 74 | 0.8049 | False | 0 | 540 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 75 | 0.7000 | False | 0 | 519 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 76 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 77 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 78 | 0.8098 | False | 0 | 564 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 79 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 80 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 81 | n/a | False | 1 | 38 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 82 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 83 | 0.7296 | False | 0 | 529 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 84 | 0.6722 | False | 0 | 524 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 85 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 86 | n/a | False | 1 | 36 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 87 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 88 | 0.8155 | True | 0 | 531 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [re-check seeds+200: 0.8155 / 0.8155] [proposed seeds=10] |
| 89 | 0.8093 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 90 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 91 | 0.8112 | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 92 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 93 | 0.8104 | False | 0 | 529 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 94 | 0.8104 | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 95 | 0.8153 | False | 0 | 537 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 96 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 97 | 0.8105 | False | 0 | 532 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 98 | 0.8112 | False | 0 | 529 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 99 | 0.8149 | False | 0 | 537 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 100 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 101 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 102 | 0.8177 | False | 0 | 532 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 103 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 104 | 0.8118 | False | 0 | 531 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 105 | 0.8083 | False | 0 | 532 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 106 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 107 | 0.8118 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 108 | 0.8111 | False | 0 | 563 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 109 | 0.8107 | False | 0 | 535 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 110 | n/a | False | 0 | 561 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 111 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 112 | 0.7665 | False | 0 | 521 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 113 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 114 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 115 | n/a | False | 1 | 36 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 116 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 117 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 118 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 119 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 120 | n/a | False | 0 | 529 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 121 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 122 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 123 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 124 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 125 | 0.7561 | False | 0 | 561 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 126 | 0.8011 | False | 0 | 588 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 127 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 128 | 0.8006 | False | 0 | 579 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 129 | 0.7695 | False | 0 | 518 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 130 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 131 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 132 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 133 | 0.8109 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 134 | 0.8152 | False | 0 | 532 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 135 | 0.8098 | False | 0 | 582 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 136 | n/a | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 137 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 138 | 0.7515 | False | 0 | 528 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 139 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 140 | 0.8143 | False | 0 | 534 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 141 | 0.8184 | False | 0 | 528 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 142 | 0.8129 | False | 0 | 528 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 143 | 0.8105 | False | 0 | 500 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 144 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 145 | 0.8100 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 146 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 147 | 0.8083 | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 148 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 149 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 150 | 0.8092 | False | 0 | 560 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 151 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 152 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 153 | 0.8129 | False | 0 | 523 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 154 | 0.8097 | False | 0 | 531 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 155 | 0.8043 | False | 0 | 515 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 156 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 157 | 0.8131 | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 158 | 0.8095 | False | 0 | 536 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 159 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 160 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 161 | 0.7404 | False | 0 | 529 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 162 | 0.8157 | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 163 | 0.7176 | False | 0 | 518 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 164 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 165 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 166 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 167 | 0.8157 | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 168 | 0.7714 | False | 0 | 519 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 169 | 0.7250 | False | 0 | 523 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 170 | 0.8125 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 171 | 0.7577 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 172 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 173 | 0.7682 | False | 0 | 520 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 174 | 0.7173 | False | 0 | 520 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 175 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 176 | 0.7584 | False | 0 | 521 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 177 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 178 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 179 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 180 | 0.8162 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 181 | 0.7604 | False | 0 | 525 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 182 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 183 | 0.8164 | False | 0 | 529 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 184 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 185 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 186 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 187 | 0.7655 | False | 0 | 558 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 188 | 0.7909 | False | 0 | 519 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 189 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 190 | 0.8056 | False | 0 | 547 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 191 | 0.8118 | False | 0 | 533 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 192 | n/a | False | 0 | 531 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 193 | 0.7689 | False | 0 | 521 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 194 | 0.6697 | False | 0 | 516 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 195 | 0.8060 | False | 0 | 532 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 196 | 0.7981 | False | 0 | 623 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 197 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 198 | n/a | False | 1 | 35 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 199 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 200 | 0.8155 | False | 0 | 526 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 201 | 0.8135 | False | 0 | 530 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 202 | n/a | False | 1 | 36 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 203 | n/a | False | 0 | 0 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 204 | n/a | False | 1 | 38 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 205 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 206 | 0.8111 | False | 0 | 675 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.04280634920634917, 'se': 0.00431638127486673, 'ci95': [0.03456507936507932, 0.050303990929705195], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': -0.015503830576294352, 'se': 0.005295209532727474, 'ci95': [-0.025705887376177256, -0.0057948811789391265], 'p_signflip': 0.015625, 'seeds_better': 2}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.10151836734693873, 'se': 0.00282535798479138, 'ci95': [0.095849387755102, 0.10630761904761896], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': -0.01825354999268044, 'se': 0.007821588952534797, 'ci95': [-0.033501390718782, -0.004233164983165045], 'p_signflip': 0.04296875, 'seeds_better': 2}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.05871201814058956, 'se': 0.004567893669034145, 'ci95': [0.050026167800453526, 0.06692607709750564], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': -0.0027497194163860874, 'se': 0.004763009336711558, 'ci95': [-0.011947738252086044, 0.0057210022934659896], 'p_signflip': 0.580078125, 'seeds_better': 5}}}
### stage-13_v2  (mode: code; generated 2026-10-15T14:06:20+00:00)

baseline_metric=0.7687, best_metric=0.8155 (experiment_v0/), stop_reason=global_deadline, iterations=2

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 0 | 0.8155 | False | 0 | 531 | overrides `{"aggr": "max", "dropout": 0.15, "gnn_type": "k2_ladder", "residual": true}` (None) [proposed seeds=10] |
| 1 | 0.7978 | False | 0 | 588 | files: rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py, rb_tokens.py (runtime-repaired) [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.05111383219954646, 'se': 0.006436818132564576, 'ci95': [0.03964263038548749, 0.06369988662131519], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': -0.019952666764260996, 'se': 0.006066390963489085, 'ci95': [-0.03088159371492709, -0.008636083052749755], 'p_signflip': 0.01171875, 'seeds_better': 1}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.10098412698412691, 'se': 0.0023064670557862974, 'ci95': [0.0964261904761904, 0.10497145124716549], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': -0.019248035914702633, 'se': 0.005946534053607017, 'ci95': [-0.03008283316254342, -0.007930439662323732], 'p_signflip': 0.013671875, 'seeds_better': 2}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.04987029478458046, 'se': 0.007447746124434547, 'ci95': [0.03595918367346937, 0.0636356916099773], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.000704630849558363, 'se': 0.006243653001904085, 'ci95': [-0.011217610891523904, 0.012009954618650242], 'p_signflip': 0.91015625, 'seeds_better': 6}}}
### stage-13  (mode: code; generated 2026-10-15T14:32:27+00:00)

baseline_metric=0.7687, best_metric=0.8155 (experiment_v0/), stop_reason=global_deadline, iterations=1

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 0 | 0.8155 | False | 0 | 531 | overrides `{"aggr": "max", "dropout": 0.15, "gnn_type": "k2_ladder", "residual": true}` (None) [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.04812244897959182, 'se': 0.003013189378803357, 'ci95': [0.04280074829931974, 0.0540690929705215], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': -0.019830185917142428, 'se': 0.003707017284511375, 'ci95': [-0.026511040355243275, -0.01280240813936466], 'p_signflip': 0.00390625, 'seeds_better': 1}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.10362811791383222, 'se': 0.0031986411669021244, 'ci95': [0.09745292517006802, 0.10921188208616786], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': -0.014814326843312376, 'se': 0.0063954032548941995, 'ci95': [-0.026776045478944067, -0.003105340848094472], 'p_signflip': 0.03515625, 'seeds_better': 1}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.05550566893424038, 'se': 0.0037664165948843487, 'ci95': [0.048264784580498835, 0.06221324263038551], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.005015859073830053, 'se': 0.0067643289322937405, 'ci95': [-0.007479700385497533, 0.017590323525106116], 'p_signflip': 0.4765625, 'seeds_better': 6}}}

### Confirmation on fresh seeds (stage-13_v1/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7126 ± 0.0102 | 0.7344 ± 0.0173 |
| baseline_tuned | 0.7713 ± 0.0150 | 0.7316 ± 0.0087 |
| proposed | 0.8141 ± 0.0055 | 0.7161 ± 0.0161 |

### Confirmation on fresh seeds (stage-13_v2/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7132 ± 0.0069 | 0.7334 ± 0.0086 |
| baseline_tuned | 0.7631 ± 0.0192 | 0.7341 ± 0.0173 |
| proposed | 0.8142 ± 0.0054 | 0.7141 ± 0.0132 |

### Confirmation on fresh seeds (stage-13/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7108 ± 0.0109 | 0.7261 ± 0.0109 |
| baseline_tuned | 0.7663 ± 0.0119 | 0.7311 ± 0.0185 |
| proposed | 0.8144 ± 0.0040 | 0.7113 ± 0.0144 |

## 4. Analysis, paper and checks

- quality report: score 7.0/10 — Accept with minor revisions
- fabrication flags: suspected=False, verified values=412
- citations: 21/21 verified
- weaknesses: Numerical inconsistency between the provided experiment summary and the paper's reported metrics (e.g., proposed test ROC-AUC differs by ~0.002).; Conclusion section is truncated in the provided text, leaving the final argument incomplete.; Minor inconsistency in statistical test descriptions (mentions Wilcoxon signed-rank in Related Work but primarily reports bootstrap/testing throughout).; Lacks computational efficiency benchmarks (FLOPs, inference latency) despite claims of memory efficiency.
- required_actions: Reconcile all reported numerical values with the official experiment summary to ensure exact consistency.; Complete and polish the Conclusion section to formally summarize findings and future directions.; Clarify the statistical testing protocol by standardizing the terminology (e.g., stick to paired bootstrap or specify both if used).; Add computational cost analysis (FLOPs/inference time) to support claims of architectural efficiency.
- paper PDF: `rc-20261014-152719-4d33ce/stage-22/paper.pdf`
- paper length: 5134 words
- numbers (0.5–1.0, 3–4 decimals) in the paper: 6; **without a match among the run's aggregated results: 0**
- seed counts claimed in the paper text: ['10']

<details><summary>abstract (as written by the pipeline)</summary>

Abstract  Relational deep learning on benchmarks like RelBench demands models that capture complex heterogeneous dependencies while generalizing across temporal splits. The driver-dnf task exemplifies the difficulty of predicting binary failure outcomes on sparse, evolving graphs where validation performance frequently misaligns with test generalization. Despite the proliferation of heterogeneous graph neural networks, rigorous statistical validation remains scarce, and claims of architectural superiority often lack test-set alignment. We introduce K2, a structured message-passing architecture integrating Pre-LayerNorm, GELU activations, and residual ladder connections within a LadderHeteroSAGE module to stabilize gradient flow and mitigate over-smoothing on temporal relational graphs. K2 replaces standard mean aggregation with maximum pooling and applies normalization prior to convolution to enhance representational learning. We evaluate K2 against official and tuned GraphSAGE baselines using a strict test-set evaluation protocol with paired bootstrap testing. K2 achieves a validation ROC-AUC of 0.8144, surpassing the tuned baseline by 4.81% ($p=0.002$). However, K2 degrades test ROC-AUC to 0.7113, a statistically significant drop of 1.98% relative to the tuned baseline ($p=0.004$) and 1.48% relative to the official baseline ($p=0.035$). Training recipe tuning captures the maj
</details>

## 5. Interpretation (to be written by a human)

- **What was done:** 
- **Results that can be trusted (and why):** 
- **What went wrong / limitations:** 
- **Decision / next step:** 

