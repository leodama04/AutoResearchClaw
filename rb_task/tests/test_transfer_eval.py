#!/usr/bin/env python3
"""Test of rb_task/tools/transfer_eval.py with a toy project (no rel-f1 data needed).

The toy main.py has the same interface as the seed project (rb_config CONDITIONS, RB_* variables, per-seed results via
the harness). Checks: the project is run unchanged on each task, seeds start at the offset, --epochs reaches every
condition, means and paired differences are right (also for an error metric where lower is better), errors are reported.
Run from the repo root (needs researchclaw/experiment/harness_template.py).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "tools" / "transfer_eval.py"

CFG = '''import os
TASK = os.environ.get("RB_TASK", "driver-top3")
SEED_OFFSET = int(os.environ.get("RB_SEED_OFFSET", "0"))
N_SEEDS = int(os.environ.get("RB_N_SEEDS", "10"))
SEEDS = [SEED_OFFSET + i for i in range(N_SEEDS)]
RECIPE = os.environ.get("RB_RECIPE", "official")
BASELINE = {"gnn_type": "sage", "epochs": 10, "batch_size": 512}
PROPOSED_OVERRIDES = {'gnn_type': 'toy_better'}
PROPOSED_SOURCE = 'K1: toy'
BASELINE_TUNED = {**BASELINE, "batch_size": 128}
CONDITIONS = {"baseline_graphsage": BASELINE, "baseline_tuned": BASELINE_TUNED,
              "proposed": {**BASELINE_TUNED, **PROPOSED_OVERRIDES}} if RECIPE == "tuned" else {"baseline_graphsage": BASELINE}
'''
MAIN = '''import experiment_harness
import rb_config as C
h = experiment_harness.get_harness(time_budget=60)
regression = C.TASK == "driver-position"
for seed in C.SEEDS:
    for name, cfg in C.CONDITIONS.items():
        v = 0.70 + 0.05 * (cfg["gnn_type"] == "toy_better") + 0.001 * (seed % 7) + 0.0001 * cfg["epochs"]
        if regression:
            v = 4.0 - (v - 0.7)
        h.log_result({"condition": name, "seed": seed, "val": v, "test": v - 0.01, "epochs": cfg["epochs"],
                      "tune_metric": "mae" if regression else "roc_auc", "higher_is_better": not regression})
h.report_metric("primary_metric", 0.75)
h.finalize()
'''
tmp = Path(tempfile.mkdtemp())
proj = tmp / "run" / "stage-13" / "experiment_final"
proj.mkdir(parents=True)
(proj / "rb_config.py").write_text(CFG)
(proj / "main.py").write_text(MAIN)
out = tmp / "out"
r = subprocess.run([sys.executable, str(TOOL), "--projects", str(tmp / "run"), "--tasks", "driver-dnf,driver-position",
                    "--epochs", "30", "--n-seeds", "5", "--infra", "run", "--out", str(out)], capture_output=True, text=True)
print(r.stdout[-1500:], r.stderr[-1500:])
assert r.returncode == 0, r.returncode
rows = json.loads((out / "summary.json").read_text())
assert [x["task"] for x in rows] == ["driver-dnf", "driver-position"] and rows[0]["project"] == "run/stage-13"
res = json.loads((out / "run__stage-13__driver-dnf" / "results.json").read_text())["results"]
assert sorted({x["seed"] for x in res}) == [100, 101, 102, 103, 104] and all(x["epochs"] == 30 for x in res)
d = rows[0]["paired"]["proposed-baseline_tuned:test"]
assert abs(d["mean_diff"] - 0.05) < 1e-9 and d["seeds_better"] == 5, d
d2 = rows[1]["paired"]["proposed-baseline_tuned:test"]
assert d2["mean_diff"] < 0 and d2["seeds_better"] == 5 and rows[1]["higher"] is False, d2   # lower MAE = better
assert "'K1: toy'" in rows[0]["source"] and "toy_better" in rows[0]["overrides"]
md = (out / "summary.md").read_text()
assert "driver-position" in md and "più basso è meglio" in md and "30 epoche" in md
print("OK 1: progetto eseguito invariato su ogni task, semi 100+, epoche uguali per tutte le condizioni, differenze appaiate giuste (anche MAE)")
(proj / "main.py").write_text("raise SystemExit(4)\n")
r2 = subprocess.run([sys.executable, str(TOOL), "--projects", str(proj), "--tasks", "driver-dnf", "--infra", "run",
                     "--out", str(tmp / "o2")],
                    capture_output=True, text=True)
assert r2.returncode == 1 and "ERRORE" in (tmp / "o2" / "summary.md").read_text()
print("OK 2: un progetto che non produce risultati viene segnalato")
# --infra current (default): the protected files come from the current kit, the model stays the run's
(proj / "rb_train.py").write_text("# old rb_train of the run\n")
(proj / "rb_model.py").write_text("# the run's model\n")
subprocess.run([sys.executable, str(TOOL), "--projects", str(proj), "--tasks", "driver-dnf", "--n-seeds", "3",
                "--out", str(tmp / "o3")], capture_output=True, text=True, timeout=600)
work = next((tmp / "o3").glob("*__driver-dnf")) / "project"
seed = HERE.parent / "seed_project"
assert (work / "rb_train.py").read_text() == (seed / "rb_train.py").read_text()
assert (work / "main.py").read_text() == (seed / "main.py").read_text()
assert (work / "rb_model.py").read_text() == "# the run's model\n" and (work / "rb_config.py").read_text() == CFG
print("OK 3: con --infra current i file protetti vengono dal kit attuale, modello e rb_config restano quelli della run")
print("TRANSFER EVAL TEST PASSED")
