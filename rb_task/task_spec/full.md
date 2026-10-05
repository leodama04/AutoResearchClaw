## TASK SPECIFICATION (authoritative - overrides any conflicting default guidance above)

### Study
Improve an existing graph neural network on a RelBench v1 task. Dataset `rel-f1`, task `driver-top3`:
binary classification - will a driver qualify in the top 3 in a race within the next 30 days
(entity table `drivers`, time column `date`, target `qualifying`). Metric: ROC-AUC (`roc_auc`).
Temporal splits: validation from 2005-01-01, test from 2010-01-01. RelBench version 1.1.0.
The starting point is the OFFICIAL RelBench GNN (heterogeneous GraphSAGE over the relational
database graph, PyTorch Frame feature encoders, relative-time encoder, MLP head).

### Environment (everything is pre-installed and OFFLINE - never pip install, never download)
Python 3.12, torch 2.8 (CUDA), torch_geometric (+ pyg-lib), torch_frame, relbench==1.1.0,
sentence-transformers (GloVe cached), lightgbm, scikit-learn, numpy, pandas. A GPU is available and
SHOULD be used. The dataset and task tables are cached; load them only through the code in
`rb_data.py` / `rb_loader.py`. This task REQUIRES deep learning: ignore any earlier instruction to stay CPU-only,
lightweight, self-contained or free of external libraries.

### Project layout (already written and working - EDIT IT, do not rewrite it from scratch)
- `main.py`      entry point; runs conditions x seeds, reports metrics through `experiment_harness`.
- `rb_config.py` `BASELINE` (official config, DO NOT CHANGE), `PROPOSED` (the model to improve),
                 `TRAIN` defaults, `SEEDS` (keep >= 3 seeds; 10 by default), `CONDITIONS`.
- `rb_model.py`  `Model`, `HeteroGNN`, `make_conv`, `build_gnn` - the main place to modify the GNN.
- `rb_train.py`  train/eval loops. `rb_data.py`, `rb_loader.py`, `rb_text.py`: data/graph loading - do not edit.
Return COMPLETE files for every file you change, keep every other file untouched.

### Search mode (how the refinement works)
SEARCH MODE = config (default of `./run.sh relbench`): the refinement does NOT write code. At every step it proposes the next
architecture configuration as JSON; an executor writes it into `rb_config.PROPOSED_OVERRIDES` and runs the unchanged project.
`main.py`, `rb_data.py`, `rb_loader.py`, `rb_text.py` and `rb_train.py` can never change, and in `rb_config.py` only
`PROPOSED_OVERRIDES` can. The allowed keys and values are listed in `rb_task/task_spec/search_space.json` (operator, depth, width,
aggregation, dropout, residual / jumping-knowledge connections, feature-encoder depth/width/dropout, time encoding, readout depth).
An iteration counts only if the whole project ran to completion with every condition and every seed; the final model is then
re-evaluated on fresh seeds (`confirm_*` metrics) that were never used to choose anything.

### Conditions (names are fixed)
`baseline_graphsage` (official RelBench GraphSAGE, official recipe) and `proposed` (current best variant). When
`rb_config.RECIPE == "tuned"` there is a third condition, `baseline_tuned`: the SAME official architecture trained with a
better recipe (batch_size 128). Measured on rel-f1/driver-top3: the official recipe is under-trained (only 30 optimiser
updates), so simply training longer already raises the validation AUROC from ~0.69 to ~0.77. With the tuned recipe the
TRAINING RECIPE IS FIXED: do NOT change lr, epochs, batch_size, weight_decay, num_neighbors, temporal_strategy or
max_fanout_product -- only the architecture (layers, channels, aggregation, GNN operator, normalisation, dropout,
residual connections, feature/column encoders, temporal encoding, readout head, forward pass). `proposed` starts
identical to `baseline_tuned`, so any difference comes from your modifications. Optional ablations must be named
`ablation_<what>` and must differ genuinely from `proposed`.

In the experiment plan list exactly the conditions `baseline_graphsage` and `proposed` (plus optional
`ablation_*`); the hyper-parameters of `proposed` are to be found by iterative refinement, not fixed in the plan.

### Evaluation protocol (must not be changed - violations invalidate the study)
1. Fit on the train table; select the best epoch/hyper-parameters ONLY with the VALIDATION metric.
2. The test metric is computed once per trained model from the validation-selected checkpoint and is
   REPORTED ONLY. Never use it (or the test table labels) to choose anything.
3. `primary_metric` = mean validation ROC-AUC of the `proposed` condition over seeds (higher is
   better; `main.py` already prints it). Do not redefine it.
4. No external data, no pretrained weights, no labels or features from outside the RelBench database.

### What you may change (one idea at a time, so effects can be attributed)
(With the official recipe you may also change the training recipe; with the tuned one you may not.)
Number of layers; channels; aggregation; GNN operator (`gnn_type`: sage, gatv2, gin, transformer,
resgated -- or another PyG operator that supports bipartite inputs; note GraphConv is mathematically the
same layer as SAGE with sum aggregation, so it is NOT a real alternative); normalisation; dropout;
residual / jumping-knowledge connections; the PyTorch Frame column encoder (ResNet depth/width, or
other `torch_frame.nn.models`); how node features/columns are embedded; temporal encoding; shallow ID
embeddings; the readout head; loss (e.g. `pos_weight`); optimiser, learning rate, weight decay,
scheduler; neighbour sampling (`num_neighbors`, `temporal_strategy`); epochs; `forward()` changes.

### Hard rules
- Use only APIs that appear in the seed files or in the official PyTorch / PyG / PyTorch Frame
  documentation. Do NOT invent methods. The harness has exactly: `should_stop()`,
  `report_metric(name, value)`, `log_result(dict)`, `finalize()`, `step()`, `elapsed`, `progress`.
- GPU memory is shared with the LLM server and is limited. Measured on rel-f1: the 2-layer baseline peaks at
  ~3.8 GB, but a 3-layer model needs >20 GB at batch 512 because each seed's temporal subgraph then reaches a large
  part of the database. `rb_data.build_loaders` therefore splits large batches into micro-batches (gradient
  accumulation) so that each optimiser step processes about as many sampled nodes as the baseline; you do not have
  to handle this. Deeper or wider models still cost more time per epoch -- prefer ideas that do not multiply the
  sampled subgraph (operator, encoders, normalisation, head, regularisation, optimisation) before adding layers.
  `main.py` prints `peak_gb` per run.
- Keep one training run short; the whole script must finish well inside the time budget
  (every run checks `harness.should_stop()`). No multiprocessing, no lambdas in dispatch dicts.
- Keep `main.py` printing `primary_metric` and the per-condition metrics. Keep the `if __name__ ==
  "__main__":` entry point.
- When something fails, fix the root cause; never hard-code metric values.
