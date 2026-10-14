---
name: relbench-gnn-code
description: How to change the GNN of this RelBench project (rb_model.py) correctly. Use when writing or repairing model code for the RelBench rel-f1 experiments.
metadata:
  category: domain
  trigger-keywords: "relbench,gnn,graph neural network,pytorch geometric,heterogeneous,message passing,rb_model,hetero"
  applicable-stages: "9,10,12,13"
  priority: "1"
  version: "1.0"
  author: relbench-kit
  references: "relbench 1.1.0 examples/model.py; PyG HeteroConv docs"
---
## Project contract
- Editable: `rb_model.py` (used ONLY by `proposed`), new module files you create, and in `rb_config.py` only
  `PROPOSED_OVERRIDES` (dict) and `PROPOSED_SOURCE` (string). Everything else is restored automatically; the
  baselines use the frozen `rb_model_official.py`.
- `build_model(data, col_stats_dict, cfg, out_channels)` must return an `nn.Module` whose
  `forward(batch, entity_table)` returns logits of shape `[num_seed_nodes, out_channels]`.
- A new component is OFF unless activated: read a new value/key from `cfg` (e.g. `cfg.get("gnn_type") == "<your option>"`)
  and set it in `PROPOSED_OVERRIDES`. A change that leaves `proposed` identical to `baseline_tuned` is rejected.
- Set `PROPOSED_SOURCE = "K<n>: <component>"` with the implementation card you are using.

## The batch (temporal NeighborLoader, disjoint subgraph per seed)
- `batch.tf_dict` (PyTorch Frame tensors per table) -> `HeteroEncoder` -> `x_dict[node_type]` of shape [N_t, C].
- `batch[entity_table].seed_time`, `batch.time_dict`, `batch.batch_dict` -> relative-time encoding.
- `batch.edge_index_dict[(src, rel, dst)]` = [2, E]; edges exist in both directions (`rev_` relations).
- Seed nodes are the FIRST `seed_time.size(0)` rows of `x_dict[entity_table]`.
- Node types without incoming edges disappear from the output of `HeteroConv`; keep the previous value for them.

## PyG patterns that work here
- One conv per edge type: `HeteroConv({et: Conv((C, C), C) for et in edge_types}, aggr="sum")`; convs must accept
  bipartite inputs `(x_src, x_dst)` (SAGEConv, GATv2Conv(add_self_loops=False), TransformerConv, GINConv, ResGatedGraphConv).
- Per-node-type normalisation: `ModuleDict({nt: LayerNorm(C, mode="node")})`.
- Create every new parameter inside modules built in `__init__` (never in `forward`) and implement `reset_parameters`.
- Memory: a 2-layer model peaks at about 1-4 GB; extra layers multiply the sampled subgraph (rb_data handles micro-batching).
- The code validator rejects any call named `eval`, `exec` or `compile`: use `model.train(False)` instead of `model.eval()`.

## Errors seen in earlier runs (avoid them)
- `GATv2Conv(..., add_self_loops=True)` on edges between DIFFERENT node types raises a ValueError: always pass
  `add_self_loops=False` (also for GATConv, TransformerConv has no such argument).
- Do not pass keyword arguments a conv does not accept (`add_self_loops` to SAGEConv/GINConv, `attn_drop` to GATv2Conv).
- `HeteroGraphSAGE` lives in `relbench.modeling.nn`, not in `torch_geometric.nn`; `BatchNorm`/`LayerNorm` for graphs are in
  `torch_geometric.nn`, not `torch.nn`.
- Sampled batches have no `n_id` on node stores; positions/hops must be computed from `edge_index_dict` and `batch_dict`.
- `torch.nn.Embedding` needs a LongTensor index, not a Python int; check shapes when concatenating per-type features.
- Always return the COMPLETE rb_model.py: `build_model` must remain defined (three attempts lost it by returning a fragment).
