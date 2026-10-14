#!/usr/bin/env python3
"""End-to-end test of the 0.6.3 fixes in stage 13 (real sandbox subprocess, toy experiment, fake LLM with a context limit).

Reproduces the conditions of RUN-007 (stage 13 failed with HTTP 400 after 216 s):
  - the project contains a large vendored file (vendor_*.py, 240k characters: RelGNN + LightRDL were 192k);
  - the model server rejects prompts above a size limit (llama-server: HTTP 400 when the prompt exceeds the context);
  - every run prints a UserWarning on stderr (torch_frame does it in every RelBench run).
Checks that:
  1. no prompt exceeds the limit: repair prompts no longer contain vendored code;
  2. a valid run with warnings is NOT sent to the runtime repair (no second run, the evaluated code is the proposed one);
  3. a crash is still repaired (and the repair prompt is small);
  4. an LLM error skips the attempt instead of failing the whole stage;
  5. a busy GPU (GPU_UNAVAILABLE) is not "repaired" and the LLM is told it was not its fault;
  6. after 20+ attempts the prompt still shows the most recent attempts (upstream showed only the first 20 entries).
Needs the patched pipeline. ARC_ROOT = repo root (default /app).
"""
import dataclasses
import json
import os
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ARC_ROOT", "/app"))
sys.path.insert(0, str(ROOT))
TASK = HERE.parent
if not (ROOT / "researchclaw/pipeline/stage_impls/_arc_knowledge.py").is_file():
    sys.exit("Apply the kit patches first: python3 rb_task/patches/apply_relbench_patches.py")

tmp = Path(tempfile.mkdtemp())
know = tmp / "KNOWLEDGE.md"
know.write_text("## KNOWLEDGE FROM THE LITERATURE AND OFFICIAL CODE (test)\n### [K1] RelToy: Relational Max Passing (2025)\n"
                "#### Components to implement\n1. RelToyConv: max over edge types\n", encoding="utf-8")
os.environ.update({
    "RB_RECIPE": "tuned", "ARC_SEARCH_MODE": "code", "ARC_SEARCH_SPACE_FILE": str(TASK / "task_spec" / "search_space.json"),
    "ARC_PROTECTED_FILES": "main.py,rb_data.py,rb_loader.py,rb_text.py,rb_train.py,rb_model_official.py",
    "ARC_PROMPT_HIDE_FILES": "rb_model_official.py,rb_loader.py,rb_text.py",
    "ARC_MIN_IMPROVEMENT": "0.005", "ARC_KEEP_SEEDS": "1", "ARC_PRESERVE_FILENAMES": "1", "ARC_HIDE_TEST_METRICS": "1",
    "ARC_REFINE_PATIENCE": "100", "ARC_MAX_NO_METRICS": "10", "ARC_KNOWLEDGE_FILE": str(know),
    "ARC_RUN_STARTED_AT": str(time.time() - 60), "ARC_REQUIRE_KNOWLEDGE_REF": "1",
    "ARC_REQUIRE_COMPONENT_MATCH": "0", "ARC_MAX_REFINE_ITERS": "1000", "ARC_HISTORY_LAST": "6",
})
os.environ.pop("ARC_REPAIR_ON_WARNINGS", None)

from researchclaw.adapters import AdapterBundle  # noqa: E402
from researchclaw.config import RCConfig  # noqa: E402
from researchclaw.pipeline.stage_impls._execution import _execute_iterative_refine  # noqa: E402
from researchclaw.prompts import PromptManager  # noqa: E402

TOY_MAIN = '''
import sys
import experiment_harness
import rb_config as C
import numpy as np
from pathlib import Path

print("/usr/lib/python3/torch_frame/data/stats.py:177: UserWarning: Could not infer format", file=sys.stderr)
model_src = Path("rb_model.py").read_text()
if "GPUBUSY" in model_src:
    print("GPU_UNAVAILABLE: only 0.0 GB free after waiting 600s (test)")
    raise SystemExit(3)

def val_of(cfg, seed, bonus):
    v = 0.70 + 0.10 * (cfg.get("gnn_type") == "reltoy") + bonus
    return v + 0.003 * np.sin(seed * 12.9898)

h = experiment_harness.get_harness(time_budget=60)
if "CRASH" in model_src:
    raise RuntimeError("toy crash: the model code is broken")
bonus = 0.0
for line in model_src.splitlines():
    if line.startswith("# bonus="):
        bonus = float(line.split("=", 1)[1])
same_code = model_src.strip() == Path("rb_model_official.py").read_text().strip()
identical = 1.0 if (not C.PROPOSED_OVERRIDES and same_code) else 0.0
for name, cfg in C.CONDITIONS.items():
    b = bonus if name == "proposed" else 0.0
    vals = [val_of(cfg, s, b) for s in C.SEEDS]
    h.report_metric(f"{name}_val_roc_auc_mean", float(np.mean(vals)))
    h.report_metric(f"{name}_val_roc_auc_std", float(np.std(vals, ddof=1)))
    h.report_metric(f"{name}_test_roc_auc_mean", float(np.mean(vals)) * 0.9)
    h.report_metric(f"{name}_n_seeds", float(len(vals)))
h.report_metric("proposed_identical_to_baseline", identical)
h.report_metric("primary_metric", float(np.mean([val_of(C.CONDITIONS["proposed"], s, bonus) for s in C.SEEDS])))
h.finalize()
'''
VENDOR = "# Vendored (read-only) official code. VENDOR_BIG_MARKER\n" + "".join(
    f"def helper_{i}(x):\n    return x + {i}  # padding to reach the size of RUN-007's vendored code\n" for i in range(3000))
assert len(VENDOR) > 190_000

seed_cfg = (TASK / "seed_project" / "rb_config.py").read_text()
run_dir = tmp / "run"
exp0 = run_dir / "stage-10" / "experiment"
exp0.mkdir(parents=True)
(exp0 / "main.py").write_text(TOY_MAIN)
(exp0 / "rb_config.py").write_text(seed_cfg)
(exp0 / "rb_model.py").write_text("# model v0\n")
(exp0 / "rb_model_official.py").write_text("# model v0\n")
(exp0 / "vendor_big_model.py").write_text(VENDOR)
for name in ("rb_data.py", "rb_loader.py", "rb_text.py", "rb_train.py"):
    (exp0 / name).write_text(f"# {name}\n")
(run_dir / "stage-09").mkdir()
(run_dir / "stage-09" / "exp_plan.yaml").write_text("conditions: [baseline_graphsage, baseline_tuned, proposed]\n")
s12 = run_dir / "stage-12" / "runs"
s12.mkdir(parents=True)
(s12 / "run-1.json").write_text(json.dumps({"run_id": "run-1", "status": "completed", "metrics": {
    "primary_metric": 0.70, "proposed_val_roc_auc_mean": 0.70, "proposed_val_roc_auc_std": 0.003,
    "baseline_graphsage_n_seeds": 10, "baseline_tuned_n_seeds": 10, "proposed_n_seeds": 10}, "stdout": "primary_metric: 0.70\n"}))


def cfg_with(overrides: str, source: str) -> str:
    t = seed_cfg.replace("PROPOSED_OVERRIDES = {}", f"PROPOSED_OVERRIDES = {overrides}", 1)
    return t.replace('PROPOSED_SOURCE = ""', f"PROPOSED_SOURCE = {source!r}", 1)


def blocks(**files) -> str:
    return "\n".join(f"```filename:{name}\n{text}\n```" for name, text in files.items())


LIMIT = 150_000  # characters: stands in for the 65k-token context of llama-server
N_ITERS = 24
calls: list[tuple[str, int, str]] = []


class Resp:
    def __init__(s, c):
        s.content, s.finish_reason, s.total_tokens, s.usage, s.model = c, "stop", 1, {}, "fake"


class LLM:
    def chat(self, messages, **kw):
        text = "\n".join(m.get("content", "") for m in messages)
        kind = "repair" if ("## Validation Issues" in text or "## Issues Found" in text) else "improve"
        calls.append((kind, len(text), text))
        if len(text) > LIMIT:
            raise RuntimeError("All models failed. Last error: HTTP Error 400: Bad Request")
        if kind == "repair":
            return Resp(blocks(**{"rb_model.py": f"# model repaired at call {len(calls)}\n# bonus=0.0\n"}))
        n = sum(1 for c in calls if c[0] == "improve")
        if n == 3:
            raise RuntimeError("All models failed. Last error: HTTP Error 503: Service Unavailable")
        if n == 5:
            return Resp(blocks(**{"rb_config.py": cfg_with('{"gnn_type": "reltoy"}', "K1: RelToyConv"),
                                  "rb_model.py": "# model CRASH\n"}))
        if n == 7:
            return Resp(blocks(**{"rb_config.py": cfg_with('{"gnn_type": "reltoy"}', "K1: RelToyConv"),
                                  "rb_model.py": "# model GPUBUSY\n"}))
        bonus = 0.01 * n if n in (1, 9, 15) else 0.0  # three real improvements, the rest no gain
        return Resp(blocks(**{"rb_config.py": cfg_with('{"gnn_type": "reltoy"}', "K1: RelToyConv"),
                              "rb_model.py": f"# model v{n}\n# bonus={bonus}\n"}))


cfg = RCConfig.load(str(TASK.parent / "config.arc.relbench.code.yaml"), check_paths=False)
cfg = dataclasses.replace(cfg, experiment=dataclasses.replace(
    cfg.experiment, max_iterations=N_ITERS, time_budget_sec=120,
    sandbox=dataclasses.replace(cfg.experiment.sandbox, python_path=sys.executable)))
stage_dir = run_dir / "stage-13"
stage_dir.mkdir()
res = _execute_iterative_refine(stage_dir, run_dir, cfg, AdapterBundle(), llm=LLM(), prompts=PromptManager())
log = json.loads((stage_dir / "refinement_log.json").read_text())
its = log["iterations"]
print("stato:", res.status, "| iterazioni:", len(its), "| chiamate LLM:", len(calls),
      "| prompt piu' lungo:", max(c[1] for c in calls), "caratteri")
print([(i["iteration"], None if i.get("metric") is None else round(i["metric"], 3), i.get("improved"),
        "R" if i.get("runtime_repaired") else "", "E" if i.get("llm_error") else "") for i in its])

assert "DONE" in str(res.status).upper(), res
too_big = [c[1] for c in calls if c[1] > LIMIT]
assert not too_big, f"prompt oltre il limite del contesto: {too_big}"
assert not any("VENDOR_BIG_MARKER" in c[2] for c in calls), "codice vendorizzato finito in un prompt"
print("OK 1: nessun prompt oltre il limite; il codice vendorizzato non entra in nessun prompt (miglioramento e riparazione)")

valid = [i for i in its if i.get("metric") is not None and (i.get("sandbox") or {}).get("returncode") == 0]
assert len(valid) >= 15, len(valid)
assert not any(i.get("runtime_repaired") for i in valid), [i["iteration"] for i in valid if i.get("runtime_repaired")]
n_repairs = sum(1 for c in calls if c[0] == "repair")
assert n_repairs == 1, f"una sola riparazione attesa (il crash), trovate {n_repairs}"
print("OK 2: le run valide con warning su stderr NON vengono 'riparate' (prima: riparazione + seconda run)")

crash = next(i for i in its if i.get("runtime_repaired"))
assert crash.get("metric") is not None and "sandbox_after_fix" in crash, crash
rep = next(c for c in calls if c[0] == "repair")
assert rep[1] < 60_000 and "toy crash" in rep[2], rep[1]
print(f"OK 3: il crash viene ancora riparato; prompt di riparazione {rep[1]} caratteri (con il vendor sarebbero >240k)")

errs = [i for i in its if i.get("llm_error")]
assert len(errs) == 1 and "503" in errs[0]["llm_error"], errs
assert len(its) == N_ITERS, len(its)
print("OK 4: un errore dell'LLM salta il tentativo, lo stage continua e finisce (prima: stage 13 FAILED)")

busy = next(i for i in its if "GPU_UNAVAILABLE" in str((i.get("sandbox") or {}).get("stdout", "")))
assert busy.get("metric") is None and not busy.get("runtime_repaired"), busy
later = [c[2] for c in calls if c[0] == "improve"][8:]
assert any("NOT EVALUATED - the GPU was occupied" in p for p in later), "l'LLM non sa che la GPU era occupata"
print("OK 5: GPU occupata: nessuna riparazione del codice, l'LLM viene avvisato che non e' colpa sua")

last = [c[2] for c in calls if c[0] == "improve"][-1]
assert f"attempt {N_ITERS - 1} " in last, "l'ultimo prompt non contiene l'ultimo tentativo"
assert "EARLIER ATTEMPTS" in last and "- attempt 1: files changed" in last, "manca il riassunto dei tentativi vecchi"
assert last.count("REFINEMENT HISTORY - attempt") <= 6, last.count("REFINEMENT HISTORY - attempt")
print("OK 6: dopo 20+ tentativi il prompt mostra gli ultimi tentativi per intero e i vecchi in una riga ciascuno")
print("STAGE13 ROBUSTNESS TEST PASSED")
