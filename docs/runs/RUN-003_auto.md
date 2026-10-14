# Run report: RUN-003

> Generated automatically by `rb_task/tools/run_report.py` from the run directory. Facts only; interpretation is in the last section.

## 1. Overview

| field | value |
|---|---|
| run id | `rc-20261004-190007-9b9601` |
| final status | done (29/29 stage executions done, 0 failed, degraded=False) |
| generated | 2026-10-04T20:33:30+00:00 |
| total stage time | 1.41 h |
| topic | Improving graph neural networks for relational deep learning on RelBench: architecture and feature-encoding modifications of the official GraphSAGE baseline on rel-f1 driver-top3 (binary classification) |
| llm | qwen3.6-35b |
| experiment | mode=sandbox, time_budget_sec=1800, max_iterations=12, metric=primary_metric (maximize) |
| checkpoint | {"last_completed_stage": 23, "last_completed_name": "CITATION_VERIFY", "run_id": "rc-20261004-190007-9b9601", "timestamp": "2026-10-04T20:33:29+00:00"} |

Pipeline decisions after the analysis: [('refine', 'ITERATIVE_REFINE'), ('refine', 'ITERATIVE_REFINE')]

### Stage durations

| stage | status | seconds |
|---|---|---|
| stage-01 | done | 16 |
| stage-02 | done | 20 |
| stage-03 | done | 22 |
| stage-04 | done | 162 |
| stage-05 | done | 51 |
| stage-06 | done | 44 |
| stage-07 | done | 21 |
| stage-08 | done | 94 |
| stage-09 | done | 41 |
| stage-10 | done | 0 |
| stage-11 | done | 16 |
| stage-12 | done | 111 |
| stage-13 | done | 1507 |
| stage-13_v1 | done | 771 |
| stage-13_v2 | done | 691 |
| stage-14 | done | 251 |
| stage-14_v1 | done | 262 |
| stage-14_v2 | done | 248 |
| stage-15 | done | 10 |
| stage-15_v1 | done | 15 |
| stage-15_v2 | done | 15 |
| stage-16 | done | 22 |
| stage-17 | done | 500 |
| stage-18 | done | 28 |
| stage-19 | done | 53 |
| stage-20 | done | 18 |
| stage-21 | done | 18 |
| stage-22 | done | 74 |
| stage-23 | done | 11 |

## 2. Reference evaluation (stage 12)

status=completed, elapsed=110 s, peak GPU memory 3.8661 GB

| condition | seeds | val ROC-AUC | test ROC-AUC |
|---|---|---|---|
| baseline_graphsage | 10 | 0.7223 ± 0.0476 | 0.7652 ± 0.0296 |
| baseline_tuned | 10 | 0.7872 ± 0.0095 | 0.7892 ± 0.0146 |
| proposed | 10 | 0.7871 ± 0.0109 | 0.7924 ± 0.0166 |

primary_metric (selection metric) = 0.7871

## 3. Iterative refinement (stage 13)

### stage-13_v1  (mode: config; generated 2026-10-04T19:10:05+00:00)

baseline_metric=0.7871, best_metric=0.7871 (experiment/), stop_reason=no_improvement_for_2_iterations, iterations=5

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | 0.6991 | False | 0 | 126 | overrides `{"dropout": 0.1, "gnn_type": "gatv2", "jk": "cat"}` (llm) — Switch to GATv2 to leverage attention for heterogeneous relations, use CatJK to aggregate  [proposed seeds=10] |
| 2 | 0.6810 | False | 0 | 125 | overrides `{"channels": 256, "residual": true}` (llm) — Reverting to the robust Sage baseline with residual connections and doubled channels to te [proposed seeds=10] |
| 3 | 0.7708 | False | 0 | 103 | overrides `{"aggr": "mean", "norm": "layer_norm"}` (llm) — Mean aggregation can reduce variance in neighbor updates compared to sum, and layer normal [proposed seeds=10] |
| 4 | 0.7914 | False | 0 | 100 | overrides `{"enc_dropout": 0.0, "time_encoding": false}` (llm) — Disabling temporal encoding and reducing encoder dropout to mitigate potential overfitting [proposed seeds=10] |
| 5 | 0.6778 | False | 0 | 104 | overrides `{"gnn_type": "gin", "jk": "cat"}` (llm) — GIN provides higher expressive power than GraphSAGE, and combining it with Jumping Knowled [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0}
### stage-13_v2  (mode: config; generated 2026-10-04T19:29:30+00:00)

baseline_metric=0.7871, best_metric=0.7871 (experiment/), stop_reason=no_improvement_for_2_iterations, iterations=5

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | 0.7765 | False | 0 | 117 | overrides `{"dropout": 0.2, "gnn_type": "gatv2", "residual": true}` (llm) — Switching to GATv2 with residual connections and 0.2 dropout to leverage attention and imp [proposed seeds=10] |
| 2 | 0.6834 | False | 0 | 112 | overrides `{"enc_layers": 6, "gnn_type": "resgated", "jk": "cat"}` (llm) — ResGated is a potent message-passing operator that often surpasses GraphSAGE; jumping know [proposed seeds=10] |
| 3 | 0.6772 | False | 0 | 104 | overrides `{"gnn_type": "gin", "jk": "cat", "residual": true}` (llm) — Combining GIN with jumping knowledge and residual connections can better capture multi-hop [proposed seeds=10] |
| 4 | 0.7752 | False | 0 | 103 | overrides `{"aggr": "mean", "dropout": 0.1}` (llm) — Retain the top-performing sage architecture while testing mean aggregation and mild dropou [proposed seeds=10] |
| 5 | 0.7016 | False | 0 | 101 | overrides `{"residual": true}` (llm) — Residual connections can stabilize gradient flow and improve representation learning in GN [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0}
### stage-13  (mode: config; generated 2026-10-04T19:46:32+00:00)

baseline_metric=0.7871, best_metric=0.8854 (experiment_v10/), stop_reason=max_iterations_reached, iterations=10

| it | metric | improved | rc | seconds | detail |
|---|---|---|---|---|---|
| 1 | 0.7116 | False | 0 | 150 | overrides `{"gnn_type": "gatv2", "jk": "cat", "residual": true}` (llm) — Adopting GATv2 for attention-based message passing improves feature mixing on heterogeneou [proposed seeds=10] |
| 2 | 0.7187 | False | 0 | 136 | overrides `{"aggr": "mean", "residual": true}` (llm) — Exploring mean aggregation and residual connections on the GraphSAGE baseline to improve g [proposed seeds=10] |
| 3 | 0.7757 | False | 0 | 127 | overrides `{"dropout": 0.1}` (llm) — The default configuration is currently the best, while GATv2 and mean-aggregation variants [proposed seeds=10] |
| 4 | 0.6815 | False | 0 | 121 | overrides `{"channels": 256, "residual": true}` (llm) — Increasing model capacity and adding residual connections may help capture richer relation [proposed seeds=10] |
| 5 | 0.8637 | True | 0 | 121 | overrides `{"aggr": "max", "dropout": 0.1}` (llm) — Max aggregation captures peak neighbor signals more effectively, and mild GNN dropout comp [proposed seeds=10] |
| 6 | 0.7342 | False | 0 | 120 | overrides `{"aggr": "max", "dropout": 0.1, "jk": "cat", "norm": "layer_norm", "residual": true}` (llm) — Adding residual connections and jumping knowledge with layer normalization can stabilize g [proposed seeds=10] |
| 7 | 0.8694 | True | 0 | 121 | overrides `{"aggr": "max", "channels": 256, "dropout": 0.1}` (llm) — Isolate the effect of increasing model capacity by testing 256 hidden channels alongside t [proposed seeds=10] |
| 8 | 0.8786 | True | 0 | 116 | overrides `{"aggr": "max", "channels": 256, "dropout": 0.1, "enc_layers": 2}` (fallback) — fallback neighbour search (4 keys differ from the best configuration (max 3)) [proposed seeds=10] |
| 9 | 0.8754 | False | 0 | 130 | overrides `{"aggr": "max", "channels": 256, "dropout": 0.1, "enc_layers": 2, "enc_width": 256}` (llm) — Increasing the encoder width to 256 compensates for the reduced depth and may enhance the  [proposed seeds=10] |
| 10 | 0.8854 | True | 0 | 118 | overrides `{"aggr": "max", "channels": 256, "dropout": 0.1, "enc_layers": 2, "head_layers": 2}` (llm) — Deepening the readout MLP head to improve classification capacity on top of the optimized  [proposed seeds=10] |

Confirmation on fresh seeds: {'seed_offset': 100, 'valid': True, 'reason': '', 'returncode': 0}

### Confirmation on fresh seeds (stage-13_v1/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7329 ± 0.0540 | 0.7645 ± 0.0439 |
| baseline_tuned | 0.7852 ± 0.0091 | 0.8021 ± 0.0200 |
| proposed | 0.7852 ± 0.0116 | 0.7932 ± 0.0264 |

### Confirmation on fresh seeds (stage-13_v2/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7329 ± 0.0539 | 0.7645 ± 0.0439 |
| baseline_tuned | 0.7841 ± 0.0094 | 0.7993 ± 0.0253 |
| proposed | 0.7852 ± 0.0089 | 0.8178 ± 0.0185 |

### Confirmation on fresh seeds (stage-13/confirmation.json)

seed offset 100, valid=True, rc=0

| condition | val ROC-AUC | test ROC-AUC |
|---|---|---|
| baseline_graphsage | 0.7327 ± 0.0540 | 0.7643 ± 0.0437 |
| baseline_tuned | 0.7878 ± 0.0128 | 0.8015 ± 0.0172 |
| proposed | 0.8884 ± 0.0071 | 0.8113 ± 0.0320 |

## 4. Analysis, paper and checks

- quality report: score 6.0/10 — Borderline / Accept with Revisions
- fabrication flags: suspected=False, verified values=409
- citations: 5/5 verified
- weaknesses: Lack of formal statistical testing: The authors admit to not performing paired statistical tests due to missing per-seed logs, weakening the claim of significan; Potential selective reporting: The initial results section heavily highlights the positive run before introducing the confirmatory run, which substantially redu; Methodological instability not adequately addressed: The paper identifies high sensitivity to initialization but offers only vague suggestions for future work r; Repetitive content: The Results section unnecessarily repeats the experimental setup and protocol details already detailed in the Experiments section.
- required_actions: Conduct and report proper paired statistical tests using per-seed logs to validate significance claims.; Reframe the Results section to present both initial and confirmatory runs concurrently or lead with the confirmatory run to avoid the appearance of selective re; Provide a deeper analysis on why the projection matrix fails to generalize across seeds, and propose concrete regularization or initialization strategies to mit; Remove redundant experimental setup descriptions from the Results section to improve conciseness.
- paper PDF: `/tmp/run8/secondo_esperimento_relbench_f1_driver_top3/stage-22/paper.pdf`
- paper length: 4559 words
- numbers (0.5–1.0, 3–4 decimals) in the paper: 12; **without a match among the run's aggregated results: 0**
- seed counts claimed in the paper text: ['10', 'ten']

<details><summary>abstract (as written by the pipeline)</summary>

Abstract  Relational deep learning on temporal benchmarks requires models to disentangle entity-specific signals from exogenous relational metadata while respecting strict evaluation protocols. Standard graph neural networks often treat tabular relational features as unstructured inputs, potentially learning spurious correlations that degrade generalization on small, volatile datasets. We introduce Relation-Conditioned Feature Projection (RCFP), a lightweight architectural intervention that learns a structured projection matrix to compress high-dimensional relational metadata into a latent manifold before message passing. This design aims to inject relational inductive biases directly into the encoding layer, reducing sensitivity to tabular noise. We evaluate RCFP against the official GraphSAGE baseline and a tuned variant on the `rel-f1-driver-top3` binary classification task from the RelBench benchmark. In initial trials, RCFP achieves a test ROC-AUC of $0.8255 \pm 0.020$, representing a $2.83\%$ absolute improvement over the tuned baseline of $0.7972 \pm 0.019$. However, confirmatory runs reveal a substantial performance drop, yielding a test ROC-AUC of $0.8113 \pm 0.032$ and a negligible $0.97\%$ gain over the tuned baseline. The results demonstrate that while relation-conditioned projections can improve mean performance in specific stochastic configurations, the method exh
</details>

## 5. Interpretation (to be written by a human)

- **What was done:** 
- **Results that can be trusted (and why):** 
- **What went wrong / limitations:** 
- **Decision / next step:** 

