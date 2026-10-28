#!/usr/bin/env python3
"""Test of rb_task/tools/repro_check.py with a toy project (no rel-f1 data, no GPU).

The toy main.py behaves like the seed project in the way that matters here: the first run of a "container" prepares the
data into RB_CACHE_DIR (stypes.json + a materialised file) and later runs reuse it; the result of a seed depends on the
seed and on the prepared data. The "data preparation" of the toy differs between containers (FAKE_VARIANT), so:
A1 = A2, B1 = B2, A != B, and C (A's cache) = A. Checks the run outputs, the comparison and the cache diff.
Run from the repo root (needs researchclaw/experiment/harness_template.py, or RB_HARNESS).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "tools" / "repro_check.py"

CFG = '''import os
CACHE_DIR = os.environ.get("RB_CACHE_DIR", "/tmp/x")
SEED_OFFSET = int(os.environ.get("RB_SEED_OFFSET", "0"))
N_SEEDS = int(os.environ.get("RB_N_SEEDS", "10"))
SEEDS = [SEED_OFFSET + i for i in range(N_SEEDS)]
CONDITIONS = {"baseline_graphsage": {"b": 0.0}, "baseline_tuned": {"b": 0.03}, "proposed": {"b": 0.03}}
'''
MAIN = '''import json, os, hashlib
from pathlib import Path
import experiment_harness
import rb_config as C
h = experiment_harness.get_harness(time_budget=60)
d = Path(C.CACHE_DIR) / "rel-f1"
st = d / "stypes.json"
if not st.is_file():                     # "data preparation": done once per container, differs between containers
    d.mkdir(parents=True, exist_ok=True)
    v = os.environ.get("FAKE_VARIANT", "1")
    st.write_text(json.dumps({"results": {"position": "numerical" if v == "1" else "categorical", "points": "numerical"}}))
    (d / "materialized").mkdir(exist_ok=True)
    (d / "materialized" / "results.pt").write_bytes(("blob" + v).encode())
key = hashlib.md5(st.read_bytes()).hexdigest()
for seed in C.SEEDS:
    for name, cfg in C.CONDITIONS.items():
        bump = (int(hashlib.md5(f"{key}{seed}".encode()).hexdigest(), 16) % 1000) / 10000.0   # depends on data + seed
        v = 0.75 + cfg["b"] + bump
        h.log_result({"condition": name, "seed": seed, "val": v, "test": v - 0.01, "tune_metric": "roc_auc",
                      "higher_is_better": True})
h.report_metric("primary_metric", 0.75)
h.finalize()
'''

tmp = Path(tempfile.mkdtemp())
proj = tmp / "proj"
proj.mkdir()
(proj / "rb_config.py").write_text(CFG)
(proj / "main.py").write_text(MAIN)
out = tmp / "repro"


def run(*args, variant="1"):
    env = dict(os.environ, FAKE_VARIANT=variant)
    r = subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, env=env, timeout=600)
    print(r.stdout[-800:], r.stderr[-800:])
    return r


assert run("run", "--out", str(out), "--name", "A", "--repeat", "2", "--project", str(proj), "--n-seeds", "4", variant="1").returncode == 0
assert run("run", "--out", str(out), "--name", "B", "--repeat", "2", "--project", str(proj), "--n-seeds", "4", variant="2").returncode == 0
assert run("run", "--out", str(out), "--name", "C", "--repeat", "1", "--project", str(proj), "--n-seeds", "4",
           "--cache-from", str(out / "A" / "cache"), variant="3").returncode == 0
info = json.loads((out / "A" / "info.json").read_text())
assert [r["returncode"] for r in info["runs"]] == [0, 0] and info["seeds"] == [100, 103]
assert "rel-f1/stypes.json" in info["cache_after_run1"] and not info["cache_changed_after_run1"]
assert (out / "A" / "run2" / "results.json").is_file() and not (out / "A" / "run1" / "project").exists()
assert (out / "A" / "packages.txt").read_text().strip() and "libs" in info["environment"]
ic = json.loads((out / "C" / "info.json").read_text())
assert ic["cache_from"].endswith("A/cache") and ic["cache_at_start"] == info["cache_after_run1"]
print("OK 1: run salva risultati per seme, impronta della cache, ambiente; C parte dalla cache di A")

assert run("compare", "--out", str(out)).returncode == 0
md = (out / "summary.md").read_text()
rows = {l.split("|")[1].strip(): l for l in md.splitlines() if l.startswith("| stesso container") or l.startswith("| A vs")}
w = float(rows["stesso container"].split("|")[2])
ab = float(rows["A vs B"].split("|")[2])
ac = float(rows["A vs C"].split("|")[2])
assert w == 0.0 and ac == 0.0 and ab > 0.001, (w, ab, ac)
assert "C (cache di A) coincide con A: la differenza viene dai dati preparati" in md
assert "A vs C: cache identiche" in md and "A vs B: 2 file diversi" in md
assert "results.position: numerical / categorical" in md, md
print("OK 2: confronto giusto (stesso container = 0, A vs B > 0, A vs C = 0), lettura e differenza dei tipi delle colonne")

# a different data preparation that does NOT explain the result: C differs from A too
(proj / "main.py").write_text(MAIN.replace('key = hashlib.md5(st.read_bytes()).hexdigest()',
                                           'key = os.environ.get("FAKE_VARIANT", "1")'))
out2 = tmp / "repro2"
for n, v, rep, extra in (("A", "1", "2", []), ("B", "2", "1", []), ("C", "3", "1", ["--cache-from", str(out2 / "A" / "cache")])):
    assert run("run", "--out", str(out2), "--name", n, "--repeat", rep, "--project", str(proj), "--n-seeds", "4", *extra,
               variant=v).returncode == 0
run("compare", "--out", str(out2))
assert "anche C differisce da A: non sono (solo) i dati preparati" in (out2 / "summary.md").read_text()
print("OK 3: se C differisce da A, la lettura dice che non sono (solo) i dati preparati")

assert run("run", "--out", str(tmp / "o3"), "--name", "X", "--project", str(proj), "--cache-from", str(tmp / "nope")).returncode == 1
print("OK 4: --cache-from mancante -> errore")
# stypes: the column types come from a random sample -> different variants, each evaluated once
sp = tmp / "proj_st"
(sp / "relbench" / "modeling").mkdir(parents=True)
(sp / "relbench" / "__init__.py").write_text("")
(sp / "relbench" / "modeling" / "__init__.py").write_text("")
(sp / "relbench" / "modeling" / "utils.py").write_text(
    "import numpy as np\n"
    "def get_stype_proposal(db):\n"
    "    return {'results': {'position': 'numerical' if np.random.rand() < 0.6 else 'categorical', 'points': 'numerical'}}\n")
(sp / "rb_loader.py").write_text(
    "class _D:\n    def get_db(self):\n        return None\n"
    "def load_dataset_and_task(d, t):\n    return _D(), None, {}\n")
(sp / "rb_config.py").write_text(CFG)
(sp / "main.py").write_text(MAIN)
out4 = tmp / "st"
r = run("stypes", "--out", str(out4), "--project", str(sp), "--n", "20", "--n-seeds", "4")
assert r.returncode == 0
md = (out4 / "summary_stypes.md").read_text()
info = json.loads((out4 / "stypes_info.json").read_text())
assert len(info["variants"]) == 2 and sum(v["samples"] for v in info["variants"]) == 20, info["variants"]
assert set(info["changing_columns"]) == {"results.position"} and len(info["worlds"]) == 2
assert "Esiti diversi: 2" in md and "`results.position`" in md and "**variante 2**" in md
w1 = json.loads((out4 / "worlds" / "v1" / "results.json").read_text())["results"]
w2 = json.loads((out4 / "worlds" / "v2" / "results.json").read_text())["results"]
assert [x["test"] for x in w1] != [x["test"] for x in w2]     # a different stypes.json -> different results
assert (out4 / "worlds" / "v1" / "cache" / "rel-f1" / "stypes.json").read_text() == (out4 / "stypes" / "variant_1.json").read_text()
print("OK 5: stypes trova le varianti dei tipi delle colonne, le colonne che cambiano e valuta ogni variante")
print("REPRO CHECK TEST PASSED")
