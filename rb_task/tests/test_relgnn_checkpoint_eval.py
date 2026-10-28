#!/usr/bin/env python3
"""Test of rb_task/tools/relgnn_checkpoint_eval.py on RelBench's FakeDataset (no download of rel-f1 needed).

Builds the OFFICIAL RelGNN model from the repository code, saves its weights as a "checkpoint", and checks that the
tool reloads them strictly, evaluates validation and test with task.evaluate and reports a mismatching checkpoint
instead of hiding it. Needs the RelGNN repository: RELGNN_REPO=<clone> (default: git clone into /tmp/RelGNN).
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools"))

import torch  # noqa: E402

import relgnn_checkpoint_eval as E  # noqa: E402
import smoke_fake as S  # noqa: E402  (build_ctx, _FullGraphLoader)

repo = os.environ.get("RELGNN_REPO", "")
if not repo:
    repo = "/tmp/RelGNN"
    if not (Path(repo) / "examples" / "relgnn_model.py").is_file():
        subprocess.run(["git", "clone", "-q", "--depth", "1", "https://github.com/snap-stanford/RelGNN", repo], check=True)
examples = E.find_repo(repo)
RelGNN_Model, get_atomic_routes, get_configs = E.import_relgnn(examples)
mc, lc = get_configs("rel-f1", "driver-top3")
assert mc["num_model_layers"] == 1 and mc["num_heads"] == 2 and mc.get("simplified_MP") is True and lc["batch_size"] == 256

ctx = S.build_ctx()
cfg = {"num_model_layers": 1, "channels": 16, "aggr": "sum", "num_heads": 2, "simplified_MP": True}
torch.manual_seed(0)
model = E.build_model(RelGNN_Model, get_atomic_routes, ctx, cfg, 1)
tmp = Path(tempfile.mkdtemp())
ckpt = tmp / "fake.pth"
torch.save(model.state_dict(), ckpt)

if S.HAS_PYG_LIB:
    factory = None
else:  # maintainer's sandbox without pyg-lib: whole-graph batches, as in smoke_fake
    factory = lambda split: S._FullGraphLoader(ctx, ctx.table_inputs[split], 64, False)  # noqa: E731
res = E.evaluate_checkpoint(ctx, RelGNN_Model, get_atomic_routes, cfg, lc, ckpt, torch.device("cpu"), seeds=(0, 1),
                            loader_factory=factory)
assert "error" not in res and res["metric"] == "roc_auc" and len(res["val"]) == 2 and len(res["test"]) == 2, res
assert 0.0 <= res["val_mean"] <= 1.0 and 0.0 <= res["test_mean"] <= 1.0, res
print(f"OK 1: checkpoint ricaricato in modo stretto, val {res['val_mean']:.3f} test {res['test_mean']:.3f} ({res['params']:,} parametri)")

# checkpoint saved with torch_frame 0.2.x: no `fill_values` buffers (the case of the authors' checkpoints)
state = {k: v for k, v in model.state_dict().items() if not k.endswith(".fill_values")}
n_fill = len(model.state_dict()) - len(state)
assert n_fill > 0, "the fake dataset should have timestamp columns"
old_ckpt = tmp / "old_torch_frame.pth"
torch.save(state, old_ckpt)
res_old = E.evaluate_checkpoint(ctx, RelGNN_Model, get_atomic_routes, cfg, lc, old_ckpt, torch.device("cpu"), seeds=(0, 1),
                                loader_factory=factory)
assert "error" not in res_old and res_old["missing_filled_from_stats"] == n_fill, res_old.get("error")
assert abs(res_old["test_mean"] - res["test_mean"]) < 1e-6, (res_old["test_mean"], res["test_mean"])
print(f"OK 1b: checkpoint senza i {n_fill} buffer `fill_values` (torch_frame 0.2.x) caricato, stesse predizioni")

bad = E.evaluate_checkpoint(ctx, RelGNN_Model, get_atomic_routes, {**cfg, "num_model_layers": 2}, lc, ckpt,
                            torch.device("cpu"), seeds=(0,), loader_factory=factory)
assert "error" in bad and bad["missing_keys"] and not bad["val"], bad.get("error")
print(f"OK 2: un checkpoint che non corrisponde al modello viene segnalato ({bad['error']})")
print("RELGNN CHECKPOINT EVAL TEST PASSED")
