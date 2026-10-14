#!/usr/bin/env python3
"""Unit tests of the kit 0.6.3 fixes (RUN-007: stage 13 failed with HTTP 400; GPU full during stage 12).

1. vendoring: command-line scripts and copies of installed libraries are not vendored (RelGNN: 25 files/154k chars -> 8/~37k);
2. prompt files: vendored/frozen files are hidden from every stage-13 prompt (improve and repair);
3. runtime repair only for real failures (not for warnings), never for a busy GPU or a skipped run;
4. prompt history: stage-12 summaries + digest of old attempts + the most recent attempts;
5. main.py waits for a busy GPU and exits with GPU_UNAVAILABLE (code 3) if it stays full;
6. stage-12 repair: no LLM edit for GPU_UNAVAILABLE, vendored code not shown to the repair LLM.
ARC_ROOT = repo root (default /app).
"""
import ast
import json
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

# 1) vendoring ------------------------------------------------------------------------------------------------
assert K._is_script("import argparse\nparser = argparse.ArgumentParser()\nargs = parser.parse_args()\n")
assert K._is_script("import argparse\nargs = argparse.ArgumentParser().parse_known_args()[0]\n")
assert not K._is_script("import argparse\ndef cli():\n    return argparse.ArgumentParser().parse_args()\n")
assert not K._is_script("import argparse\nif __name__ == '__main__':\n    argparse.ArgumentParser().parse_args()\n")
assert not K._is_script("class Conv:\n    pass\n")
repo = tmp / "RelToyRepo"
(repo / "examples").mkdir(parents=True)
(repo / "relbench" / "base").mkdir(parents=True)
(repo / "relbench" / "__init__.py").write_text("")
(repo / "relbench" / "base" / "__init__.py").write_text("")
(repo / "relbench" / "base" / "table.py").write_text("class Table:\n    pass\n")
(repo / "examples" / "reltoy_conv.py").write_text("import json\nclass RelToyConv:\n    def forward(self, x):\n        return x\n")
(repo / "examples" / "gnn_node.py").write_text(
    "import argparse\nfrom reltoy_conv import RelToyConv\nparser = argparse.ArgumentParser()\nargs = parser.parse_args()\n")
v = K.vendor_repo(repo, "reltoy", tmp / "vendor", "https://github.com/x/RelToyRepo",
                  installed=lambda name: name == "relbench")
assert sorted(v["files"]) == ["vendor_reltoy_reltoy_conv.py"], sorted(v["files"])
assert "script" in v["skipped"]["examples/gnn_node.py"] and "relbench" in v["skipped"]["relbench/base/table.py"], v["skipped"]
v2 = K.vendor_repo(repo, "reltoy", tmp / "vendor2", "", installed=lambda name: False)  # not installed -> kept
assert "vendor_reltoy_table.py" in v2["files"], sorted(v2["files"])
os.environ["ARC_VENDOR_MAX_CHARS"] = "10"
assert not K.vendor_repo(repo, "reltoy", tmp / "vendor3", "", installed=lambda n: n == "relbench")["files"]
os.environ.pop("ARC_VENDOR_MAX_CHARS")
print("OK 1: vendor = solo moduli del modello (script con argparse e copie di librerie installate esclusi), budget da ARC_VENDOR_MAX_CHARS")

# 2) files shown in the prompts ------------------------------------------------------------------------------------
os.environ["ARC_PROMPT_HIDE_FILES"] = "rb_model_official.py,rb_loader.py,rb_text.py"
files = {"main.py": "m", "rb_model.py": "x", "rb_model_official.py": "o", "rb_text.py": "t", "vendor_relgnn_model.py": "v" * 10}
assert sorted(K.visible_files(files)) == ["main.py", "rb_model.py"]
exe = (ROOT / "researchclaw/pipeline/stage_impls/_execution.py").read_text()
assert exe.count("ARC patch: repair prompt files") == 2, "le due chiamate di riparazione devono filtrare i file"
assert "all_files_ctx=_files_to_context(candidate_files)," not in exe, "resta una riparazione con TUTTI i file"
print("OK 2: i file vendorizzati/congelati sono esclusi anche dai prompt di riparazione (prima solo da quello di miglioramento)")

# 3) runtime repair only for real failures ---------------------------------------------------------------------------
detect = lambda run: "Runtime warnings/errors from stderr:\n" + run.stderr if "Warning" in run.stderr or "Error" in run.stderr else ""
ok_run = SimpleNamespace(returncode=0, timed_out=False, stdout="primary_metric: 0.8\n",
                         stderr="stats.py:177: UserWarning: Could not infer format", metrics={"primary_metric": 0.8})
assert A.repair_issues(ok_run, 0.8, detect) == "", "una run valida con warning non va riparata"
crash = SimpleNamespace(returncode=1, timed_out=False, stdout="", stderr="Traceback ...\nRuntimeError: boom", metrics={})
assert "boom" in A.repair_issues(crash, None, detect)
silent = SimpleNamespace(returncode=0, timed_out=False, stdout="", stderr="", metrics={})
assert "no primary metric" in A.repair_issues(silent, None, detect)
nan = SimpleNamespace(returncode=0, timed_out=False, stdout="", stderr="", metrics={"primary_metric": float("nan")})
assert A.repair_issues(nan, float("nan"), lambda r: "METRIC NaN") == "METRIC NaN"
busy = SimpleNamespace(returncode=3, timed_out=False, stdout="GPU_UNAVAILABLE: only 0.1 GB free", stderr="", metrics={})
assert A.repair_issues(busy, None, detect) == "" and A.gpu_unavailable(busy)
assert A.repair_issues(A.skipped_run(), None, detect) == ""
os.environ["ARC_REPAIR_ON_WARNINGS"] = "1"
assert A.repair_issues(ok_run, 0.8, detect).startswith("Runtime warnings")
os.environ.pop("ARC_REPAIR_ON_WARNINGS")
rec = {"metric": None, "sandbox": {"returncode": 3, "stdout": busy.stdout, "stderr": ""}}
assert "NOT EVALUATED - the GPU was occupied" in A.history_line(5, rec, {"a.py": "1"}, {"a.py": "2"}, 0.8)
print("OK 3: riparazione solo per crash/assenza di metrica/NaN; mai per warning, GPU occupata o tentativo saltato")

# 4) history in the prompt -------------------------------------------------------------------------------------------
base = ['{"run": "stage12", "primary_metric": 0.70}']
hist = [f"REFINEMENT HISTORY - attempt {i} (your earlier modification, already evaluated):\n  files changed: rb_model.py\n"
        f"  RESULT: primary_metric=0.{700 + i} (did NOT improve; best so far=0.8)\n  change (unified diff):\n" + "+x\n" * 50 +
        "  Do not repeat attempts that did not help; try a different idea." for i in range(1, 31)]
out = A.summaries_for_prompt(base + hist, keep_last=5, max_chars=40000)
assert out[0] == base[0] and out[-1] == hist[-1] and out[-5] == hist[-5]
assert out[1].startswith("EARLIER ATTEMPTS") and "- attempt 1: files changed: rb_model.py | RESULT: primary_metric=0.701" in out[1]
assert "- attempt 25:" in out[1] and "- attempt 26:" not in out[1] and len(out) == 1 + 1 + 5
small = A.summaries_for_prompt(base + hist, keep_last=5, max_chars=600)
assert sum(len(x) for x in small[2:]) <= 600 and small[-1] == hist[-1]
assert A.summaries_for_prompt(base + hist[:3], keep_last=5) == base + hist[:3]
print("OK 4: storia nel prompt = riassunti dello stage 12 + una riga per i tentativi vecchi + ultimi tentativi completi")

# 5) main.py waits for a busy GPU -----------------------------------------------------------------------------------
src = (TASK / "seed_project" / "main.py").read_text()
tree = ast.parse(src)
fn_src = "\n\n".join(ast.get_source_segment(src, n) for n in tree.body
                     if isinstance(n, ast.FunctionDef) and n.name in ("_child_free_bytes", "wait_for_gpu"))
seq = []


class FakeCuda:
    def __init__(self, frees):
        self.frees = list(frees)

    def mem_get_info(self):
        f = self.frees.pop(0) if len(self.frees) > 1 else self.frees[0]
        if f is None:
            raise RuntimeError("CUDA error: out of memory")
        return (f, 32e9)


class FakePool:
    def __init__(self, cuda):
        self.cuda = cuda

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def apply(self, fn):
        return fn()


def run_wait(frees, wait_sec):
    cuda = FakeCuda(frees)
    clock = {"t": 0.0}
    fake_time = SimpleNamespace(time=lambda: clock["t"], sleep=lambda s: clock.__setitem__("t", clock["t"] + s))
    fake_mp = SimpleNamespace(get_context=lambda kind: SimpleNamespace(Pool=lambda n: FakePool(cuda)))
    ns = {"torch": SimpleNamespace(cuda=cuda), "time": fake_time, "os": os}
    exec(fn_src, ns)
    sys.modules["multiprocessing"], saved = fake_mp, sys.modules.get("multiprocessing")
    os.environ["RB_GPU_WAIT_SEC"] = str(wait_sec)
    try:
        ns["wait_for_gpu"]()
        return "ok", clock["t"]
    except SystemExit as e:
        return f"exit {e.code}", clock["t"]
    finally:
        sys.modules["multiprocessing"] = saved


os.environ["RB_MIN_FREE_GB"] = "4.5"
assert run_wait([20e9], 600) == ("ok", 0.0)                      # enough memory: no wait at all
assert run_wait([None, 1e9, 6e9], 600) == ("ok", 60.0)            # context creation fails, then frees up
assert run_wait([None], 120)[0] == "exit 3"                        # stays full -> GPU_UNAVAILABLE, exit code 3
assert "GPU_UNAVAILABLE" in src and "wait_for_gpu()  # before the harness clock starts" in src
body = src.split("for seed in C.SEEDS:", 1)
assert 'harness.report_metric("proposed_identical_to_baseline"' in body[1], "metrica diagnostica da riportare dopo l'addestramento"
print("OK 5: main.py aspetta la GPU occupata (sonda in un processo nuovo) e termina con GPU_UNAVAILABLE / codice 3 se resta piena")

# 6) stage-12 repair -------------------------------------------------------------------------------------------------
exp = tmp / "exp"
exp.mkdir()
(exp / "main.py").write_text("print('x')\n")
(exp / "vendor_big.py").write_text("# VENDOR\n" * 100)
st12 = tmp / "stage-12"
st12.mkdir()


class NoLLM:
    def chat(self, *a, **k):
        raise AssertionError("the LLM must not be asked to repair a busy GPU")


res = S12.repair_loop(sandbox=None, result=busy, exp_dir=exp, stage_dir=st12, llm=NoLLM(), timeout_sec=60,
                      parse_metrics=lambda out: {})
assert res is busy
rep = json.loads((st12 / "stage12_repairs.json").read_text())
assert not rep["success"] and "GPU_UNAVAILABLE" in rep["attempts"][0]["note"], rep
assert "VENDOR" not in S12._read_sources(st12 / "experiment_repaired") and "main.py" in S12._read_sources(st12 / "experiment_repaired")
print("OK 6: stage 12: nessuna modifica del codice se la GPU e' occupata; il codice vendorizzato non va nel prompt di riparazione")
print("FIXES 0.6.3 TESTS PASSED")
