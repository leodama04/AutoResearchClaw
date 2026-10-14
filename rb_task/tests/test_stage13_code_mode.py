#!/usr/bin/env python3
"""End-to-end test of stage 13 in CODE MODE (real sandbox subprocess, toy experiment, fake LLM).

Checks that: the knowledge file (implementation cards) and the project skills reach the code-writing prompt;
protected files and the rest of rb_config.py are restored; an attempt without a valid card id is rejected even if
its metric is better; an attempt that leaves `proposed` identical to the baseline is rejected; good attempts are
accepted; the final project keeps the official model and the seeds.
Needs the patched pipeline (rb_task/patches/apply_relbench_patches.py). ARC_ROOT = repo root (default /app).
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
    "ARC_MIN_IMPROVEMENT": "0.005", "ARC_KEEP_SEEDS": "1", "ARC_PRESERVE_FILENAMES": "1", "ARC_HIDE_TEST_METRICS": "1",
    "ARC_REFINE_PATIENCE": "10", "ARC_MAX_NO_METRICS": "10", "ARC_KNOWLEDGE_FILE": str(know),
    "ARC_RUN_STARTED_AT": str(time.time() - 60), "ARC_REQUIRE_KNOWLEDGE_REF": "1",
    "ARC_REQUIRE_COMPONENT_MATCH": "1", "ARC_MAX_REFINE_ITERS": "1000",
})

from researchclaw.adapters import AdapterBundle  # noqa: E402
from researchclaw.config import RCConfig  # noqa: E402
from researchclaw.pipeline.stage_impls._execution import _execute_iterative_refine  # noqa: E402
from researchclaw.prompts import PromptManager  # noqa: E402

TOY_MAIN = '''
import experiment_harness
import rb_config as C
import numpy as np
from pathlib import Path

def val_of(cfg, seed):
    v = 0.70 + 0.10 * (cfg.get("gnn_type") == "reltoy") + 0.03 * (cfg.get("dropout") == 0.2)
    return v + 0.003 * np.sin(seed * 12.9898)

h = experiment_harness.get_harness(time_budget=60)
if "CRASH" in Path("rb_model.py").read_text():
    raise RuntimeError("toy crash: the model code is broken")
same_code = Path("rb_model.py").read_text().strip() == Path("rb_model_official.py").read_text().strip()
identical = 1.0 if (not C.PROPOSED_OVERRIDES and same_code) else 0.0
h.report_metric("proposed_identical_to_baseline", identical)
for name, cfg in C.CONDITIONS.items():
    vals = [val_of(cfg, s) for s in C.SEEDS]
    for s_, v_ in zip(C.SEEDS, vals):
        h.log_result({"condition": name, "seed": s_, "val": float(v_), "test": float(v_) * 0.9})
    h.report_metric(f"{name}_val_roc_auc_mean", float(np.mean(vals)))
    h.report_metric(f"{name}_val_roc_auc_std", float(np.std(vals, ddof=1)))
    h.report_metric(f"{name}_test_roc_auc_mean", float(np.mean(vals)) * 0.9)
    h.report_metric(f"{name}_n_seeds", float(len(vals)))
h.report_metric("primary_metric", float(np.mean([val_of(C.CONDITIONS["proposed"], s) for s in C.SEEDS])))
h.finalize()
'''
seed_cfg = (TASK / "seed_project" / "rb_config.py").read_text()
run_dir = tmp / "run"
exp0 = run_dir / "stage-10" / "experiment"
exp0.mkdir(parents=True)
(exp0 / "main.py").write_text(TOY_MAIN)
(exp0 / "rb_config.py").write_text(seed_cfg)
(exp0 / "rb_model.py").write_text("# model v0\n")
(exp0 / "rb_model_official.py").write_text("# model v0\n")
for name in ("rb_data.py", "rb_loader.py", "rb_text.py", "rb_train.py"):
    (exp0 / name).write_text(f"# {name}\n")
(run_dir / "stage-09").mkdir()
(run_dir / "stage-09" / "exp_plan.yaml").write_text("conditions: [baseline_graphsage, baseline_tuned, proposed]\n")
s12 = run_dir / "stage-12" / "runs"
s12.mkdir(parents=True)
(s12 / "run-1.json").write_text(json.dumps({"run_id": "run-1", "status": "completed", "metrics": {
    "primary_metric": 0.70, "proposed_val_roc_auc_mean": 0.70, "proposed_val_roc_auc_std": 0.003,
    "baseline_graphsage_n_seeds": 10, "baseline_tuned_n_seeds": 10, "proposed_n_seeds": 10}, "stdout": "primary_metric: 0.70\n"}))

def cfg_with(overrides: str, source: str, extra: str = "") -> str:
    t = seed_cfg.replace("PROPOSED_OVERRIDES = {}", f"PROPOSED_OVERRIDES = {overrides}", 1)
    t = t.replace('PROPOSED_SOURCE = ""', f"PROPOSED_SOURCE = {source!r}", 1)
    return t + extra

def blocks(**files) -> str:
    return "\n".join(f"```filename:{name}\n{text}\n```" for name, text in files.items())

answers = iter([
    # 1: valid change from K1 + an attempt to edit a protected file -> accepted, main.py restored
    blocks(**{"rb_config.py": cfg_with('{"gnn_type": "reltoy"}', "K1: RelToyConv"),
              "rb_model.py": "# model v1 with RelToyConv\n", "main.py": "print('hacked')\n"}),
    # 2: better metric but no card cited -> rejected
    blocks(**{"rb_config.py": cfg_with('{"gnn_type": "reltoy", "dropout": 0.2}', "")}),
    # 3: overrides removed and model reverted -> identical to baseline -> rejected
    blocks(**{"rb_config.py": cfg_with("{}", "K1: nothing"), "rb_model.py": "# model v0\n"}),
    # 4: valid improvement + tries to change the seeds -> accepted, seeds restored
    blocks(**{"rb_config.py": cfg_with('{"gnn_type": "reltoy", "dropout": 0.2, "lr": 0.001}', "K1: RelToyConv max over edge types",
                                        "\nSEEDS = [0]\n")}),
    # 5: cites K1 but the component is not in the card -> rejected
    blocks(**{"rb_config.py": cfg_with('{"gnn_type": "reltoy", "dropout": 0.2, "heads": 8}', "K1: GATv2 attention with LayerNorm")}),
    # 6: same files as the current best -> rejected (nothing changed)
    blocks(**{"rb_model.py": "# model v1 with RelToyConv"}),
    # 7: crash; the repair answers with an UNLABELLED block that must go to rb_model.py, not main.py
    blocks(**{"rb_config.py": cfg_with('{"gnn_type": "reltoy", "dropout": 0.2, "channels": 64}', "K1: RelToyConv max over edge types"),
              "rb_model.py": "# model v2 CRASH"}),
    "Here is the fix:\n```python\ndef build_model(data, col_stats_dict, cfg, out_channels):\n    return None  # fixed\n```\n",
])
prompts = []

class Resp:
    def __init__(s, c):
        s.content, s.finish_reason, s.total_tokens, s.usage, s.model = c, "stop", 1, {}, "fake"

class LLM:
    def chat(self, messages, **kw):
        prompts.append(messages[-1]["content"])
        return Resp(next(answers, ""))

cfg = RCConfig.load(str(TASK.parent / "config.arc.relbench.code.yaml"), check_paths=False)
cfg = dataclasses.replace(cfg, experiment=dataclasses.replace(
    cfg.experiment, max_iterations=12, time_budget_sec=120,
    sandbox=dataclasses.replace(cfg.experiment.sandbox, python_path=sys.executable)))
stage_dir = run_dir / "stage-13"
stage_dir.mkdir()
res = _execute_iterative_refine(stage_dir, run_dir, cfg, AdapterBundle(), llm=LLM(), prompts=PromptManager())
log = json.loads((stage_dir / "refinement_log.json").read_text())
its = log["iterations"]
print("iterazioni:", [(i["iteration"], None if i["metric"] is None else round(i["metric"], 3), i["improved"], i.get("arc_rejected", "")[:45]) for i in its])

assert its[0]["improved"] and its[0]["metric"] > 0.79
assert its[1]["metric"] is None and "PROPOSED_SOURCE" in its[1]["arc_rejected"]
assert its[2]["metric"] is None and "identical" in its[2]["arc_rejected"]
assert its[3]["improved"] and its[3]["metric"] > 0.82
print("OK 1: accettato (K1), rifiutato senza scheda, rifiutato perche' identico al baseline, accettato (K1)")

final = {p.name: p.read_text() for p in (stage_dir / "experiment_final").glob("*.py")}
assert final["main.py"] == TOY_MAIN and final["rb_model_official.py"] == "# model v0\n"
assert final["rb_model.py"].strip() == "# model v1 with RelToyConv"
assert "SEEDS = [0]" not in final["rb_config.py"] and "SEED_OFFSET + i for i in range(N_SEEDS)" in final["rb_config.py"]
assert "PROPOSED_SOURCE = 'K1: RelToyConv max over edge types'" in final["rb_config.py"]
assert "'lr'" not in final["rb_config.py"].split("PROPOSED_OVERRIDES =", 1)[1].split("\n", 1)[0], "lr deve essere rimosso (ricetta bloccata)"
assert its[4]["metric"] is None and "not described in card" in its[4]["arc_rejected"]
print("OK 2: main.py e modello ufficiale protetti, semi ripristinati, lr (ricetta) rimosso, PROPOSED_SOURCE conservato; citazione nominale rifiutata")

improve = [p for p in prompts if "REFINEMENT" in p or "iterat" in p.lower()] or prompts
assert improve and all("### [K1] RelToy" in p for p in improve[:4]), "la conoscenza non e' nel prompt di scrittura del codice"
assert any("relbench-gnn-code" in p or "Project contract" in p for p in improve), "le skill del progetto non sono nel prompt"
assert any("PROPOSED_SOURCE does not cite" in p for p in prompts[2:]), "il motivo del rifiuto non arriva all'LLM"
print("OK 3: schede K1 e skill del progetto nel prompt di scrittura del codice; i rifiuti tornano all'LLM")
sb6 = its[5]["sandbox"]
assert its[5]["metric"] is None and "SKIPPED" in sb6["stderr"] and sb6["elapsed_sec"] == 0.0, sb6
assert not its[5].get("runtime_repaired"), "un tentativo saltato non deve attivare la riparazione"
assert len(its) == 12, f"il tetto di 10 iterazioni non e' stato rimosso: {len(its)}"
assert all("arc_official_code" in i for i in its if i.get("iteration", 0) >= 1)
assert any("official code imported: NONE" in p for p in prompts), "la storia deve dire se e' stato usato il codice ufficiale"
v7 = stage_dir / its[6]["version_dir"].strip("/")
assert (v7 / "main.py").read_text().strip() == TOY_MAIN.strip(), "main.py sovrascritto dalla riparazione"
assert "fixed" in (v7 / "rb_model.py").read_text(), "la riparazione non e' finita in rb_model.py"
assert its[6].get("runtime_repaired") and its[6]["metric"] is not None, its[6]
acc = [i for i in its if i.get("improved")]
assert acc and all("arc_recheck" in i and i["arc_recheck"]["valid"] for i in acc), [i.get("arc_recheck") for i in acc]
print("OK 4: identico al migliore saltato senza eseguirlo (12 iterazioni oltre il vecchio tetto di 10); riparazione nel file giusto con main.py protetto; ogni miglioramento ricontrollato su altri semi")
print("STAGE13 CODE MODE TEST PASSED")
