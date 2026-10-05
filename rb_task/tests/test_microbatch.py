#!/usr/bin/env python3
"""Tests of the memory control: micro-batch planning, gradient accumulation, node counting."""
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "seed_project"), str(HERE)]

import torch

import rb_config as C
import rb_data
import rb_train

# 1) pianificazione dei micro-batch (funzione pura)
p = rb_data.plan_micro_batches
assert p(1000, 1000, 512) == (512, 1)            # come il baseline -> nessun frazionamento
assert p(1040, 1000, 512) == (512, 1)            # entro la tolleranza del 5%
assert p(6300, 1000, 512) == (74, 7), p(6300, 1000, 512)
assert p(10**9, 1000, 512) == (8, 64), p(10**9, 1000, 512)   # minimo 8 semi per micro-batch
assert p(5000, 0, 512) == (512, 1)               # nessun budget -> disattivato
micro, acc = p(6300, 1000, 512)
assert micro * acc >= 512
print("OK 1: plan_micro_batches")

# 2) accumulo del gradiente == un solo batch grande (stessa media), meta' degli step
class B:
    def __init__(self, x, y): self.x, self.y = x, y
    def to(self, d): return self
    def __getitem__(self, k): return self
class M(torch.nn.Module):
    def __init__(self): super().__init__(); self.l = torch.nn.Linear(3, 1)
    def forward(self, b, et): return self.l(b.x)

torch.manual_seed(0)
x = torch.randn(8, 3); y = (torch.rand(8) > 0.5).float()
setup = SimpleNamespace(loss_fn=torch.nn.BCEWithLogitsLoss())

def run(batches, accum):
    torch.manual_seed(1); m = M(); o = torch.optim.SGD(m.parameters(), lr=0.1)
    steps = []
    orig = o.step
    o.step = lambda *a, **k: (steps.append(1), orig(*a, **k))[1]
    loss = rb_train.train_epoch(m, batches, o, setup, "e", torch.device("cpu"), 100, accum=accum)
    return m.l.weight.detach().clone(), len(steps), loss

w_big, s_big, _ = run([B(x, y)], 1)
w_acc, s_acc, _ = run([B(x[:4], y[:4]), B(x[4:], y[4:])], 2)
assert s_big == 1 and s_acc == 1, (s_big, s_acc)
assert torch.allclose(w_big, w_acc, atol=1e-6), (w_big, w_acc)
w_two, s_two, _ = run([B(x[:4], y[:4]), B(x[4:], y[4:])], 1)
assert s_two == 2                                    # accum=1 -> uno step per batch (comportamento originale)
w_odd, s_odd, _ = run([B(x[:3], y[:3]), B(x[3:6], y[3:6]), B(x[6:], y[6:])], 2)
assert s_odd == 2                                    # gruppo incompleto: step finale comunque eseguito
print("OK 2: gradient accumulation (equivalente al batch grande, step dimezzati, gruppo incompleto gestito)")

# 3) conteggio nodi + build_loaders con loader finti (senza pyg-lib)
import smoke_fake as SF
ctx = SF.build_ctx()
rb_data._make_loader = lambda ctx_, fan, split, bs, tc, shuffle: SF._FullGraphLoader(ctx_, ctx_.table_inputs[split], bs, shuffle)
cfg = {**C.BASELINE, "batch_size": 32, "num_neighbors": 16}
npb = rb_data.mean_nodes_per_batch(ctx, cfg)
assert npb > 0
ld = rb_data.build_loaders(ctx, cfg, ref_nodes=0.0)
assert ld["_accum"] == 1
ld = rb_data.build_loaders(ctx, cfg, ref_nodes=npb / 4)
assert ld["_accum"] > 1, ld["_accum"]
first = next(iter(ld["train"]))
assert first["customer"].seed_time.numel() < 32
print(f"OK 3: nodes/batch={npb:.0f}; con budget/4 -> accum={ld['_accum']}, micro-batch={first['customer'].seed_time.numel()}")

# 4) run_one end-to-end con accumulo
class H:
    def should_stop(self): return False
cfg2 = {**cfg, "epochs": 2, "max_steps_per_epoch": 5}
res = rb_train.run_one(ctx, ld, cfg2, 0, torch.device("cpu"), H())
assert 0 <= res["val"] <= 1 and 0 <= res["test"] <= 1
print("OK 4: run_one con micro-batch ->", {k: round(v, 3) for k, v in res.items() if k in ("val", "test")})
print("MICROBATCH TESTS PASSED")
