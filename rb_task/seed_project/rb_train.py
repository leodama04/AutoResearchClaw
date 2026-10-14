"""Training / evaluation loops (official RelBench protocol).

Protocol (must not be changed):
  * fit on the train table, select the best epoch by the validation metric;
  * evaluate the selected checkpoint on the test table exactly once, for
    reporting only -- the test metric is never used to choose anything.
"""

import copy
import gc
import math
from types import SimpleNamespace
from typing import Dict

import numpy as np
import torch
from torch.nn import BCEWithLogitsLoss, L1Loss
from torch_geometric.seed import seed_everything

from relbench.base import TaskType

import rb_config as C
import rb_model
import rb_model_official


def builder_for(cfg: dict):
    """Baselines always use the frozen official model; `proposed` uses the editable rb_model.py."""
    return rb_model_official.build_model if cfg.get("model_impl") == "official" else rb_model.build_model


def task_setup(task, train_table) -> SimpleNamespace:
    """Loss / tuning metric depending on the task type (as in the official example)."""
    clamp_min = clamp_max = None
    if task.task_type == TaskType.BINARY_CLASSIFICATION:
        return SimpleNamespace(
            out_channels=1,
            loss_fn=BCEWithLogitsLoss(),
            tune_metric="roc_auc",
            higher_is_better=True,
            clamp=(None, None),
        )
    if task.task_type == TaskType.REGRESSION:
        clamp_min, clamp_max = np.percentile(
            train_table.df[task.target_col].to_numpy(), [2, 98]
        )
        return SimpleNamespace(
            out_channels=1,
            loss_fn=L1Loss(),
            tune_metric="mae",
            higher_is_better=False,
            clamp=(clamp_min, clamp_max),
        )
    raise ValueError(f"Unsupported task type {task.task_type}")


def train_epoch(model, loader, optimizer, setup, entity_table, device, max_steps, accum=1):
    """One epoch. With accum > 1 the loader yields micro-batches whose gradients are
    accumulated before every optimiser step (same effective batch size, bounded memory)."""
    model.train()
    loss_accum = count_accum = 0
    steps = 0
    seen = 0
    optimizer.zero_grad()
    for batch in loader:
        batch = batch.to(device)
        pred = model(batch, entity_table)
        pred = pred.view(-1) if pred.size(1) == 1 else pred
        loss = setup.loss_fn(pred.float(), batch[entity_table].y.float())
        (loss / accum).backward()
        loss_accum += loss.detach().item() * pred.size(0)
        count_accum += pred.size(0)
        seen += 1
        if seen % accum == 0:
            optimizer.step()
            optimizer.zero_grad()
            steps += 1
            if steps >= max_steps:
                break
    if seen % accum != 0:  # incomplete last group of micro-batches
        optimizer.step()
        optimizer.zero_grad()
    return loss_accum / max(count_accum, 1)


@torch.no_grad()
def predict(model, loader, setup, task, entity_table, device) -> np.ndarray:
    model.eval()
    preds = []
    for batch in loader:
        batch = batch.to(device)
        pred = model(batch, entity_table)
        if task.task_type == TaskType.REGRESSION:
            pred = torch.clamp(pred, setup.clamp[0], setup.clamp[1])
        if task.task_type == TaskType.BINARY_CLASSIFICATION:
            pred = torch.sigmoid(pred)
        pred = pred.view(-1) if pred.size(1) == 1 else pred
        preds.append(pred.detach().cpu())
    return torch.cat(preds, dim=0).numpy()


def run_one(ctx, loaders: Dict, cfg: dict, seed: int, device, harness) -> dict:
    """Train one model (one condition, one seed). Returns val/test metrics."""
    tc = C.merged_train_cfg(cfg)
    task = ctx.task
    setup = task_setup(task, ctx.tables["train"])
    seed_everything(seed)
    on_cuda = device.type == "cuda"
    if on_cuda:
        torch.cuda.reset_peak_memory_stats()

    model = builder_for(cfg)(
        ctx.data, ctx.col_stats_dict, cfg, out_channels=setup.out_channels
    ).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=float(tc["lr"]), weight_decay=float(tc["weight_decay"])
    )

    try:
        best_val = -math.inf if setup.higher_is_better else math.inf
        best_state = None
        epochs_run = 0
        for epoch in range(1, int(tc["epochs"]) + 1):
            if harness.should_stop():
                break
            train_loss = train_epoch(
                model, loaders["train"], optimizer, setup, ctx.entity_table, device,
                int(tc["max_steps_per_epoch"]), accum=int(loaders.get("_accum", 1)),
            )
            val_pred = predict(model, loaders["val"], setup, task, ctx.entity_table, device)
            val_metrics = task.evaluate(val_pred, ctx.tables["val"])
            val_value = float(val_metrics[setup.tune_metric])
            epochs_run = epoch
            print(f"  epoch={epoch} train_loss={train_loss:.4f} val_{setup.tune_metric}={val_value:.4f}")
            improved = val_value > best_val if setup.higher_is_better else val_value < best_val
            if improved:
                best_val = val_value
                best_state = copy.deepcopy(model.state_dict())

        if best_state is None:
            raise RuntimeError("No epoch completed (time budget exhausted too early)")

        model.load_state_dict(best_state)
        # Test split: evaluated once, for reporting only (never used for selection).
        test_pred = predict(model, loaders["test"], setup, task, ctx.entity_table, device)
        test_metrics = task.evaluate(test_pred)
        peak_gb = torch.cuda.max_memory_allocated() / 1e9 if on_cuda else 0.0
        return {
            "val": float(best_val),
            "test": float(test_metrics[setup.tune_metric]),
            "test_all": {k: float(v) for k, v in test_metrics.items()},
            "tune_metric": setup.tune_metric,
            "higher_is_better": setup.higher_is_better,
            "epochs_run": epochs_run,
            "peak_gpu_gb": float(peak_gb),
        }
    finally:
        # The GPU is shared with the LLM server: release memory between runs.
        del model, optimizer
        gc.collect()
        if on_cuda:
            torch.cuda.empty_cache()
