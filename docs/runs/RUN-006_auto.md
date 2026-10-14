# Run report: RUN-006

> Generated automatically by `rb_task/tools/run_report.py` from the run directory. Facts only; interpretation is in the last section.

## 1. Overview

| field | value |
|---|---|
| run id | `rc-20261007-085443-9b9601` |
| final status | done (29/29 stage executions done, 0 failed, degraded=True) |
| generated | 2026-10-07T11:10:50+00:00 |
| total stage time | 2.21 h |
| topic | Improving graph neural networks for relational deep learning on RelBench: architecture and feature-encoding modifications of the official GraphSAGE baseline on rel-f1 driver-top3 (binary classification) |
| llm | qwen3.6-35b |
| experiment | mode=sandbox, time_budget_sec=1800, max_iterations=300, metric=primary_metric (maximize) |
| checkpoint | {"last_completed_stage": 23, "last_completed_name": "CITATION_VERIFY", "run_id": "rc-20261007-085443-9b9601", "timestamp": "2026-10-07T11:10:48+00:00"} |

Pipeline decisions after the analysis: [('refine', 'ITERATIVE_REFINE'), ('refine', 'ITERATIVE_REFINE')]

### Stage durations

| stage | status | seconds |
|---|---|---|
| stage-01 | done | 20 |
| stage-02 | done | 27 |
| stage-03 | done | 30 |
| stage-04 | done | 164 |
| stage-05 | done | 85 |
| stage-06 | done | 180 |
| stage-07 | done | 22 |
| stage-08 | done | 90 |
| stage-09 | done | 50 |
| stage-10 | done | 0 |
| stage-11 | done | 24 |
| stage-12 | done | 103 |
| stage-13 | done | 2038 |
| stage-13_v1 | done | 1631 |
| stage-13_v2 | done | 2153 |
| stage-14 | done | 190 |
| stage-14_v1 | done | 192 |
| stage-14_v2 | done | 265 |
| stage-15 | done | 12 |
| stage-15_v1 | done | 10 |
| stage-15_v2 | done | 15 |
| stage-16 | done | 29 |
| stage-17 | done | 408 |
| stage-18 | done | 33 |
| stage-19 | done | 51 |
| stage-20 | done | 14 |
| stage-21 | done | 18 |
| stage-22 | done | 83 |
| stage-23 | done | 17 |

## 2. Reference evaluation (stage 12)

status=completed, elapsed=102 s, peak GPU memory 3.7045 GB

| condition | seeds | val ROC-AUC | test ROC-AUC |
|---|---|---|---|
| baseline_graphsage | 10 | 0.7167 ± 0.0616 | 0.7776 ± 0.0310 |
| baseline_tuned | 10 | 0.7718 ± 0.0190 | 0.7813 ± 0.0197 |
| proposed | 10 | 0.7737 ± 0.0207 | 0.7950 ± 0.0210 |

primary_metric (selection metric) = 0.7737

## 3. Iterative refinement (stage 13)

### stage-13_v1  (mode: code; generated 2026-10-07T09:07:56+00:00)

baseline_metric=0.7737, best_metric=0.7737 (experiment/), stop_reason=max_iterations_reached, iterations=10

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 2 | n/a | False | 0 | 118 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: the component in PROPOSED_SOURCE ('Multi-head attention aggregation (GATv2) with Pre-LN') is not described in card K1: implement a component listed in the card and use its name** [proposed seeds=10] |
| 3 | n/a | False | 0 | 103 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: nothing changed with respect to the current best version: re-running the same code only measures noise - change the model** [proposed seeds=10] |
| 4 | n/a | False | 1 | 12 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 5 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 6 | n/a | False | 1 | 12 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 7 | n/a | False | 0 | 103 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: nothing changed with respect to the current best version: re-running the same code only measures noise - change the model** [proposed seeds=10] |
| 8 | n/a | False | 1 | 12 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 9 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 10 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': -0.0036408593288061787, 'se': 0.00339377240980287, 'ci95': [-0.010743670602569384, 0.0012883212986686432], 'p_signflip': 0.373046875, 'seeds_better': 5}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': -0.004374608068561825, 'se': 0.004846834395876697, 'ci95': [-0.013191252743520013, 0.004738091816471614], 'p_signflip': 0.40234375, 'seeds_better': 4}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.03834011216426868, 'se': 0.013578544094832806, 'ci95': [0.013258810987081359, 0.06386379925104374], 'p_signflip': 0.029296875, 'seeds_better': 8}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.015178851379598669, 'se': 0.016361189330716258, 'ci95': [-0.016927126881270883, 0.04316154760660537], 'p_signflip': 0.3828125, 'seeds_better': 7}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.04198097149307486, 'se': 0.0147954400941181, 'ci95': [0.014988532726523474, 0.07029281861998533], 'p_signflip': 0.0234375, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.019553459448160494, 'se': 0.015225687315352848, 'ci95': [-0.011083788409280987, 0.04505186559364542], 'p_signflip': 0.232421875, 'seeds_better': 8}}}
### stage-13_v2  (mode: code; generated 2026-10-07T09:39:24+00:00)

baseline_metric=0.7737, best_metric=0.7737 (experiment/), stop_reason=max_iterations_reached, iterations=10

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | n/a | False | 0 | 102 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** (runtime-repaired) [proposed seeds=10] |
| 2 | 0.7166 | False | 0 | 144 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 3 | n/a | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: nothing changed with respect to the current best version: re-running the same code only measures noise - change the model** [proposed seeds=10] |
| 4 | n/a | False | 0 | 124 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: the component in PROPOSED_SOURCE ('Multi-head attention aggregation with jumping knowledge') is not described in card K1: implement a component listed in the card and use its name** (runtime-repaired) [proposed seeds=10] |
| 5 | n/a | False | 0 | 129 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: nothing changed with respect to the current best version: re-running the same code only measures noise - change the model** [proposed seeds=10] |
| 6 | n/a | False | 1 | 13 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 7 | n/a | False | 1 | 12 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 8 | 0.7106 | False | 0 | 144 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 9 | n/a | False | 0 | 141 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: the component in PROPOSED_SOURCE ('Multi-head attention aggregation with jumping knowledge') is not described in card K1: implement a component listed in the card and use its name** [proposed seeds=10] |
| 10 | 0.6767 | False | 0 | 126 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.00791062693734208, 'se': 0.0067597008973705516, 'ci95': [-0.0024834262063034352, 0.02179346365411831], 'p_signflip': 0.30859375, 'seeds_better': 7}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': 0.0057470213210702335, 'se': 0.007712554640200771, 'ci95': [-0.00550546091137127, 0.02205951805497491], 'p_signflip': 0.6640625, 'seeds_better': 6}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.04270663489276303, 'se': 0.013307552226890958, 'ci95': [0.018603590690007235, 0.06843731522459726], 'p_signflip': 0.0078125, 'seeds_better': 8}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.02741429765886285, 'se': 0.010328848874783154, 'ci95': [0.009049076348244115, 0.04736839268917221], 'p_signflip': 0.029296875, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.03479600795542095, 'se': 0.01238099404153936, 'ci95': [0.01249010051781904, 0.0583363494651592], 'p_signflip': 0.025390625, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.02166727633779262, 'se': 0.014681854160792932, 'ci95': [-0.006139997909698984, 0.04811734100647981], 'p_signflip': 0.177734375, 'seeds_better': 8}}}
### stage-13  (mode: code; generated 2026-10-07T10:21:39+00:00)

baseline_metric=0.7737, best_metric=0.7737 (experiment/), stop_reason=max_iterations_reached, iterations=10

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | n/a | False | 0 | 121 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: nothing changed with respect to the current best version: re-running the same code only measures noise - change the model** [proposed seeds=10] |
| 2 | n/a | False | 0 | 128 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: the component in PROPOSED_SOURCE ('Multi-head attention aggregation') is not described in card K1: implement a component listed in the card and use its name** [proposed seeds=10] |
| 3 | n/a | False | 0 | 117 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: nothing changed with respect to the current best version: re-running the same code only measures noise - change the model** [proposed seeds=10] |
| 4 | n/a | False | 1 | 12 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 5 | n/a | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: nothing changed with respect to the current best version: re-running the same code only measures noise - change the model** [proposed seeds=10] |
| 6 | n/a | False | 0 | 117 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: nothing changed with respect to the current best version: re-running the same code only measures noise - change the model** [proposed seeds=10] |
| 7 | 0.6866 | False | 0 | 137 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 8 | n/a | False | 0 | 112 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: `proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py** [proposed seeds=10] |
| 9 | n/a | False | 0 | 147 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: the component in PROPOSED_SOURCE ('Multi-head attention aggregation') is not described in card K1: implement a component listed in the card and use its name** (runtime-repaired) [proposed seeds=10] |
| 10 | n/a | False | 0 | 135 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: the component in PROPOSED_SOURCE ('Multi-head attention aggregation') is not described in card K1: implement a component listed in the card and use its name** [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.0024242532834028996, 'se': 0.0016293847367459227, 'ci95': [-0.0001487609969360967, 0.005814266004909364], 'p_signflip': 0.181640625, 'seeds_better': 6}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': 1.633047658864406e-05, 'se': 0.004935583581583957, 'ci95': [-0.009354750209030049, 0.009650527801003356], 'p_signflip': 0.986328125, 'seeds_better': 4}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.044896167422192726, 'se': 0.014567222382409751, 'ci95': [0.01834911576570921, 0.0726546290157854], 'p_signflip': 0.009765625, 'seeds_better': 8}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.026927649456521752, 'se': 0.018765286897774618, 'ci95': [-0.009371880878971598, 0.06002648803302673], 'p_signflip': 0.1796875, 'seeds_better': 9}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.042471914138789826, 'se': 0.013814956951994316, 'ci95': [0.01747298919567823, 0.06889242264069804], 'p_signflip': 0.009765625, 'seeds_better': 8}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.026911318979933107, 'se': 0.0207082868082896, 'ci95': [-0.011878298756270974, 0.06494243507002506], 'p_signflip': 0.21875, 'seeds_better': 8}}}

### Confirmation on fresh seeds (stage-13_v1/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7182 ± 0.0581 | 0.7509 ± 0.0414 |
| baseline_tuned | 0.7602 ± 0.0190 | 0.7705 ± 0.0357 |
| proposed | 0.7566 ± 0.0177 | 0.7661 ± 0.0409 |

### Confirmation on fresh seeds (stage-13_v2/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7180 ± 0.0578 | 0.7507 ± 0.0423 |
| baseline_tuned | 0.7528 ± 0.0268 | 0.7724 ± 0.0309 |
| proposed | 0.7607 ± 0.0193 | 0.7781 ± 0.0161 |

### Confirmation on fresh seeds (stage-13/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7180 ± 0.0575 | 0.7448 ± 0.0471 |
| baseline_tuned | 0.7605 ± 0.0193 | 0.7717 ± 0.0384 |
| proposed | 0.7629 ± 0.0195 | 0.7717 ± 0.0405 |

## 4. Analysis, paper and checks

- quality report: score 2.0/10 — Reject
- fabrication flags: suspected=False, verified values=152
- citations: 20/21 verified
- weaknesses: Critical data inconsistency: Reported numerical results in tables fundamentally contradict the ground truth experiment summary metrics, indicating severe misrep; Proposed method failed to execute: The `proposed_identical_to_baseline` flag confirms the FeaGate module was never activated during training, rendering all perf; Severe reproducibility failure: The paper presents a novel architecture but admits it contributed nothing to the reported results, yet still lists it as a prima; Misleading statistical claims: Significance tests and performance deltas are calculated on unverified or mismatched data, undermining the scientific validity of
- required_actions: Immediately reconcile all reported tables and metrics with the ground truth experiment summary data to eliminate fabrication or misreporting.; Completely restructure the paper to accurately reflect that the proposed architecture failed execution, or provide a valid, verified configuration where the mod; Remove claims of architectural novelty or performance gains that cannot be causally attributed to the proposed module.; Conduct and report a proper ablation study with verified module execution before claiming any methodological contribution.
- paper PDF: `/tmp/run11/quinto_esperimento_relbench_f1_driver_top3/stage-22/paper.pdf`
- paper length: 4352 words
- numbers (0.5–1.0, 3–4 decimals) in the paper: 6; **without a match among the run's aggregated results: 1** → ['0.986']
- seed counts claimed in the paper text: ['10']

<details><summary>abstract (as written by the pipeline)</summary>

Abstract Relational deep learning benchmarks demand rigorous evaluation, yet standard graph neural networks frequently conflate architectural novelty with training recipe optimization. On the driver-top3 task, uniform neighborhood pooling ignores feature-level similarity, propagating noise across heterogeneous entities. We introduce FeaGate, a lightweight feature-conditioned aggregation module designed to modulate neighbor contributions based on cross-feature semantic alignment within the official GraphSAGE backbone. We implement FeaGate within a strictly controlled experimental protocol that enforces matched compute budgets, verified module execution, and multi-metric reporting. Experimental evaluation on the rel-f1 driver-top3 binary classification task demonstrates that FeaGate achieves a test ROC-AUC of 0.7717, matching the recipe-optimized baseline ($p=0.986$). The observed 0.0269 improvement over the unoptimized official baseline is statistically significant on the validation split ($p=0.010$) but not on the test split ($p=0.180$), and is entirely attributable to reducing the batch size from 512 to 128. These results establish that training recipe optimization dominates performance gains in this regime, offering a reproducible pathway for accurately attributing improvements in hybrid tabular-graph modeling.   > **Note:** This paper was produced in degraded mode. Quality g
</details>

## 5. Interpretation (to be written by a human)

- **What was done:** 
- **Results that can be trusted (and why):** 
- **What went wrong / limitations:** 
- **Decision / next step:** 

