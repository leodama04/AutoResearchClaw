# Run report: RUN-004

> Generated automatically by `rb_task/tools/run_report.py` from the run directory. Facts only; interpretation is in the last section.

## 1. Overview

| field | value |
|---|---|
| run id | `rc-20261005-183409-9b9601` |
| final status | done (29/29 stage executions done, 0 failed, degraded=False) |
| generated | 2026-10-05T20:39:32+00:00 |
| total stage time | 2.03 h |
| topic | Improving graph neural networks for relational deep learning on RelBench: architecture and feature-encoding modifications of the official GraphSAGE baseline on rel-f1 driver-top3 (binary classification) |
| llm | qwen3.6-35b |
| experiment | mode=sandbox, time_budget_sec=1800, max_iterations=300, metric=primary_metric (maximize) |
| checkpoint | {"last_completed_stage": 23, "last_completed_name": "CITATION_VERIFY", "run_id": "rc-20261005-183409-9b9601", "timestamp": "2026-10-05T20:39:30+00:00"} |

Pipeline decisions after the analysis: [('refine', 'ITERATIVE_REFINE'), ('refine', 'ITERATIVE_REFINE')]

### Stage durations

| stage | status | seconds |
|---|---|---|
| stage-01 | done | 17 |
| stage-02 | done | 21 |
| stage-03 | done | 21 |
| stage-04 | done | 166 |
| stage-05 | done | 76 |
| stage-06 | done | 265 |
| stage-07 | done | 25 |
| stage-08 | done | 87 |
| stage-09 | done | 24 |
| stage-10 | done | 0 |
| stage-11 | done | 15 |
| stage-12 | done | 104 |
| stage-13 | done | 1474 |
| stage-13_v1 | done | 1906 |
| stage-13_v2 | done | 1702 |
| stage-14 | done | 203 |
| stage-14_v1 | done | 179 |
| stage-14_v2 | done | 206 |
| stage-15 | done | 11 |
| stage-15_v1 | done | 11 |
| stage-15_v2 | done | 7 |
| stage-16 | done | 137 |
| stage-17 | done | 450 |
| stage-18 | done | 25 |
| stage-19 | done | 49 |
| stage-20 | done | 15 |
| stage-21 | done | 16 |
| stage-22 | done | 73 |
| stage-23 | done | 18 |

## 2. Reference evaluation (stage 12)

status=completed, elapsed=103 s, peak GPU memory 3.4947 GB

| condition | seeds | val ROC-AUC | test ROC-AUC |
|---|---|---|---|
| baseline_graphsage | 10 | 0.7047 ± 0.0522 | 0.7663 ± 0.0384 |
| baseline_tuned | 10 | 0.7702 ± 0.0180 | 0.7880 ± 0.0218 |
| proposed | 10 | 0.7689 ± 0.0146 | 0.7899 ± 0.0237 |

primary_metric (selection metric) = 0.7689

## 3. Iterative refinement (stage 13)

### stage-13_v1  (mode: code; generated 2026-10-05T18:47:50+00:00)

baseline_metric=0.7689, best_metric=0.8200 (experiment_v8/), stop_reason=max_iterations_reached, iterations=10

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | n/a | False | 1 | 1 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 2 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 3 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 4 | 0.7002 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 5 | 0.7428 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 6 | 0.6762 | False | 0 | 104 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) [proposed seeds=10] |
| 7 | n/a | False | 1 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 8 | 0.8200 | True | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 9 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 10 | 0.8212 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.0507158087115443, 'se': 0.009811284509813799, 'ci95': [0.03140944437476477, 0.06754076257368621], 'p_signflip': 0.005859375, 'seeds_better': 9}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': 0.03761170045986616, 'se': 0.0063302487314961745, 'ci95': [0.024805944946697224, 0.04857689694816052], 'p_signflip': 0.00390625, 'seeds_better': 9}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.10635358621060367, 'se': 0.01636500488445461, 'ci95': [0.07620715450359253, 0.1375752539821899], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.07406001776755847, 'se': 0.007493356587485191, 'ci95': [0.059851719272575175, 0.087816386653428], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.05563777749905938, 'se': 0.017176418602500767, 'ci95': [0.023332049237605505, 0.08649406031069147], 'p_signflip': 0.0234375, 'seeds_better': 7}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.0364483173076923, 'se': 0.009666725226546897, 'ci95': [0.018969808214882915, 0.055179716894857886], 'p_signflip': 0.005859375, 'seeds_better': 9}}}
### stage-13_v2  (mode: code; generated 2026-10-05T19:24:38+00:00)

baseline_metric=0.7689, best_metric=0.8200 (experiment/), stop_reason=max_iterations_reached, iterations=10

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 2 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 3 | n/a | False | 0 | 118 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py **REJECTED: PROPOSED_SOURCE does not cite an implementation card; set it to one of ['K1', 'K2', 'K3', 'K4'], e.g. "K1: <component you implemented>"** [proposed seeds=10] |
| 4 | 0.8221 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 5 | 0.8193 | False | 0 | 118 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 6 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 7 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 8 | 0.8229 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 9 | 0.8219 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 10 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.04756768378993394, 'se': 0.01022958905610537, 'ci95': [0.02747406425256669, 0.06513415814086833], 'p_signflip': 0.0078125, 'seeds_better': 8}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': 0.03894034803511705, 'se': 0.005495228298860938, 'ci95': [0.028132724315426415, 0.04855292380852842], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.1047266667861175, 'se': 0.01621812441003721, 'ci95': [0.07532354732937961, 0.1357280822776872], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.07468776128762537, 'se': 0.006633172247176852, 'ci95': [0.0625424265781772, 0.08741402004076085], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.05715898299618357, 'se': 0.017879518577476324, 'ci95': [0.023754143448424192, 0.08943962659690743], 'p_signflip': 0.0234375, 'seeds_better': 7}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.03574741325250833, 'se': 0.009112530817244486, 'ci95': [0.019096157112249115, 0.052748958115593596], 'p_signflip': 0.005859375, 'seeds_better': 9}}}
### stage-13  (mode: code; generated 2026-10-05T19:57:26+00:00)

baseline_metric=0.7689, best_metric=0.8200 (experiment/), stop_reason=global_deadline, iterations=9

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | 0.8205 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 2 | 0.8198 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 3 | n/a | False | 1 | 12 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 4 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 5 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 6 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py |
| 7 | 0.8108 | False | 0 | 119 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py [proposed seeds=10] |
| 8 | n/a | False | 0 | 2 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |
| 9 | n/a | False | 1 | 11 | files: main.py, rb_config.py, rb_data.py, rb_loader.py, rb_model.py, rb_model_official.py, rb_text.py (runtime-repaired) |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0, 'paired': {'proposed-baseline_tuned:val': {'n': 10, 'mean_diff': 0.04895809069896615, 'se': 0.008271332518713032, 'ci95': [0.03253072870939421, 0.06305033953880064], 'p_signflip': 0.00390625, 'seeds_better': 9}, 'proposed-baseline_tuned:test': {'n': 10, 'mean_diff': 0.03162886705685618, 'se': 0.007196134216783486, 'ci95': [0.017754706443352853, 0.044422325721153816], 'p_signflip': 0.00390625, 'seeds_better': 9}, 'proposed-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.10426439232409383, 'se': 0.01662173312301222, 'ci95': [0.07365573094909607, 0.13561744100625323], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'proposed-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.07321801839464882, 'se': 0.0075831245363318905, 'ci95': [0.05893136627299331, 0.08746265220004186], 'p_signflip': 0.001953125, 'seeds_better': 10}, 'baseline_tuned-baseline_graphsage:val': {'n': 10, 'mean_diff': 0.05530630162512769, 'se': 0.01744207012903227, 'ci95': [0.02247746859938007, 0.08688999480389174], 'p_signflip': 0.0234375, 'seeds_better': 7}, 'baseline_tuned-baseline_graphsage:test': {'n': 10, 'mean_diff': 0.04158915133779264, 'se': 0.009740629985299936, 'ci95': [0.02267966790342815, 0.05911377769648831], 'p_signflip': 0.005859375, 'seeds_better': 9}}}

### Confirmation on fresh seeds (stage-13_v1/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7199 ± 0.0557 | 0.7559 ± 0.0219 |
| baseline_tuned | 0.7755 ± 0.0116 | 0.7923 ± 0.0242 |
| proposed | 0.8262 ± 0.0246 | 0.8300 ± 0.0091 |

### Confirmation on fresh seeds (stage-13_v2/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7203 ± 0.0560 | 0.7560 ± 0.0221 |
| baseline_tuned | 0.7774 ± 0.0125 | 0.7918 ± 0.0222 |
| proposed | 0.8250 ± 0.0248 | 0.8307 ± 0.0067 |

### Confirmation on fresh seeds (stage-13/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7202 ± 0.0562 | 0.7558 ± 0.0221 |
| baseline_tuned | 0.7755 ± 0.0111 | 0.7974 ± 0.0224 |
| proposed | 0.8245 ± 0.0215 | 0.8290 ± 0.0077 |

## 4. Analysis, paper and checks

- quality report: score 8.0/10 — Accept
- fabrication flags: suspected=False, verified values=400
- citations: 14/15 verified
- weaknesses: Evaluation restricted to a single RelBench task, limiting claims of generalizability; Minor mathematical notation error in the residual normalization equation (self-referential variable before definition); Citation formatting uses placeholder-style year tags rather than standard venue-compliant references; Slight conceptual ambiguity between mean aggregation and GATv2 dynamic attention mechanisms in the method section
- required_actions: Clarify the precise interaction between mean aggregation and GATv2 attention to resolve methodological ambiguity; Correct the residual+LayerNorm equation to use an intermediate unnormalized hidden state variable; Standardize all citations to match target publication guidelines; Reconcile minor numerical differences between reported table values and the experiment summary log
- paper PDF: `/tmp/run9/terzo_esperimento_relbench_f1_driver_top3/stage-22/paper.pdf`
- paper length: 4235 words
- numbers (0.5–1.0, 3–4 decimals) in the paper: 15; **without a match among the run's aggregated results: 9** → ['0.7492', '0.7658', '0.7719', '0.7837', '0.7852', '0.8180', '0.8260', '0.8310', '0.8320']
- seed counts claimed in the paper text: ['10', 'ten']

<details><summary>abstract (as written by the pipeline)</summary>

Abstract Relational deep learning benchmarks require robust architectures capable of capturing heterogeneous interactions across complex databases. The official GraphSAGE baseline on RelBench relies on sum aggregation, large batch sizes, and lacks standard normalization techniques, leading to suboptimal performance and training instability on tasks like driver-top-3 prediction. We introduce REL, a refined configuration of the official GraphSAGE pipeline that replaces sum aggregation with mean aggregation, adopts the GATv2 message-passing operator, and integrates residual connections, layer normalization, and dropout. These architectural changes are combined with a tuned training recipe to ensure fair and stable optimization. On the `rel-f1-driver-top3` binary classification task, REL achieves a validation ROC-AUC of 0.8245 and a test ROC-AUC of 0.8290, significantly outperforming the official baseline by 10.4 and 7.3 percentage points, respectively. Paired statistical testing confirms that these gains are robust across ten random seeds (sign-flip p < 0.004). Our analysis disentangles the contributions of training recipes versus architectural design, demonstrating that while recipe tuning yields the largest baseline improvements, architectural refinements provide a statistically significant boost in representation quality. This work establishes that standard stabilizers are esse
</details>

## 5. Interpretation (to be written by a human)

- **What was done:** 
- **Results that can be trusted (and why):** 
- **What went wrong / limitations:** 
- **Decision / next step:** 

