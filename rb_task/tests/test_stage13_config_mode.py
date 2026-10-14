#!/usr/bin/env python3
"""End-to-end test of stage 13 in config mode (real sandbox subprocess, toy experiment, fake LLM).

Checks: the LLM never touches code; invalid proposals fall back; crashed / incomplete runs are rejected;
the noise margin is applied; the final project differs from the seed ONLY in PROPOSED_OVERRIDES; the
confirmation on fresh seeds is produced; no test number ever reaches the LLM prompts.
Needs the patched pipeline (rb_task/patches/apply_relbench_patches.py). ARC_ROOT = repo root (default /app).
"""
import dataclasses, json, os, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ARC_ROOT", "/app"))
if not (ROOT / "researchclaw/pipeline/stage_impls/_arc_refine.py").is_file():
    sys.exit("The kit patches are not applied to the pipeline code. Run, from the repo root and OUTSIDE the container:\n"
             "    python3 rb_task/patches/apply_relbench_patches.py\nthen repeat ./run.sh smoke")
sys.path.insert(0, str(ROOT))
TASK = HERE.parent
os.environ.update({
    "RB_RECIPE": "tuned", "ARC_SEARCH_MODE": "config", "ARC_SEARCH_SPACE_FILE": str(TASK / "task_spec" / "search_space.json"),
    "ARC_PROTECTED_FILES": "main.py,rb_data.py,rb_loader.py,rb_text.py,rb_train.py", "ARC_MIN_IMPROVEMENT": "0.005",
    "ARC_CONFIRM_SEED_OFFSET": "100", "ARC_METHOD_FILE": str(Path(tempfile.mkdtemp()) / "METHOD.md"), "ARC_HIDE_TEST_METRICS": "1", "ARC_KEEP_SEEDS": "1", "ARC_REFINE_PATIENCE": "5", "ARC_PRESERVE_FILENAMES": "1",
})

from researchclaw.adapters import AdapterBundle
from researchclaw.config import RCConfig
from researchclaw.pipeline.stage_impls._execution import _execute_iterative_refine
from researchclaw.prompts import PromptManager

# ---- regression: the upstream helper used to turn a lone rb_config.py block into main.py
from researchclaw.pipeline._helpers import _extract_multi_file_blocks
_blk = "```filename:rb_config.py\nX = 1\n```"
assert list(_extract_multi_file_blocks(_blk)) == ["rb_config.py"], "ARC_PRESERVE_FILENAMES non applicato"
os.environ.pop("ARC_PRESERVE_FILENAMES")
assert list(_extract_multi_file_blocks(_blk)) == ["main.py"]          # il comportamento originale (causa della corruzione)
os.environ["ARC_PRESERVE_FILENAMES"] = "1"
print("OK 0: causa della corruzione di main.py riprodotta e neutralizzata")

# ---- toy experiment with the same interface as the real seed (rb_config.py is the REAL one)
TOY_MAIN = '''
import experiment_harness
import rb_config as C
import numpy as np

def val_of(cfg, seed):
    # toy landscape (only options that matter for the chosen operator): sage+max, channels=64, residual hurts
    v = 0.70 + 0.10 * (cfg.get("aggr") == "max" and cfg.get("gnn_type") == "sage") + 0.05 * (cfg.get("channels") == 64)
    v += 0.02 * (cfg.get("dropout") == 0.3)  # a "better-looking" value from a run that will crash
    v -= 0.04 * bool(cfg.get("residual"))
    return v + 0.004 * np.sin(seed * 12.9898)

h = experiment_harness.get_harness(time_budget=60)
for name, cfg in C.CONDITIONS.items():
    vals = [val_of(cfg, s) for s in C.SEEDS]
    for s_, v_ in zip(C.SEEDS, vals):
        h.log_result({"condition": name, "seed": s_, "val": float(v_), "test": float(v_) * 0.9})
    h.report_metric(f"{name}_val_roc_auc_mean", float(np.mean(vals)))
    h.report_metric(f"{name}_val_roc_auc_std", float(np.std(vals, ddof=1)))
    h.report_metric(f"{name}_test_roc_auc_mean", float(np.mean(vals)) * 0.9)
    h.report_metric(f"{name}_n_seeds", float(len(vals)))
h.report_metric("primary_metric", h_val := float(np.mean([val_of(C.CONDITIONS["proposed"], s) for s in C.SEEDS])))
h.finalize()
import sys
if C.CONDITIONS["proposed"].get("dropout") == 0.3:
    sys.exit(3)  # like the real run: metric printed, then the process fails
'''
seed_cfg = (TASK / "seed_project" / "rb_config.py").read_text()
run_dir = Path(tempfile.mkdtemp())
exp0 = run_dir / "stage-10" / "experiment"; exp0.mkdir(parents=True)
(exp0 / "main.py").write_text(TOY_MAIN); (exp0 / "rb_config.py").write_text(seed_cfg)
for name in ("rb_data.py", "rb_loader.py", "rb_text.py", "rb_train.py", "rb_model.py"):
    (exp0 / name).write_text(f"# {name}\n")
(run_dir / "stage-09").mkdir(); (run_dir / "stage-09" / "exp_plan.yaml").write_text("conditions: [baseline_graphsage, baseline_tuned, proposed]\n")
s12 = run_dir / "stage-12" / "runs"; s12.mkdir(parents=True)
(s12 / "run-1.json").write_text(json.dumps({"run_id": "run-1", "status": "completed", "metrics": {
    "primary_metric": 0.70, "proposed_val_roc_auc_mean": 0.70, "proposed_val_roc_auc_std": 0.022, "proposed_test_roc_auc_mean": 0.63,
    "baseline_graphsage_n_seeds": 10, "baseline_tuned_n_seeds": 10, "proposed_n_seeds": 10},
    "stdout": "proposed_test_roc_auc_mean: 0.63\nprimary_metric: 0.70\n", "structured_results": {"metrics": {"proposed_test_roc_auc_mean": 0.63}}}))

cfg = RCConfig.load(str(TASK.parent / "config.arc.relbench.yaml"), check_paths=False)
exp = dataclasses.replace(cfg.experiment, max_iterations=5, time_budget_sec=120,
                          sandbox=dataclasses.replace(cfg.experiment.sandbox, python_path=sys.executable))
cfg = dataclasses.replace(cfg, experiment=exp)

class Resp:
    def __init__(s, c): s.content, s.finish_reason, s.total_tokens, s.usage, s.model = c, "stop", 1, {}, "fake"
answers = iter([
    '{"overrides": {"aggr": "max"}, "rationale": "max aggregation"}',                                                  # 1: ok -> 0.80
    'I think we should try something', 'still not json',                                                              # 2: invalid x2 -> fallback
    '{"overrides": {"aggr": "max", "channels": 64}, "rationale": "narrower"}',                                         # 3: ok -> 0.85
    '{"overrides": {"aggr": "max", "channels": 64, "dropout": 0.3}}',                                                 # 4: exits 3 after printing a better metric
    '{"overrides": {"aggr": "max", "channels": 64, "residual": true}}',                                               # 5: worse
])
prompts = []
sys.path.insert(0, str(TASK / "patches"))
import researchclaw.pipeline.stage_impls._arc_refine as _pkg_arc
_orig_fallback = _pkg_arc._fallback
_pkg_arc._fallback = lambda space_cfg, best, seen, iteration: {"enc_layers": 2}   # deterministic, harmless for the toy (pass 1 only)
class LLM:
    def chat(self, messages, **kw):
        prompts.append(messages[-1]["content"]); return Resp(next(answers))

stage_dir = run_dir / "stage-13"; stage_dir.mkdir()
res = _execute_iterative_refine(stage_dir, run_dir, cfg, AdapterBundle(), llm=LLM(), prompts=PromptManager())
assert str(res.status).endswith("DONE"), res
log = json.loads((stage_dir / "refinement_log.json").read_text())
its = log["iterations"]
print("iterazioni:", [(i["iteration"], i.get("arc_overrides"), None if i["metric"] is None else round(i["metric"], 3), i["improved"], i.get("arc_source"), i.get("arc_rejected")) for i in its])

assert [i["improved"] for i in its][:3] == [True, False, True], [i["improved"] for i in its]
assert its[0]["metric"] > 0.79 and its[2]["metric"] > 0.84 and its[1]["metric"] < 0.72
assert its[1]["arc_source"] == "fallback"                                  # proposte non valide -> ricerca deterministica
assert its[3]["metric"] is None and "exit code 3" in (its[3].get("arc_rejected") or ""), its[3].get("arc_rejected")
# senza il filtro 0.872 sarebbe stato accettato come nuovo best (e' esattamente cio' che accadde nella run reale)
assert not its[4]["improved"]                                              # 0.81 < best 0.85
assert abs(log["best_metric"] - its[2]["metric"]) < 1e-9, log["best_metric"]
print("OK 1: accettazioni, fallback, rifiuto del run in crash, nessun miglioramento falso")

final = {p.name: p.read_text() for p in (stage_dir / "experiment_final").glob("*.py")}
assert final["main.py"] == TOY_MAIN and all(final[n] == f"# {n}\n" for n in ("rb_data.py", "rb_loader.py", "rb_text.py", "rb_train.py"))
import importlib.util
sys.path.insert(0, str(TASK / "patches")); import _arc_refine as A
assert A.read_overrides(final["rb_config.py"], "PROPOSED_OVERRIDES") == {"aggr": "max", "channels": 64}
orig = seed_cfg.splitlines(); new = final["rb_config.py"].splitlines()
changed = [l for l in new if l not in orig]
assert len(changed) == 1 and changed[0].startswith("PROPOSED_OVERRIDES"), changed
print("OK 2: il progetto finale differisce dal seed solo per PROPOSED_OVERRIDES:", changed[0])

conf = json.loads((stage_dir / "confirmation.json").read_text())
assert conf["valid"] and conf["seed_offset"] == 100 and conf["metrics"]["proposed_n_seeds"] == 10
best = next(i for i in its if i["version_dir"] == log["best_version"])
sbx = best.get("sandbox_after_fix") or best["sandbox"]
assert "confirm_proposed_val_roc_auc_mean" in sbx["metrics"] and "confirm_proposed_test_roc_auc_mean" in sbx["metrics"]
assert (stage_dir / "confirmation.md").exists()
print("OK 3: conferma su semi nuovi (offset 100) prodotta e passata allo stage 14:", {k: round(v, 3) for k, v in conf["metrics"].items() if k.startswith("proposed") and "mean" in k})

blob = "\n".join(prompts)
assert "test_roc_auc" not in blob and "0.63" not in blob and "0.9" not in blob.replace("0.95", ""), "numeri di test nel prompt!"
assert "REJECTED" in blob or "FAILED" in blob                               # l'LLM vede il tentativo fallito
print("OK 4: nessun numero di test nei prompt dell'LLM; i fallimenti sono nella storia")
# ---- 2nd pass: the pipeline archives pass 1 as stage-13_v1 and runs stage 13 again
import shutil
shutil.move(str(stage_dir), str(run_dir / "stage-13_v1"))
stage2 = run_dir / "stage-13"; stage2.mkdir()
answers2 = iter([
    '{"overrides": {"aggr": "max", "channels": 64}}',                    # already evaluated in pass 1 -> must be refused
    '{"overrides": {"aggr": "max", "channels": 64}}',                    # ... again -> fallback
    '{"overrides": {"aggr": "max", "channels": 64, "norm": "layer_norm"}, "rationale": "norm"}',   # worse than best (toy ignores norm) -> no gain
])
prompts2 = []
class LLM2:
    def chat(self, messages, **kw):
        prompts2.append(messages[-1]["content"]); return Resp(next(answers2))
os.environ["ARC_PRESERVE_FILENAMES"] = "1"
_pkg_arc._fallback = _orig_fallback            # pass 2 uses the REAL fallback: it must avoid everything already evaluated
cfg2 = dataclasses.replace(cfg, experiment=dataclasses.replace(cfg.experiment, max_iterations=2))
res2 = _execute_iterative_refine(stage2, run_dir, cfg2, AdapterBundle(), llm=LLM2(), prompts=PromptManager())
log2 = json.loads((stage2 / "refinement_log.json").read_text())
first = log2["iterations"][0]
assert first["iteration"] == 0 and first["arc_overrides"] == {"aggr": "max", "channels": 64} and first.get("arc_carried_from"), first
assert log2["best_version"] == "experiment_v0/" and abs(log2["best_metric"] - 0.852) < 0.01, (log2["best_version"], log2["best_metric"])
assert A.read_overrides((stage2 / "experiment_final" / "rb_config.py").read_text(), "PROPOSED_OVERRIDES") == {"aggr": "max", "channels": 64}
joined = "\n".join(prompts2)
assert "#1:" in prompts2[0] and '"aggr": "max"' in prompts2[0], "la storia della passata 1 non e' nel prompt"
assert sum(1 for it in log2["iterations"][1:] if it.get("arc_source") == "llm") <= 1                      # il duplicato non e' stato accettato
assert all(canon_ not in [A.canon(i2.get("arc_overrides") or {}) for i2 in json.loads((run_dir / "stage-13_v1" / "refinement_log.json").read_text())["iterations"]]
           for canon_ in [A.canon(it["arc_overrides"]) for it in log2["iterations"][1:] if it.get("arc_overrides") is not None])
print("OK 5: seconda passata: storia condivisa, partenza dal migliore (iterazione 0 riportata), nessuna configurazione ripetuta")

# ---- method ground-truth file + paired stats
mt = A.method_text()
assert "GROUND TRUTH" in mt and "`aggr` = 'max'" in mt and "`channels` = 64" in mt, mt[:400]
assert "paired test difference proposed - baseline_tuned" in mt and "paired validation difference proposed - baseline_tuned" in mt
assert "projection" in mt                                                                                     # la regola 'non inventare' e' presente
conf2 = json.loads((stage_dir.parent / "stage-13_v1" / "confirmation.json").read_text())
assert conf2["paired"]["proposed-baseline_tuned:val"]["n"] == 10
print("OK 6: file del metodo (impostazioni reali, numeri di conferma, differenze appaiate)")
# il file del metodo arriva ai prompt di analisi e paper, ma NON a quelli di raffinamento
pm = PromptManager()
pa = pm.for_stage("paper_draft", topic="T", outline="O", hypotheses="H", analysis="A", results="R", literature="L").user if False else None
for st_ in ("paper_draft", "result_analysis", "peer_review"):
    kw = {k: "x" for k in ("topic", "outline", "hypotheses", "analysis", "results", "literature", "draft", "experiment_summary",
                           "paper", "reviews", "synthesis", "metric_key", "metric_direction", "experiment_results", "context", "figures")}
    try:
        txt = pm.for_stage(st_, **kw).user
    except Exception:
        txt = ""
    assert "GROUND TRUTH ABOUT THE EVALUATED METHOD" in txt, st_
for sub in ("iterative_improve",):
    assert "GROUND TRUTH" not in pm.sub_prompt(sub, metric_key="m", metric_direction="maximize", files_context="", run_summaries="",
                                                condition_coverage_hint="", topic="t", exp_plan_anchor="").user
print("OK 7: il file del metodo e' iniettato nei prompt di analisi/paper e non in quelli di raffinamento")
print("STAGE13 CONFIG MODE TEST PASSED")
