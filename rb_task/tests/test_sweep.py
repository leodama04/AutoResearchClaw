#!/usr/bin/env python3
"""Offline test of the sweep tool on RelBench's FakeDataset."""
import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "tools"), str(HERE.parent / "seed_project"), str(HERE)]
import torch
import numpy as np
import rb_data
import smoke_fake as SF
import sweep as W

assert abs(W.spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1) < 1e-9
assert abs(W.spearman([1, 2, 3, 4], [4, 3, 2, 1]) + 1) < 1e-9
cfgs = W.sweep_configs(deep=True)
assert "baseline (official)" in cfgs and "3 layers" in cfgs and len(cfgs) == 15, len(cfgs)
arch = W.sweep_configs(deep=True, mode="arch")
assert list(arch)[0] == "baseline (fixed recipe)" and "layers=3" in arch and len(arch) == 15, len(arch)
assert all(c["batch_size"] == 128 for c in arch.values()), "la ricetta tuned deve essere fissa in modalita' arch"
assert W.sweep_configs(mode="arch", recipe={"batch_size": 256})["gin"]["batch_size"] == 256
lo, hi = W.rho_ci(0.16, 14); assert -0.5 < lo < -0.3 and 0.55 < hi < 0.7, (lo, hi)
assert "INCONCLUSIVE" in W.verdict(0.16, lo, hi) and "reasonably" in W.verdict(0.74, 0.29 + 0.02, 0.92) and "WEAK" in W.verdict(0.0, -0.3, 0.25)
assert cfgs["baseline (official)"] == dict(__import__("rb_config").BASELINE)
print("OK 1: spearman + elenco configurazioni")

ctx = SF.build_ctx()
rb_data._make_loader = lambda c, fan, split, bs, tc, shuffle: SF._FullGraphLoader(c, c.table_inputs[split], bs, shuffle)
small = {k: {**v, "epochs": 2, "max_steps_per_epoch": 4, "batch_size": 32, "num_neighbors": 16} for k, v in list(cfgs.items())[:4]}
logs = []
rows = W.run_sweep(ctx, small, [0, 1], 0.0, torch.device("cpu"), log=logs.append)
assert len(rows) == 4 and all(len(r["val"]) == 2 for r in rows) and len(logs) == 4
out = W.report(rows)
assert -1 <= out["spearman_val_test"] <= 1
print("OK 2: run_sweep + report su dati finti, rho =", round(out["spearman_val_test"], 2))
# regola di disaccordo e correlazione senza le config in disaccordo (dati sintetici)
def row(name, v, t, sd=0.02):
    return {"name": name, "val_mean": v, "val_std": sd, "test_mean": t, "test_std": sd, "val": [v] * 5, "test": [t] * 5}
syn = [row("ref", .75, .78), row("good", .85, .81), row("res", .68, .80), row("neutral", .76, .785),
       row("a", .74, .77), row("b", .78, .79), row("c", .72, .76), row("d", .79, .80)]
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rep = W.report(syn)
assert rep["disagree"] == ["res"], rep["disagree"]
assert rep["spearman_without_disagree"] is not None and "Spearman without them" in buf.getvalue()
print("OK 3: regola di disaccordo (residual-like segnalato, il vincitore coerente no)")
print("SWEEP TEST PASSED")
