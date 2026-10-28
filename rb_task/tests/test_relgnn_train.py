#!/usr/bin/env python3
"""Test of rb_task/tools/relgnn_train.py on RelBench's FakeDataset (no download of rel-f1 needed).

Checks: the RelGNN conditions are built with the OFFICIAL class from the repository and the authors' configuration
(the run008 variant only changes layers/heads and uses our loader), the baselines keep the frozen RDL model, every
condition is trained by rb_train.run_one on the same seeds with the requested epochs, updates per epoch are counted,
paired differences against baseline_tuned are computed and the summary is written.
Needs the RelGNN repository: RELGNN_REPO=<clone> (default: git clone into /tmp/RelGNN).
"""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools"))

import torch  # noqa: E402

import relgnn_train as T  # noqa: E402
import smoke_fake as S  # noqa: E402  (build_ctx, _FullGraphLoader, fake_loaders; puts the seed project on sys.path)
import rb_config as C  # noqa: E402
import rb_data  # noqa: E402
import rb_model_official  # noqa: E402
import rb_train  # noqa: E402

repo = os.environ.get("RELGNN_REPO", "")
if not repo:
    repo = "/tmp/RelGNN"
    if not (Path(repo) / "examples" / "relgnn_model.py").is_file():
        subprocess.run(["git", "clone", "-q", "--depth", "1", "https://github.com/snap-stanford/RelGNN", repo], check=True)
examples = T.E.find_repo(repo)
RelGNN_Model, get_atomic_routes, get_configs = T.E.import_relgnn(examples)

# the authors' configuration for driver-top3 is what the tool will use on rel-f1
mc, lc = get_configs("rel-f1", "driver-top3")
conds = T.conditions(C, mc, lc, 10, 0.005, {"authors", "run008"}, True)
assert list(conds) == ["baseline_graphsage", "baseline_tuned", "relgnn_authors", "relgnn_run008"], list(conds)
ra, r8 = conds["relgnn_authors"], conds["relgnn_run008"]
assert ra["cfg"]["relgnn_model"] == mc and ra["loader"] == lc and ra["cfg"]["batch_size"] == 256
assert r8["cfg"]["relgnn_model"] == {**mc, "num_model_layers": 2, "num_heads": 4} and r8["loader"] == "ours"
assert r8["cfg"]["batch_size"] == 128 and r8["cfg"]["num_layers"] == 2 and rb_data.fanouts_for(r8["cfg"]) == [128, 64]
assert conds["baseline_tuned"]["cfg"]["batch_size"] == 128 and conds["baseline_graphsage"]["cfg"].get("batch_size", 512) == 512
assert all(c["cfg"]["epochs"] == 10 and c["cfg"]["lr"] == 0.005 for c in conds.values())
print("OK 1: condizioni con la configurazione degli autori (modello e loader) e la variante di RUN-008")

build = T.relgnn_builder(RelGNN_Model, get_atomic_routes)
T.install_builder(rb_train, build)
assert rb_train.builder_for({"model_impl": "relgnn"}) is build
assert rb_train.builder_for(C.BASELINE) is rb_model_official.build_model
assert rb_train.builder_for(C.BASELINE_TUNED) is rb_model_official.build_model
ctx = S.build_ctx()
small = {"num_model_layers": 1, "channels": 16, "aggr": "sum", "num_heads": 2, "simplified_MP": True}
m1 = build(ctx.data, ctx.col_stats_dict, {"relgnn_model": small}, 1)
m2 = build(ctx.data, ctx.col_stats_dict, {"relgnn_model": {**small, **T.RUN008_MODEL}}, 1)
assert type(m1).__name__ == "RelGNN_Model" and type(m1).__module__ == "relgnn_model"
n1, n2 = (sum(p.numel() for p in m.parameters()) for m in (m1, m2))
assert n2 > n1, (n1, n2)
print(f"OK 2: RelGNN costruito con la classe ufficiale ({n1:,} parametri; 2 strati e 4 teste: {n2:,}); baseline = modello RDL congelato")

small_lc = {**lc, "batch_size": 64}
conds = T.conditions(C, small, small_lc, 2, 0.005, {"authors", "run008"}, True)
ours = lambda ctx_, cfg: {**S.fake_loaders(ctx_, cfg), "_accum": 1}  # noqa: E731
authors = lambda ctx_, lconf: {**{s: S._FullGraphLoader(ctx_, ctx_.table_inputs[s], int(lconf["batch_size"]), s == "train")  # noqa: E731
                                  for s in ("train", "val", "test")}, "_accum": 1}
logs = []
rows = T.run_task(ctx, conds, [100, 101, 102], torch.device("cpu"), rb_train, rb_data, C, ours_factory=ours,
                  authors_factory=authors, log=logs.append)
assert len(rows) == 12 and {r["seed"] for r in rows} == {100, 101, 102}, len(rows)
assert all(r["epochs"] == 2 and r["epochs_run"] == 2 and 0.0 <= r["test"] <= 1.0 for r in rows)
n_train = len(ctx.table_inputs["train"].nodes[1])
upe = {r["condition"]: r["updates_per_epoch"] for r in rows}
assert upe["relgnn_authors"] == -(-n_train // 64) and upe["baseline_tuned"] == -(-n_train // 128), upe
print(f"OK 3: 4 condizioni x 3 semi allenate da rb_train.run_one, 2 epoche; aggiornamenti per epoca {upe}")

s = T.summarize(rows)
assert set(s["conditions"]) == set(conds) and s["metric"] == "roc_auc" and s["higher"] is True
pa = s["paired"]["relgnn_authors-baseline_tuned:test"]
assert pa and pa["n"] == 3, pa
va = {r["seed"]: r["test"] for r in rows if r["condition"] == "relgnn_authors"}
vb = {r["seed"]: r["test"] for r in rows if r["condition"] == "baseline_tuned"}
assert abs(pa["mean_diff"] - sum(va[k] - vb[k] for k in va) / 3) < 1e-12
assert "baseline_tuned-baseline_tuned:test" not in s["paired"]
md = T.render("rel-f1", [{"task": "driver-top3", "model_config": mc, "loader_config": lc, "by_epochs": [(2, s)]},
                         {"task": "driver-dnf", "error": "boom"}],
              SimpleNamespace(seed_offset=100, n_seeds=3, lr=0.005), str(examples))
assert "configurazione degli autori" in md and "0.8585" in md and "0.8569" in md and "ERRORE: boom" in md
assert sum(1 for ln in md.splitlines() if ln.startswith("| 2 | ")) == 4, md
assert "val (roc_auc)" in md and "modello `None`" not in md, md
print("OK 4: differenze appaiate contro baseline_tuned e riepilogo con i riferimenti (paper, checkpoint di RUN-009)")
print("RELGNN TRAIN TEST PASSED")
