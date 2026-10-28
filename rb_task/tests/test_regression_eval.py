#!/usr/bin/env python3
"""Regression tasks (driver-position: MAE) with the installed scikit-learn.

relbench 1.1.0 computes `rmse` with mean_squared_error(squared=False), removed in scikit-learn 1.6: every regression
evaluation crashed ("got an unexpected keyword argument 'squared'"), first seen with `./run.sh relgnn-ckpt`.
Checks that rb_train.evaluate_task returns r2 / mae / rmse (rmse = sqrt(mse)) and that the seed project trains and
evaluates a regression task end to end. Uses RelBench's FakeDataset (no download).
"""
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from relbench.modeling.graph import get_node_train_table_input  # noqa: E402
from relbench.tasks.amazon import UserLTVTask  # noqa: E402

import smoke_fake as S  # noqa: E402
import rb_config as C  # noqa: E402
import rb_data  # noqa: E402
import rb_train  # noqa: E402

ctx = S.build_ctx()
task = UserLTVTask(ctx.dataset)
tables = {s: task.get_table(s) for s in ("train", "val", "test")}
ctx = rb_data.DataContext(dataset=ctx.dataset, task=task, data=ctx.data, col_stats_dict=ctx.col_stats_dict, tables=tables,
                          table_inputs={s: get_node_train_table_input(tables[s], task) for s in tables},
                          entity_table=task.entity_table)
target = tables["val"].df[task.target_col].to_numpy()
pred = target + np.random.default_rng(0).normal(0, 1.0, size=len(target))
m = rb_train.evaluate_task(task, pred, tables["val"])
assert set(m) == {"r2", "mae", "rmse"}, m
assert abs(m["rmse"] - math.sqrt(float(np.mean((target - pred) ** 2)))) < 1e-9, m
print(f"OK 1: metriche di regressione {sorted(m)} (rmse senza squared=False)")

cfg = {**C.BASELINE, "epochs": 2, "batch_size": 32, "num_neighbors": 16}
loaders = rb_data.build_loaders(ctx, cfg) if S.HAS_PYG_LIB else S.fake_loaders(ctx, cfg)
res = rb_train.run_one(ctx, loaders, cfg, seed=0, device=torch.device("cpu"), harness=S._Harness())
assert res["tune_metric"] == "mae" and res["higher_is_better"] is False and math.isfinite(res["test"]), res
print(f"OK 2: run_one su un task di regressione: val MAE {res['val']:.3f}, test MAE {res['test']:.3f}")
print("REGRESSION EVAL TEST PASSED")
