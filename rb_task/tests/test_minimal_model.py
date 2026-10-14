#!/usr/bin/env python3
"""rb_model_minimal.py (starting model of code mode) must compute EXACTLY the official model of the baselines,
and must not offer alternative operators."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "seed_project"), str(HERE)]
import torch
from torch_geometric.seed import seed_everything
import smoke_fake as SF
import rb_config as C
import rb_model_minimal as M
import rb_model_official as O

ctx = SF.build_ctx()
batch = next(iter(SF._FullGraphLoader(ctx, ctx.table_inputs["val"], 16, False)))
cfg = {**C.BASELINE, **C.TUNED_TRAIN}
outs = []
for build in (O.build_model, M.build_model):
    seed_everything(0)
    m = build(ctx.data, ctx.col_stats_dict, cfg, 1)
    m.train(False)
    with torch.no_grad():
        outs.append((sum(p.numel() for p in m.parameters()), m(batch, ctx.entity_table)))
assert outs[0][0] == outs[1][0], (outs[0][0], outs[1][0])
assert torch.allclose(outs[0][1], outs[1][1], atol=1e-6), "il modello minimo deve coincidere con quello ufficiale"
src = (HERE.parent / "seed_project" / "rb_model_minimal.py").read_text()
for op in ("GATv2Conv", "GINConv", "TransformerConv", "ResGatedGraphConv", "GNN_TYPES", "jk", "enc_layers"):
    assert op not in src, f"il modello minimo non deve offrire {op}"
seed_everything(0)
m2 = M.build_model(ctx.data, ctx.col_stats_dict, {**cfg, "gnn_type": "gatv2"}, 1)
print(f"OK: modello minimo identico all'ufficiale ({outs[0][0]:,} parametri, stesse uscite); nessun operatore alternativo")
print("MINIMAL MODEL TESTS PASSED")
