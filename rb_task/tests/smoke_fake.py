#!/usr/bin/env python3
"""Smoke test of the seed project on RelBench's FakeDataset (no download needed).

Checks that, with the installed stack, every GNN type / option used by the seed
can be built, trained for a few steps, evaluated with `task.evaluate`, and that
`run_one` + the temporal NeighborLoader work end to end.

Run in the container:   ./run.sh smoke
"""
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = Path(os.environ.get("RB_SEED_DIR", HERE.parent / "seed_project"))
sys.path.insert(0, str(SEED))

import numpy as np
import torch
from torch_frame.config.text_embedder import TextEmbedderConfig
from torch_frame.testing.text_embedder import HashTextEmbedder

from relbench.datasets.fake import FakeDataset
from relbench.modeling.graph import get_node_train_table_input, make_pkey_fkey_graph
from relbench.modeling.utils import get_stype_proposal
from relbench.tasks.amazon import UserChurnTask

import rb_config as C
import rb_data
import rb_model
import rb_train

try:
    import pyg_lib  # noqa: F401

    HAS_PYG_LIB = True
except Exception:  # noqa: BLE001
    HAS_PYG_LIB = False

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"device={device} torch={torch.__version__} pyg_lib={HAS_PYG_LIB}")


class _Harness:
    def should_stop(self):
        return False


def build_ctx():
    dataset = FakeDataset()
    task = UserChurnTask(dataset)
    db = dataset.get_db()
    data, col_stats_dict = make_pkey_fkey_graph(
        db,
        get_stype_proposal(db),
        text_embedder_cfg=TextEmbedderConfig(HashTextEmbedder(8), batch_size=None),
    )
    tables, table_inputs = {}, {}
    for split in ["train", "val", "test"]:
        tables[split] = task.get_table(split)
        table_inputs[split] = get_node_train_table_input(tables[split], task)
    return rb_data.DataContext(
        dataset=dataset, task=task, data=data, col_stats_dict=col_stats_dict,
        tables=tables, table_inputs=table_inputs, entity_table=task.entity_table,
    )


class _FullGraphLoader:
    """Fallback when pyg-lib is missing (only used by the maintainer's sandbox):
    one batch per chunk of seed nodes, containing the whole graph with the seed
    nodes first, as NeighborLoader would produce."""

    def __init__(self, ctx, table_input, batch_size, shuffle):
        self.ctx, self.ti, self.bs, self.shuffle = ctx, table_input, batch_size, shuffle

    def __iter__(self):
        n = len(self.ti.nodes[1])
        order = torch.randperm(n) if self.shuffle else torch.arange(n)
        et = self.ti.nodes[0]
        data = self.ctx.data
        for i in range(0, n, self.bs):
            idx = order[i : i + self.bs]
            seeds = self.ti.nodes[1][idx]
            rest = torch.tensor(
                [j for j in range(data[et].num_nodes) if j not in set(seeds.tolist())],
                dtype=torch.long,
            )
            subset = {nt: torch.arange(data[nt].num_nodes) for nt in data.node_types}
            subset[et] = torch.cat([seeds, rest])
            batch = data.subgraph(subset)
            batch[et].seed_time = self.ti.time[idx]
            for nt in batch.node_types:
                batch[nt].batch = torch.zeros(batch[nt].num_nodes, dtype=torch.long)
                batch[nt].num_sampled_nodes = [batch[nt].num_nodes]
            for et_ in batch.edge_types:
                batch[et_].num_sampled_edges = [batch[et_].num_edges]
            if self.ti.transform is not None:
                batch = self.ti.transform(batch) if _transform_ok(batch, self.ti, idx) else batch
            yield batch

    def __len__(self):
        return (len(self.ti.nodes[1]) + self.bs - 1) // self.bs


def _transform_ok(batch, ti, idx):
    # AttachTargetTransform indexes target by batch.input_id; emulate it.
    et = ti.nodes[0]
    batch[et].y = ti.target[idx]
    return False


def fake_loaders(ctx, cfg):
    tc = C.merged_train_cfg(cfg)
    return {
        s: _FullGraphLoader(ctx, ctx.table_inputs[s], int(tc["batch_size"]), s == "train")
        for s in ["train", "val", "test"]
    }


def check_model_variants(ctx):
    base = dict(C.BASELINE)
    variants = {
        "baseline_sage": base,
        "sage+drop+res": {**base, "dropout": 0.2, "residual": True, "num_layers": 3},
        "resgated": {**base, "gnn_type": "resgated"},
        "gatv2": {**base, "gnn_type": "gatv2", "heads": 2},
        "gin": {**base, "gnn_type": "gin"},
        "transformer": {**base, "gnn_type": "transformer", "heads": 2},
        "layers4_ch64": {**base, "num_layers": 4, "channels": 64},
        "jk_cat+res": {**base, "gnn_type": "gatv2", "jk": "cat", "residual": True, "num_layers": 3},
        "enc6_w64_d0": {**base, "enc_layers": 6, "enc_width": 64, "enc_dropout": 0.0},
        "no_time_enc": {**base, "time_encoding": False, "head_layers": 2, "norm": "layer_norm"},
    }
    setup = rb_train.task_setup(ctx.task, ctx.tables["train"])
    h = _Harness()
    ref = 0.0
    if HAS_PYG_LIB:
        ref = rb_data.reference_nodes(
            ctx, {**base, "epochs": 2, "batch_size": 32, "num_neighbors": 16})
    for name, cfg in variants.items():
        cfg = {**cfg, "epochs": 2, "max_steps_per_epoch": 5, "batch_size": 32,
               "num_neighbors": 16}
        if HAS_PYG_LIB:
            # "layers4_ch64": budget ridotto -> forza i micro-batch col NeighborLoader vero
            loaders = rb_data.build_loaders(ctx, cfg, ref * (0.3 if name == "layers4_ch64" else 1.0))
        else:
            loaders = fake_loaders(ctx, cfg)
        t0 = time.time()
        res = rb_train.run_one(ctx, loaders, cfg, seed=0, device=device, harness=h)
        n_params = sum(
            p.numel() for p in rb_model.build_model(ctx.data, ctx.col_stats_dict, cfg, 1).parameters()
        )
        assert np.isfinite(res["val"]) and np.isfinite(res["test"]), name
        print(f"OK {name:16s} params={n_params:>8d} val={res['val']:.3f} "
              f"test={res['test']:.3f} ({time.time() - t0:.1f}s)")
    assert setup.tune_metric == "roc_auc"


if __name__ == "__main__":
    ctx = build_ctx()
    print("graph:", {nt: ctx.data[nt].num_nodes for nt in ctx.data.node_types})
    check_model_variants(ctx)
    print("SMOKE TEST PASSED")
