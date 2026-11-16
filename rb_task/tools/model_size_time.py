#!/usr/bin/env python3
"""Size and training speed of the RelBench models of the thesis (numbers for the context slide).

Run inside the arc-relbench container, from the repo root:

    python3 /app/rb_task/tools/model_size_time.py --tasks driver-top3,driver-dnf --epochs 10

For each task it prints the graph size, the parameters of the official RelBench model
(heterogeneous GraphSAGE) by component, and seconds per training epoch / validation pass for
baseline_graphsage (batch 512) and baseline_tuned (batch 128), mean of epochs 2..N, with peak GPU memory.
It also counts the parameters in the official RelGNN checkpoints in artifacts/relgnn_checkpoints/.
Nothing is written and no model is saved.
"""
import argparse
import glob
import os
import statistics
import sys
import time

sys.path.insert(0, "/app/rb_task/seed_project")
os.environ.setdefault("RB_RECIPE", "tuned")  # so that baseline_tuned exists in rb_config

import torch  # noqa: E402
from torch_geometric.seed import seed_everything  # noqa: E402

import rb_config as C  # noqa: E402
import rb_model_official as M  # noqa: E402
import rb_train as T  # noqa: E402
from rb_data import build_loaders, prepare_data, reference_nodes  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--tasks", default="driver-top3,driver-dnf")
ap.add_argument("--epochs", type=int, default=10)
ap.add_argument("--ckpt-dir", default="/app/artifacts/relgnn_checkpoints")
a = ap.parse_args()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
on_cuda = device.type == "cuda"


def sync():
    if on_cuda:
        torch.cuda.synchronize()


def n_params(module):
    return sum(p.numel() for p in module.parameters())


if on_cuda:
    free, total = torch.cuda.mem_get_info()
    print(f"GPU: {torch.cuda.get_device_name(0)}, free {free / 1e9:.1f} of {total / 1e9:.1f} GB "
          "(other processes on the GPU slow the timings down: note nvidia-smi at the same time)")
else:
    print("GPU not available: timings are on CPU")

for task_name in [t.strip() for t in a.tasks.split(",") if t.strip()]:
    t0 = time.perf_counter()
    ctx = prepare_data(C.DATASET, task_name, C.CACHE_DIR, device)
    data = ctx.data
    n_nodes = sum(int(data[nt].num_nodes) for nt in data.node_types)
    n_edges = sum(int(data[et].edge_index.size(1)) for et in data.edge_types)
    rows = {s: len(ctx.tables[s].df) for s in ("train", "val", "test")}
    print(f"\n=== {C.DATASET} / {task_name}  (graph built in {time.perf_counter() - t0:.0f} s)")
    print(f"graph: {len(data.node_types)} node types, {n_nodes:,} nodes; "
          f"{len(data.edge_types)} edge types, {n_edges:,} edges")
    print(f"examples: train {rows['train']:,}, val {rows['val']:,}, test {rows['test']:,}")

    setup = T.task_setup(ctx.task, ctx.tables["train"])
    ref = reference_nodes(ctx, C.BASELINE)
    for name in ("baseline_graphsage", "baseline_tuned"):
        cfg = C.CONDITIONS[name]
        tc = C.merged_train_cfg(cfg)
        loaders = build_loaders(ctx, cfg, ref)
        seed_everything(0)
        model = M.build_model(data, ctx.col_stats_dict, cfg, setup.out_channels).to(device)
        if name == "baseline_graphsage":
            parts = {k: n_params(getattr(model, k)) for k in ("encoder", "temporal_encoder", "gnn", "head")}
            print(f"official RelBench model (GraphSAGE): {n_params(model):,} parameters  "
                  + "  ".join(f"{k} {v:,}" for k, v in parts.items()))
        opt = torch.optim.Adam(model.parameters(), lr=float(tc["lr"]), weight_decay=float(tc["weight_decay"]))
        if on_cuda:
            torch.cuda.reset_peak_memory_stats()
        tr, va = [], []
        for _ in range(a.epochs):
            sync()
            t1 = time.perf_counter()
            T.train_epoch(model, loaders["train"], opt, setup, ctx.entity_table, device,
                          int(tc["max_steps_per_epoch"]), accum=int(loaders.get("_accum", 1)))
            sync()
            t2 = time.perf_counter()
            T.predict(model, loaders["val"], setup, ctx.task, ctx.entity_table, device)
            sync()
            tr.append(t2 - t1)
            va.append(time.perf_counter() - t2)
        peak = torch.cuda.max_memory_allocated() / 1e9 if on_cuda else 0.0
        steady_tr = tr[1:] or tr
        steady_va = va[1:] or va
        print(f"  {name:19s} batch {int(tc['batch_size']):3d}: training {statistics.mean(steady_tr):.2f} s/epoch "
              f"(first epoch {tr[0]:.2f} s), validation pass {statistics.mean(steady_va):.2f} s, "
              f"{a.epochs} epochs + validation {sum(tr) + sum(va):.1f} s, peak GPU {peak:.2f} GB")
        del model, opt
        if on_cuda:
            torch.cuda.empty_cache()

ckpts = sorted(glob.glob(os.path.join(a.ckpt_dir, "*.pth")))
if ckpts:
    print("\nOfficial RelGNN checkpoints (parameters stored in the file, without normalisation statistics):")
    for p in ckpts:
        sd = torch.load(p, map_location="cpu", weights_only=True)
        n = sum(v.numel() for k, v in sd.items()
                if torch.is_tensor(v) and not any(s in k for s in ("running_mean", "running_var", "num_batches_tracked")))
        print(f"  {os.path.basename(p)}: {n:,}")
else:
    print(f"\n(no RelGNN checkpoints in {a.ckpt_dir}: run it where ./run.sh relgnn-ckpt was run, if you need them)")
