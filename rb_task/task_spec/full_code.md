# RelBench task specification - CODE MODE (authoritative; overrides generic instructions)

## Study
Improve the official RelBench GNN ("RDL": PyTorch-Frame column encoders + relative-time encoding + heterogeneous
GraphSAGE message passing + MLP head) on RelBench 1.1.0, dataset `{{DATASET}}`, task `{{TASK}}` ({{TASK_TYPE}}:
{{TASK_DESC}}). Metric {{METRIC}} ({{METRIC_DIR}}). Temporal splits:
{{SPLITS}}.

## How the refinement works in CODE MODE
You write code. YOU decide, from the papers you found and read, which architecture to try. In every attempt implement
ONE idea taken from the implementation cards of the knowledge file
(K1, K2, ...: built at stage 6 from the FULL TEXT of the papers and their official code, shown below).
- Editable: `rb_model.py` (the model of `proposed` ONLY; it starts as the official RelBench model and contains no
  alternative architectures: every change comes from the papers you selected), new module files you create (e.g. `rb_<method>.py`), and in
  `rb_config.py` ONLY the dict `PROPOSED_OVERRIDES` and the string `PROPOSED_SOURCE`.
- Everything else is restored automatically: `main.py`, `rb_data.py`, `rb_loader.py`, `rb_text.py`, `rb_train.py`,
  `rb_model_official.py` (the frozen official model used by the baselines), `rb_tokens.py`, `vendor_*.py`, seeds, training
  recipe, conditions. Edits to these files are DISCARDED (the history tells you when this happened).
- ACTIVATE your component for `proposed`: read a new key/value from `cfg` in `rb_model.py` and set it in
  `PROPOSED_OVERRIDES` (e.g. `{"gnn_type": "<your option>"}`). If `proposed` stays functionally identical to `baseline_tuned`
  the attempt is rejected automatically.
- DECLARE the card: `PROPOSED_SOURCE = "K2: <component>"`. Attempts without a valid card id are rejected.
- OFFICIAL CODE FIRST. The official code of the papers is in the project as read-only `vendor_<repo>_<module>.py`
  files (listed in the cards with their classes and signatures). IMPORT those classes and write only the glue to our
  batch; do NOT rewrite them from scratch (re-implementations caused most crashes so far). `rb_tokens.py` (read-only)
  converts our batch into per-seed token sets, for official code that works on per-node token sequences:
  `tok = seed_token_sets(batch, x_dict, entity_table, k)` -> `tok["tokens"]` [B, K, C] (seed first), `tok["mask"]`,
  `tok["node_type"]`, `tok["hop"]`, `tok["rel_time"]` (days).
  Without official code, port the excerpt shown in the card. Generic code (e.g. a standard PyG operator) is acceptable
  when it is related to the cited card.
- Name new options after what they compute (e.g. `"gnn_type": "transformer_attn_drop"`), not after a paper whose method
  you did not implement in full.
- An attempt identical to the current best is rejected (re-running the same code only measures noise); an apparent
  improvement is re-evaluated on different seeds before being accepted.
- Return COMPLETE files (all imports) for every file you change. Keep `build_model(data, col_stats_dict, cfg,
  out_channels)` and `forward(batch, entity_table)` (logits `[num_seed_nodes, out_channels]`).
- If the previous attempt crashed or was rejected (REFINEMENT HISTORY), fix that first.

## Conditions (fixed)
`baseline_graphsage` (official model, official recipe), `baseline_tuned` (official model, batch size 128),
`proposed` (= `baseline_tuned` + your change). 10 seeds each; the training recipe is fixed.

## Protocol (non-negotiable)
- `primary_metric` = mean VALIDATION {{METRIC}} of `proposed` over seeds{{PRIMARY_SIGN}}. Selection uses validation only.
- Test {{METRIC}} is computed once per trained model and only reported; it is hidden from you during refinement.
- An attempt counts only if the whole project runs to completion (exit code 0) with every condition and every seed.
- At the end the best model is re-evaluated on fresh seeds (`confirm_*` metrics).

## Practical limits
- One full evaluation (3 conditions x 10 seeds) must fit the time budget; a 2-layer model takes seconds per seed.
  More message-passing layers make each seed's temporal subgraph reach most of the database: much slower.
- GPU memory is shared with the LLM server: keep peak memory below ~6 GB (`peak_gb` is printed per run).
- PyTorch Geometric 2.8, PyTorch 2.8, relbench 1.1.0, torch_frame 0.3; no new pip packages.
