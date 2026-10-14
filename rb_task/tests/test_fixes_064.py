#!/usr/bin/env python3
"""Tests of the kit 0.6.4 changes.

1. Warm start between passes only from ACCEPTED versions (RUN-008: pass 2 started from a never re-checked attempt).
2. The task specs are templates: RB_TASK=driver-dnf / driver-position fills task, metric and description everywhere
   Qwen reads them (extra prompts, stage-12 repair, paper selection) and driver-top3-only facts are dropped.
3. An error metric (MAE, lower is better) is handled in the confirmation table, the paired statistics and the method file.
ARC_ROOT = repo root (default /app).
"""
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ARC_ROOT", "/app"))
sys.path.insert(0, str(ROOT))
TASK = HERE.parent
if not (ROOT / "researchclaw/pipeline/stage_impls/_arc_knowledge.py").is_file():
    sys.exit("Apply the kit patches first: python3 rb_task/patches/apply_relbench_patches.py")

from researchclaw.pipeline.stage_impls import _arc_knowledge as K  # noqa: E402
from researchclaw.pipeline.stage_impls import _arc_refine as A  # noqa: E402
from researchclaw.pipeline.stage_impls import _stage12_repair as S12  # noqa: E402

tmp = Path(tempfile.mkdtemp())
for k in ("RB_TASK", "RB_DATASET", "ARC_WARM_START_ANY"):
    os.environ.pop(k, None)

# 1) warm start ----------------------------------------------------------------------------------------------------------
prev = tmp / "run" / "stage-13_v1"
for v, txt in (("experiment_v19", "# accepted best\n"), ("experiment_v31", "# never re-checked\n")):
    (prev / v).mkdir(parents=True)
    (prev / v / "rb_model.py").write_text(txt)
    (prev / v / "rb_config.py").write_text("PROPOSED_OVERRIDES = {}\nSEED_OFFSET = 0\n")
log1 = {"generated": "t1", "iterations": [
    {"iteration": 19, "version_dir": "experiment_v19/", "metric": 0.8787, "improved": True, "sandbox": {"metrics": {}}},
    {"iteration": 31, "version_dir": "experiment_v31/", "metric": 0.8836, "improved": False, "sandbox": {"metrics": {}}},
]}
(prev / "refinement_log.json").write_text(json.dumps(log1))
state = SimpleNamespace(space={"config_file": "rb_config.py", "variable": "PROPOSED_OVERRIDES"}, config_mode=False,
                        prev_logs=A.previous_passes(tmp / "run"))
ws = A.warm_start(state, {"rb_config.py": "PROPOSED_OVERRIDES = {}\n"}, 0.8787, "maximize")
assert ws is not None and ws["metric"] == 0.8787 and ws["files"]["rb_model.py"] == "# accepted best\n", ws
assert "iteration 19" in ws["record"]["arc_carried_from"]
os.environ["ARC_WARM_START_ANY"] = "1"  # old behaviour, kept as an option
ws_old = A.warm_start(state, {"rb_config.py": "PROPOSED_OVERRIDES = {}\n"}, 0.8787, "maximize")
assert ws_old["files"]["rb_model.py"] == "# never re-checked\n"
os.environ.pop("ARC_WARM_START_ANY")
log1["iterations"][0]["improved"] = False
(prev / "refinement_log.json").write_text(json.dumps(log1))
state.prev_logs = A.previous_passes(tmp / "run")
assert A.warm_start(state, {"rb_config.py": "PROPOSED_OVERRIDES = {}\n"}, 0.7677, "maximize") is None  # nothing accepted
print("OK 1: la ripartenza tra passate usa solo versioni accettate (prima: il tentativo con la metrica piu' alta, anche se mai ricontrollato)")

# 2) task templates --------------------------------------------------------------------------------------------------------
spec_dir = TASK / "task_spec"
specs = {n: (spec_dir / n).read_text() for n in ("full_code.md", "short_code.md", "full.md", "short.md")}
for task, metric, word in (("driver-top3", "ROC-AUC", "top 3"), ("driver-dnf", "ROC-AUC", "not finish"),
                           ("driver-position", "MAE", "finishing position")):
    os.environ["RB_TASK"] = task
    for name, text in specs.items():
        out = K.render_task_text(text)
        assert "{{" not in out and "<!-- only" not in out, (task, name)
        assert task in out and metric in out, (task, name)
        others = [t for t in ("driver-top3", "driver-dnf", "driver-position") if t != task]
        assert not any(o in out for o in others), (task, name, [o for o in others if o in out])
        if name in ("full_code.md", "full.md"):
            assert word in out, (task, name)
    full = K.render_task_text(specs["full.md"])
    assert ("Measured on rel-f1/driver-top3" in full) == (task == "driver-top3"), task
    if task == "driver-position":
        assert "lower is better" in K.render_task_text(specs["full_code.md"])
        assert "primary_metric = -MAE" in K.render_task_text(specs["full_code.md"])
os.environ.pop("RB_TASK")
assert "driver-top3" in K.render_task_text(specs["full_code.md"])  # default task
print("OK 2a: specifiche come modelli: task, descrizione, metrica e direzione dal registro; fatti misurati su driver-top3 solo per driver-top3")

os.environ["RB_TASK"] = "driver-dnf"
from researchclaw.prompts import PromptManager  # noqa: E402

pm = PromptManager(extra_prompts={"iterative_improve": str(spec_dir / "full_code.md"),
                                  "hypothesis_gen": str(spec_dir / "short_code.md")})
ex = pm.extra_prompts if isinstance(pm.extra_prompts, dict) else pm.extra_prompts()
assert all("driver-dnf" in t and "{{" not in t and "driver-top3" not in t for t in ex.values()), list(ex)
os.environ["ARC_TASK_SPEC_FILE"] = str(spec_dir / "full_code.md")
suf = S12._task_spec_suffix()
assert "driver-dnf" in suf and "{{" not in suf
seen = {}


def chat_sel(llm, system, user, max_tokens=None, **kw):
    seen["user"] = user
    return SimpleNamespace(content='{"selected": [0]}')


K.select_papers([{"title": "Some RDL paper", "year": 2025, "abstract": "x"}], [], 1, object(), chat_sel, "topic")
assert "driver-dnf" in seen["user"] and "driver-top3" not in seen["user"], seen["user"][:400]
print("OK 2b: con RB_TASK=driver-dnf il task giusto arriva ai prompt aggiuntivi, alla riparazione dello stage 12 e alla scelta dei paper")

# 3) error metric (MAE) ----------------------------------------------------------------------------------------------------
os.environ["RB_TASK"] = "driver-position"
res = [{"condition": c, "seed": s, "val": v, "test": v} for s in range(10)
       for c, v in (("proposed", 3.8 + 0.01 * s), ("baseline_tuned", 4.0 + 0.01 * s))]
st = A.paired_stats(res, "proposed", "baseline_tuned", "test")
assert st["mean_diff"] < 0 and st["seeds_better"] == 10, st  # lower MAE = better on every seed
os.environ["RB_TASK"] = "driver-dnf"
st2 = A.paired_stats(res, "proposed", "baseline_tuned", "test")
assert st2["seeds_better"] == 0  # same numbers read as AUROC: proposed lower = worse
os.environ["RB_TASK"] = "driver-position"
run_dir, st13 = tmp / "run2", tmp / "run2" / "stage-13"
st13.mkdir(parents=True)
(run_dir / "stage-12" / "runs").mkdir(parents=True)
(run_dir / "stage-12" / "runs" / "run-1.json").write_text(json.dumps({"metrics": {
    "proposed_n_seeds": 10, "baseline_tuned_n_seeds": 10, "proposed_val_mae_std": 0.05}}))
method = tmp / "METHOD.md"
os.environ.update({"ARC_SEARCH_MODE": "code", "ARC_SEARCH_SPACE_FILE": str(spec_dir / "search_space.json"),
                   "ARC_CONFIRM_SEED_OFFSET": "100", "ARC_METHOD_FILE": str(method)})
ms = A.ModeState(run_dir, st13, "topic")
assert ms.expected["seeds"] == 10 and abs(ms.expected["se"] - 0.05 / 10 ** 0.5) < 1e-9, ms.expected
metrics = {"primary_metric": -3.845, "proposed_n_seeds": 10.0, "baseline_tuned_n_seeds": 10.0,
           "proposed_val_mae_mean": 3.845, "proposed_val_mae_std": 0.03, "proposed_test_mae_mean": 3.9, "proposed_test_mae_std": 0.04,
           "baseline_tuned_val_mae_mean": 4.045, "baseline_tuned_val_mae_std": 0.03, "baseline_tuned_test_mae_mean": 4.0,
           "baseline_tuned_test_mae_std": 0.04}


class Box:
    def __init__(self, cfg, path):
        self.path = Path(path)

    def run_project(self, cdir, timeout_sec=None):
        p = self.path / "_project_1"
        p.mkdir(parents=True, exist_ok=True)
        (p / "results.json").write_text(json.dumps({"results": res}))
        return SimpleNamespace(returncode=0, metrics=dict(metrics), stdout="", stderr="", timed_out=False, elapsed_sec=1.0)


def write_project(d, files):
    Path(d).mkdir(parents=True, exist_ok=True)
    for k, v in files.items():
        (Path(d) / k).write_text(v)


best = {"rb_config.py": (TASK / "seed_project" / "rb_config.py").read_text(), "rb_model.py": "# m\n", "rb_model_official.py": "# o\n"}
A.confirm(ms, SimpleNamespace(experiment=SimpleNamespace(time_budget_sec=60)), st13, best, "experiment_v1/",
          {"iterations": []}, Box, write_project, logging.getLogger("t"))
md = (st13 / "confirmation.md").read_text()
assert "| condition | val MAE | test MAE |" in md and "3.8450" in md and "nan" not in md, md
meth = method.read_text()
assert "test MAE 3.9000" in meth and "better on 10/10 seeds" in meth and "rel-f1 / driver-position" in meth, meth[-1500:]
print("OK 3: metrica d'errore (MAE): tabella di conferma, statistiche appaiate (meglio = piu' basso) e file del metodo corretti")
print("FIXES 0.6.4 TESTS PASSED")
