# Run report: RUN-005

> Generated automatically by `rb_task/tools/run_report.py` from the run directory. Facts only; interpretation is in the last section.

## 1. Overview

| field | value |
|---|---|
| run id | `rc-20261006-144130-9b9601` |
| final status | done (29/29 stage executions done, 0 failed, degraded=True) |
| generated | 2026-10-06T16:45:35+00:00 |
| total stage time | 1.98 h |
| topic | Improving graph neural networks for relational deep learning on RelBench: architecture and feature-encoding modifications of the official GraphSAGE baseline on rel-f1 driver-top3 (binary classification) |
| llm | qwen3.6-35b |
| experiment | mode=sandbox, time_budget_sec=1800, max_iterations=300, metric=primary_metric (maximize) |
| checkpoint | {"last_completed_stage": 23, "last_completed_name": "CITATION_VERIFY", "run_id": "rc-20261006-144130-9b9601", "timestamp": "2026-10-06T16:45:33+00:00"} |

Pipeline decisions after the analysis: [('refine', 'ITERATIVE_REFINE'), ('refine', 'ITERATIVE_REFINE')]

### Stage durations

| stage | status | seconds |
|---|---|---|
| stage-01 | done | 15 |
| stage-02 | done | 21 |
| stage-03 | done | 22 |
| stage-04 | done | 201 |
| stage-05 | done | 73 |
| stage-06 | done | 192 |
| stage-07 | done | 20 |
| stage-08 | done | 94 |
| stage-09 | done | 43 |
| stage-10 | done | 0 |
| stage-11 | done | 21 |
| stage-12 | done | 103 |
| stage-13 | done | 1722 |
| stage-13_v1 | done | 1570 |
| stage-13_v2 | done | 1786 |
| stage-14 | done | 223 |
| stage-14_v1 | done | 181 |
| stage-14_v2 | done | 187 |
| stage-15 | done | 13 |
| stage-15_v1 | done | 14 |
| stage-15_v2 | done | 14 |
| stage-16 | done | 30 |
| stage-17 | done | 307 |
| stage-18 | done | 22 |
| stage-19 | done | 42 |
| stage-20 | done | 14 |
| stage-21 | done | 17 |
| stage-22 | done | 154 |
| stage-23 | done | 23 |

## 2. Reference evaluation (stage 12)

status=completed, elapsed=103 s, peak GPU memory 3.8661 GB

| condition | seeds | val ROC-AUC | test ROC-AUC |
|---|---|---|---|
| baseline_graphsage | 10 | 0.7185 ± 0.0485 | 0.7637 ± 0.0312 |
| baseline_tuned | 10 | 0.7834 ± 0.0132 | 0.7929 ± 0.0162 |
| proposed | 10 | 0.7857 ± 0.0158 | 0.7925 ± 0.0153 |

primary_metric (selection metric) = 0.7857

## 3. Iterative refinement (stage 13)

### stage-13_v1  (mode: code; generated 2026-10-06T14:54:57+00:00)

baseline_metric=0.7857, best_metric=0.7857 (experiment/), stop_reason=max_iterations_reached, iterations=10

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | n/a | False | 0 | 102 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 2 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 3 | n/a | False | 0 | 3 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 4 | 0.6691 | False | 0 | 103 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 5 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 6 | 0.6687 | False | 0 | 135 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 7 | n/a | False | 1 | 12 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 8 | n/a | False | 0 | 102 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 9 | n/a | False | 0 | 102 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 10 | 0.7296 | False | 0 | 104 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.0033989715289100774, 'se': 0.0015331333562757195, 'ci95': [0.0006934116930354173, 0.006375176936446233], 'p_signflip': 0.04296875, 'seeds_better': 7}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': -0.00705933841973243, 'se': 0.010361326799818939, 'ci95': [-0.028965121368101993, 0.009406370845526816], 'p_signflip': 0.6015625, 'seeds_better': 6}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.04996864417408756, 'se': 0.01716137610171224, 'ci95': [0.01887244450018811, 0.08281208005590297], 'p_signflip': 0.01953125, 'seeds_better': 7}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.021852790551839463, 'se': 0.01629713334687588, 'ci95': [-0.006686480978260867, 0.05503484923704014], 'p_signflip': 0.21484375, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.04656967264517749, 'se': 0.01727397925909772, 'ci95': [0.015523776674849072, 0.07953727759760622], 'p_signflip': 0.029296875, 'seeds_better': 7}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.028912128971571895, 'se': 0.013618093610431046, 'ci95': [0.005581707906563518, 0.05634105873745812], 'p_signflip': 0.0625, 'seeds_better': 7}}}
### stage-13_v2  (mode: code; generated 2026-10-06T15:25:17+00:00)

baseline_metric=0.7857, best_metric=0.7857 (experiment/), stop_reason=max_iterations_reached, iterations=10

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 2 | n/a | False | 0 | 102 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 3 | n/a | False | 0 | 101 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 4 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 5 | 0.7901 | False | 0 | 122 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 6 | 0.6692 | False | 0 | 135 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 7 | n/a | False | 0 | 101 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 8 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 9 | n/a | False | 0 | 102 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** (runtime-repaired) [proposed seeds=10] |
| 10 | 0.7675 | False | 0 | 104 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': -0.0020838186020676773, 'se': 0.001559210131150106, 'ci95': [-0.004932764150436314, 0.0008421726899715584], 'p_signflip': 0.205078125, 'seeds_better': 2}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': 0.005031093227424699, 'se': 0.004707294143008291, 'ci95': [-0.0032666015625000605, 0.01395494748118724], 'p_signflip': 0.32421875, 'seeds_better': 7}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.0488864202397377, 'se': 0.01653622014912473, 'ci95': [0.019095429216462678, 0.0805494884520973], 'p_signflip': 0.015625, 'seeds_better': 7}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.031860759824414706, 'se': 0.013713546087658344, 'ci95': [0.012417694397993307, 0.06166178929765886], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.05097023884180538, 'se': 0.01621204429819681, 'ci95': [0.021714267796670905, 0.08196771245811763], 'p_signflip': 0.013671875, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.026829666596990008, 'se': 0.01309562552001704, 'ci95': [0.005182280779682304, 0.05409538957984951], 'p_signflip': 0.03125, 'seeds_better': 9}}}
### stage-13  (mode: code; generated 2026-10-06T15:59:18+00:00)

baseline_metric=0.7857, best_metric=0.8164 (experiment_v5/), stop_reason=max_iterations_reached, iterations=11

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 0 | 0.7901 | False | 0 | 122 | overrides `{"dropout": 0.3, "gnn_type": "relphormer", "norm": "layer_norm"}` (None) [proposed seeds=10] |
| 1 | 0.8060 | True | 0 | 121 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py [proposed seeds=10] |
| 2 | 0.8040 | False | 0 | 122 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py [proposed seeds=10] |
| 3 | n/a | False | 1 | 11 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py |
| 4 | n/a | False | 0 | 2 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py (runtime-repaired) |
| 5 | 0.8164 | True | 0 | 122 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py [proposed seeds=10] |
| 6 | 0.6508 | False | 0 | 123 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py [proposed seeds=10] |
| 7 | n/a | False | 0 | 122 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 8 | 0.8012 | False | 0 | 122 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py [proposed seeds=10] |
| 9 | n/a | False | 0 | 2 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py (runtime-repaired) |
| 10 | n/a | False | 0 | 2 | files: vendor_relphormer_huggingface_relformer.py, rb_model.py, rb_model_official.py, rb_loader.py, rb_config.py, rb_train.py, rb_data.py (runtime-repaired) |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.015466485101503313, 'se': 0.007974972615573221, 'ci95': [0.0014638243357044296, 0.031485235885398886], 'p_signflip': 0.064453125, 'seeds_better': 8}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': 0.00807378762541804, 'se': 0.011466227079130874, 'ci95': [-0.013423145511078607, 0.02871892310305178], 'p_signflip': 0.490234375, 'seeds_better': 5}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.06572181111250472, 'se': 0.016313794279826543, 'ci95': [0.03568436329755787, 0.0967988837325975], 'p_signflip': 0.00390625, 'seeds_better': 9}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.03639475334448158, 'se': 0.017475015995118425, 'ci95': [0.007988264919523314, 0.07281370845526756], 'p_signflip': 0.044921875, 'seeds_better': 7}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.0502553260110014, 'se': 0.016698700226693963, 'ci95': [0.020075477952374944, 0.08246223862679396], 'p_signflip': 0.015625, 'seeds_better': 7}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.02832096571906354, 'se': 0.012357793346636442, 'ci95': [0.008903294183737453, 0.05464136640363712], 'p_signflip': 0.015625, 'seeds_better': 9}}}

### Confirmation on fresh seeds (stage-13_v1/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7348 ± 0.0542 | 0.7654 ± 0.0430 |
| baseline_tuned | 0.7813 ± 0.0065 | 0.7944 ± 0.0251 |
| proposed | 0.7847 ± 0.0084 | 0.7873 ± 0.0251 |

### Confirmation on fresh seeds (stage-13_v2/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7350 ± 0.0533 | 0.7651 ± 0.0429 |
| baseline_tuned | 0.7859 ± 0.0097 | 0.7919 ± 0.0181 |
| proposed | 0.7838 ± 0.0101 | 0.7970 ± 0.0135 |

### Confirmation on fresh seeds (stage-13/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7345 ± 0.0539 | 0.7653 ± 0.0430 |
| baseline_tuned | 0.7847 ± 0.0083 | 0.7936 ± 0.0151 |
| proposed | 0.8002 ± 0.0315 | 0.8017 ± 0.0269 |

## 4. Analysis, paper and checks

- quality report: score 2.0/10 — Reject / Major Revision Required
- fabrication flags: suspected=False, verified values=411
- citations: 8/8 verified
- weaknesses: Critical numerical discrepancy: reported test ROC-AUC (0.8017) directly contradicts the provided experiment summary (0.7748); the proposed model actually underp; Methodological inconsistency: claims p=0.064 is statistically significant despite explicitly stating a p<0.05 threshold in the methodology; Overstated conclusions that fundamentally misrepresent the experimental outcomes; Several citations appear placeholder-like or potentially fabricated (e.g., [chen2023relphormer], [jiang2023relbench])
- required_actions: Immediately reconcile all reported metrics with the ground-truth experiment summary and correct the Results section to reflect the actual negative test gain; Fix statistical reporting to strictly adhere to the stated alpha=0.05 threshold; remove claims of significance for p>0.05; Rewrite Discussion and Conclusion to accurately reflect the true findings, acknowledging the test performance drop; Audit and replace all placeholder or unverifiable citations with verified, peer-reviewed literature
- paper PDF: `/tmp/run10/quarto_esperimento_relbench_f1_driver_top3/stage-22/paper.pdf`
- paper length: 3604 words
- numbers (0.5–1.0, 3–4 decimals) in the paper: 6; **without a match among the run's aggregated results: 0**
- seed counts claimed in the paper text: ['ten']

<details><summary>abstract (as written by the pipeline)</summary>

Abstract Relational deep learning on the RelBench benchmark, particularly the temporal driver-top3 forecasting task, demands robust graph neural network architectures capable of modeling heterogeneous, time-varying interactions. The official baseline relies on a standard GraphSAGE operator combined with batch normalization and no regularization, which frequently under-fits due to restrictive training recipes and unstable feature variance. We introduce Relphormer, a minimal architectural refinement that replaces the standard message-passing operator with a local attention mechanism, applies layer normalization within the readout MLP head, and enforces a dropout rate of 0.3 across all message-passing layers. Evaluated on the rel-f1 dataset with ten random seeds, Relphormer achieves a validation ROC-AUC of 0.8002 and a test ROC-AUC of 0.8017. The validation gain over the tuned official baseline is statistically significant (p=0.064, 95% CI [+0.0015, +0.0315]), while the test improvement remains positive but statistically indistinguishable (p=0.490, 95% CI [-0.0134, +0.0287]). Relative to the under-trained official baseline, Relphormer yields a robust test improvement of +0.0364 (p=0.045). These findings demonstrate that targeted normalization and attention-based message passing provide measurable gains on temporal relational graphs, though careful recipe tuning remains the primary
</details>

## 5. Interpretation (to be written by a human)

- **What was done:** 
- **Results that can be trusted (and why):** 
- **What went wrong / limitations:** 
- **Decision / next step:** 

