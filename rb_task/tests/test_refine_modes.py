#!/usr/bin/env python3
"""Unit tests of the stage-13 modes (gate, guard, config proposals, confirmation). No GPU, no LLM, no data."""
import json, sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "patches")]
import _arc_refine as A

SEED = HERE.parent / "seed_project"
SPACE = json.loads((HERE.parent / "task_spec" / "search_space.json").read_text())
CFG = (SEED / "rb_config.py").read_text()

# 1) validate_overrides
ok, errs = A.validate_overrides(SPACE, {"aggr": "max", "residual": True, "dropout": 0, "num_layers": 2})
assert ok == {"aggr": "max", "residual": True}, ok          # 0 -> 0.0 e num_layers=2 sono i default -> scartati
assert not errs, errs
ok, errs = A.validate_overrides(SPACE, {"aggr": "median", "foo": 1, "channels": 100, "residual": 1})
assert ok == {} and len(errs) == 4, (ok, errs)               # residual=1 (int) non e' un bool consentito
assert A.validate_overrides(SPACE, {"dropout": 0.1})[0] == {"dropout": 0.1}
assert A.validate_overrides(SPACE, "x")[1]
# dipendenze: heads conta solo per gatv2/transformer, aggr solo per sage
assert A.validate_overrides(SPACE, {"aggr": "max", "heads": 8})[0] == {"aggr": "max"}
assert A.validate_overrides(SPACE, {"gnn_type": "transformer", "heads": 8, "aggr": "max"})[0] == {"gnn_type": "transformer", "heads": 8}
assert A.validate_overrides(SPACE, {"gnn_type": "gin", "aggr": "mean"})[0] == {"gnn_type": "gin"}
assert A.canon(A.validate_overrides(SPACE, {"aggr": "max", "heads": 8})[0]) == A.canon({"aggr": "max"})
assert not any("heads" in c for c in A._neighbours(SPACE, {"aggr": "max"}))                       # nessun vicino inutile
assert any("heads" in c for c in A._neighbours(SPACE, {"gnn_type": "transformer"}))
print("OK 1: validate_overrides (+ dipendenze tra chiavi)")

# 2) read/write sul vero rb_config.py
assert A.read_overrides(CFG, "PROPOSED_OVERRIDES") == {}
new = A.write_overrides(CFG, "PROPOSED_OVERRIDES", {"aggr": "max", "residual": True, "gnn_type": "transformer"})
assert A.read_overrides(new, "PROPOSED_OVERRIDES") == {"aggr": "max", "gnn_type": "transformer", "residual": True}
compile(new, "rb_config.py", "exec")
assert new.replace(new[new.index("PROPOSED_OVERRIDES = {"):].splitlines()[0], "") .count("\n") >= CFG.count("\n") - 1
assert A.write_overrides("x = 1\n", "PROPOSED_OVERRIDES", {}) is None
print("OK 2: read/write_overrides (il file resta compilabile)")

# 3) guard
best = {"main.py": "MAIN\n", "rb_data.py": "DATA\n", "rb_config.py": CFG, "rb_model.py": "MODEL\n"}
evil_cfg = CFG.replace("SEED_OFFSET = int", "SEED_OFFSET = 0  # hacked\nSEED_OFFSET2 = int", 1).replace(
    "PROPOSED_OVERRIDES = {}", "PROPOSED_OVERRIDES = {'aggr': 'max', 'bogus': 3, 'channels': 100}")
cand = {"main.py": "[rb_config content]", "rb_data.py": "DATA\n", "rb_config.py": evil_cfg,
        "rb_model.py": "MODEL v2\n", "extra.py": "x"}
import os
os.environ["ARC_SEARCH_MODE"] = "config"
out, notes = A.guard_candidate(best, cand, SPACE, ["main.py", "rb_data.py"])
assert out["main.py"] == "MAIN\n" and out["rb_data.py"] == "DATA\n"
assert A.read_overrides(out["rb_config.py"], "PROPOSED_OVERRIDES") == {"aggr": "max"}   # bogus + channels=100 scartati
assert "hacked" not in out["rb_config.py"] and out["rb_model.py"] == "MODEL v2\n"       # rb_model resta modificabile
assert any("restored protected file main.py" in n for n in notes), notes
print("OK 3: guard (main.py ripristinato, rb_config solo PROPOSED_OVERRIDES validato, rb_model libero in code mode)")
# modalita' codice: chiavi nuove ammesse (componenti implementati dall'LLM), PROPOSED_SOURCE conservato, il resto ripristinato
os.environ["ARC_SEARCH_MODE"] = "code"
cand_c = dict(cand); cand_c["rb_config.py"] = evil_cfg.replace("PROPOSED_OVERRIDES = {'aggr': 'max', 'bogus': 3, 'channels': 100}",
    "PROPOSED_OVERRIDES = {'gnn_type': 'relgnn', 'routes': 2}").replace('PROPOSED_SOURCE = ""', 'PROPOSED_SOURCE = "K1: atomic routes"')
outc, _ = A.guard_candidate(best, cand_c, SPACE, ["main.py", "rb_data.py"])
assert A.read_overrides(outc["rb_config.py"], "PROPOSED_OVERRIDES") == {"gnn_type": "relgnn", "routes": 2}
assert "PROPOSED_SOURCE = 'K1: atomic routes'" in outc["rb_config.py"] and "hacked" not in outc["rb_config.py"]
cand_l = dict(cand_c); cand_l["rb_config.py"] = cand_c["rb_config.py"].replace("'routes': 2}", "'routes': 2, 'lr': 0.001, 'batch_size': 512}")
outl, notes_l = A.guard_candidate(best, cand_l, SPACE, ["main.py", "rb_data.py"])
assert A.read_overrides(outl["rb_config.py"], "PROPOSED_OVERRIDES") == {"gnn_type": "relgnn", "routes": 2}, "lr/batch_size devono sparire"
assert any("training-recipe keys" in n for n in notes_l)
os.environ["ARC_SEARCH_MODE"] = "config"
cand_v = dict(cand_c); cand_v["vendor_relgt_model.py"] = "# edited by the LLM"; cand_v["vendor_new.py"] = "x = 1"
best_v = dict(best); best_v["vendor_relgt_model.py"] = "# official"
outv, notes_v = A.guard_candidate(best_v, cand_v, SPACE, ["main.py"])
assert outv["vendor_relgt_model.py"] == "# official" and "vendor_new.py" not in outv, "i file vendor_ sono di sola lettura"
print("OK 3b: guard in modalita' codice (chiavi nuove ammesse, PROPOSED_SOURCE conservato, resto ripristinato)")

# 4) gate
def run(rc=0, m=None, to=False): return SimpleNamespace(returncode=rc, metrics=m, timed_out=to)
exp = {"seeds": 10, "conditions": ["baseline_graphsage", "baseline_tuned", "proposed"]}
good = {"primary_metric": 0.78, "baseline_graphsage_n_seeds": 10, "baseline_tuned_n_seeds": 10, "proposed_n_seeds": 10}
assert A.run_is_valid(run(0, good), exp) == (True, "")
assert not A.run_is_valid(run(1, good), exp)[0]                                           # exit code != 0
assert not A.run_is_valid(run(0, good, to=True), exp)[0]
assert not A.run_is_valid(run(0, {**good, "proposed_n_seeds": 3, "baseline_graphsage_n_seeds": 3, "baseline_tuned_n_seeds": 3}), exp)[0]
partial = {"primary_metric": 0.7862, "baseline_graphsage_n_seeds": 10}                      # come l'iterazione 5 del run reale
assert not A.run_is_valid(run(1, partial), exp)[0] and not A.run_is_valid(run(0, partial), exp)[0]
assert not A.run_is_valid(run(0, {**good, "primary_metric": float("nan")}), exp)[0]
assert not A.run_is_valid(run(0, {k: v for k, v in good.items() if k != "baseline_tuned_n_seeds"}), exp)[0]
print("OK 4: gate (rc!=0, timeout, semi diversi, metriche parziali, NaN, condizione mancante)")

# 5) margine
assert A.margin_ok(0.790, 0.780, "maximize", 0.005) and not A.margin_ok(0.782, 0.780, "maximize", 0.005)
assert A.margin_ok(0.770, 0.780, "minimize", 0.005) and A.margin_ok(0.5, None, "maximize", 0.1)
print("OK 5: margine di miglioramento")

# 6) proposte: JSON valido, JSON con testo/think, invalido -> riprova -> fallback, duplicato
class St:  # ModeState minimale
    space, expected, margin, topic = SPACE, {"seeds": 10, "se": 0.007}, 0.005, "T"
    prev_logs = []
    config_mode, mode = True, "config"
best_files = {"rb_config.py": CFG}
log = {"iterations": [{"arc_overrides": {"aggr": "max"}, "metric": 0.85, "improved": True}]}
def chat_ret(*texts):
    it = iter(texts)
    return lambda llm, s, u, **k: SimpleNamespace(content=next(it))
r = A.propose_config(chat_ret('<think>hm</think> ok {"overrides": {"gnn_type": "transformer"}, "rationale": "try attention"}'),
                     None, St, best_files, log, 2, 0.85, 0.78)
assert A.read_overrides(A._extract_json(f'{{"overrides": {{}}}}') and r.content.split("\n", 1)[1].rsplit("\n```", 1)[0], "PROPOSED_OVERRIDES") == {"gnn_type": "transformer"}
assert A.LAST["source"] == "llm" and A.LAST["rationale"] == "try attention"
r = A.propose_config(chat_ret("not json", '{"overrides": {"aggr": "median"}}'), None, St, best_files, log, 3, 0.85, 0.78)
assert A.LAST["source"] == "fallback" and A.LAST["overrides"] and A.LAST["overrides"] != {}, A.LAST
fb1 = dict(A.LAST["overrides"])
A.propose_config(chat_ret("x", "y"), None, St, best_files, log, 3, 0.85, 0.78); assert A.LAST["overrides"] == fb1   # deterministico
r = A.propose_config(chat_ret('{"overrides": {"aggr": "max"}}', '{"overrides": {"aggr": "max"}}'), None, St, best_files, log, 4, 0.85, 0.78)
assert A.LAST["source"] == "fallback"                                                                           # duplicato rifiutato
r = A.propose_config(chat_ret('{"overrides": {"aggr": "mean", "residual": true, "jk": "cat", "dropout": 0.3}}', '{"overrides": {"aggr": "sum", "residual": true}}'),
                     None, St, best_files, log, 5, 0.85, 0.78)   # 4+ chiavi diverse dal best -> rifiutato; il secondo tentativo e' valido
assert A.LAST["source"] == "llm" and A.LAST["overrides"] == {"residual": True}, A.LAST
print("OK 6: propose_config (JSON, think, retry, fallback deterministico, duplicati, max chiavi)")

# 7) prompt di proposta: contiene storia e regole, MAI numeri di test
sysm, usr = A.build_proposal_prompt(SPACE, A._evaluated(log), {"aggr": "max"}, 0.85, 0.78, St.expected, 0.005, "T", 3)
assert "aggr" in usr and "0.8500" in usr and "RULES" in usr and "test" not in usr.lower().replace("latest", "").replace("contest", "")
print("OK 7: prompt di proposta senza riferimenti al test")

# 8) conferma: SEED_OFFSET riscritto nel vero rb_config
f = A.make_confirm_files({"rb_config.py": CFG}, 100)
assert "SEED_OFFSET = 100" in f["rb_config.py"] and A.make_confirm_files({"rb_config.py": "x=1"}, 100) is None
print("OK 8: file di conferma con SEED_OFFSET=100")

# 9) memoria tra passate e partenza dal migliore (funzioni pure)
prev = [{"generated": "1", "iterations": [
            {"iteration": 1, "metric": 0.80, "arc_overrides": {"aggr": "max"}, "sandbox": {"metrics": {"m": 1}}, "improved": True},
            {"iteration": 2, "metric": 0.70, "arc_overrides": {"gnn_type": "gin"}},
            {"iteration": 3, "metric": 0.95, "arc_overrides": {"aggr": "mean"}, "arc_rejected": "exit code 1"},
            {"iteration": 4, "metric": 0.83, "arc_overrides": {"heads": 8}, "improved": False}]}]  # not accepted (margin)
class St2(St): prev_logs = prev
rows = A._evaluated({"iterations": [{"arc_overrides": {"dropout": 0.1}, "metric": 0.75}]}, prev)
assert [A.canon(r[0]) for r in rows] == [A.canon(x) for x in ({}, {"aggr": "max"}, {"gnn_type": "gin"}, {"aggr": "mean"}, {"heads": 8}, {"dropout": 0.1})]
ws = A.warm_start(St2, {"rb_config.py": CFG}, 0.78, "maximize")
assert ws and ws["overrides"] == {"aggr": "max"} and ws["metric"] == 0.80                    # ne' il run rifiutato (0.95) ne' quello non accettato (0.83)
assert ws["record"]["iteration"] == 0 and ws["record"]["arc_carried_from"] and A.read_overrides(ws["files"]["rb_config.py"], "PROPOSED_OVERRIDES") == {"aggr": "max"}
assert A.warm_start(St2, {"rb_config.py": CFG}, 0.90, "maximize") is None                    # il corrente e' migliore: nessuna partenza
assert A.warm_start(St2, {"rb_config.py": CFG}, 0.80, "maximize") is not None                # pari (metrica recuperata da upstream): si'
assert [r for r in A._evaluated({"iterations": [ws["record"]]}, [])] == [({}, None, "initial")]   # i record riportati non si contano due volte
print("OK 9: memoria tra passate e partenza dal migliore")

# 10) statistiche appaiate
res = [{"condition": c, "seed": s, "val": v + 0.1 * (c == "proposed"), "test": v} for c in ("proposed", "baseline_tuned") for s, v in enumerate([0.70, 0.72, 0.71, 0.69, 0.73, 0.70])]
st = A.paired_stats(res, "proposed", "baseline_tuned", "val")
assert st["n"] == 6 and abs(st["mean_diff"] - 0.1) < 1e-9 and st["seeds_better"] == 6 and st["ci95"][0] > 0.09
assert abs(A.paired_stats(res, "proposed", "baseline_tuned", "test")["mean_diff"]) < 1e-12 and A.paired_stats(res, "proposed", "nonexistent", "val") is None
print("OK 10: statistiche appaiate (media, IC, semi migliori, test di permutazione)")
# 11) l'errore vero arriva all'LLM anche se lo stderr e' pieno di warning
rec = {"sandbox": {"stderr": "x.py:1: UserWarning: Weights only load failed\n  warnings.warn(\n" * 30 +
                   "Traceback (most recent call last):\n  File \"/a/experiment_v3/rb_model.py\", line 99, in __init__\n"
                   "ValueError: 'add_self_loops' attribute set to 'True' on module GATv2Conv"}}
ex = A.error_excerpt(rec)
assert "add_self_loops" in ex and "Weights only" not in ex, ex
print("OK 11: estratto dell'errore senza i warning")

# 12) ripartenza in modalita' codice: tutti i file della versione migliore della passata precedente
import tempfile
from pathlib import Path as _P
d = _P(tempfile.mkdtemp()); (d / "stage-13_v1" / "experiment_v2").mkdir(parents=True)
(d / "stage-13_v1" / "experiment_v2" / "rb_model.py").write_text("# best model\n")
(d / "stage-13_v1" / "experiment_v2" / "rb_config.py").write_text(CFG)
(d / "stage-13_v1" / "refinement_log.json").write_text(json.dumps({"generated": "1", "iterations": [
    {"iteration": 1, "metric": 0.75, "version_dir": "experiment_v1/", "improved": True},
    {"iteration": 2, "metric": 0.82, "version_dir": "experiment_v2/", "improved": True}]}))
class St3(St):
    prev_logs = A.previous_passes(d); config_mode = False; mode = "code"
ws = A.warm_start(St3, {"rb_config.py": CFG, "rb_model.py": "# seed\n"}, 0.78, "maximize")
assert ws and ws["metric"] == 0.82 and ws["files"]["rb_model.py"] == "# best model\n", ws and ws["files"].keys()
print("OK 12: ripartenza in modalita' codice dai file della versione migliore")
# 13) riparazione: un blocco di codice senza nome va nel file giusto (non in main.py)
files = {"main.py": "import rb_config\nprint(1)\n", "rb_model.py": "def build_model(d, c, cfg, o):\n    pass\n", "rb_config.py": CFG}
assert A.target_for_block("import torch\ndef build_model(data, col_stats_dict, cfg, out_channels):\n    return 1\n", files) == "rb_model.py"
assert A.target_for_block("PROPOSED_OVERRIDES = {}\n", files) == "rb_config.py"
assert A.target_for_block("import rb_config\nprint(2)\n", files) == "main.py"
print("OK 13: blocco di riparazione senza nome assegnato al file giusto")

# 14) candidato identico alla versione migliore -> rifiutato (rieseguire lo stesso codice misura solo rumore)
os.environ["ARC_SEARCH_MODE"] = "code"
same, _ = A.guard_candidate(best, dict(best), SPACE, ["main.py"])
class StC(St):
    mode = "code"; config_mode = False
ok, why = A.knowledge_gate(type("R", (), {"metrics": {}})(), same, StC)
assert not ok and "nothing changed" in why, why
diff_c = dict(best); diff_c["rb_model.py"] = "MODEL v3\n"
A.guard_candidate(best, diff_c, SPACE, ["main.py"])
assert not A.LAST_GUARD["unchanged"]
os.environ["ARC_SEARCH_MODE"] = "config"
assert A.no_gain_value(0.8, "maximize") < 0.8 and A.no_gain_value(0.8, "minimize") > 0.8
print("OK 14: candidato identico al migliore rifiutato; valore 'senza guadagno' coerente con la direzione")
# 15) codice ufficiale importato, tentativi saltati senza attivare la riparazione
assert A.official_imports({"rb_model.py": "import torch\nfrom vendor_relgt_model import RelGTLayer\nimport vendor_relgt_encoders as E\n",
                           "vendor_relgt_model.py": "from vendor_relgt_local_module import LocalModule\n"}) == ["vendor_relgt_encoders", "vendor_relgt_model"]
A.LAST_GUARD["unchanged"] = True
assert A.skip_run()
st = A.skipped_run().stderr
assert not [kw for kw in ("Warning", "Error", "Traceback", "Exception", "divide", "overflow", "invalid value", "NaN", "inf") if kw in st]
A.LAST_GUARD["unchanged"] = False
print("OK 15: import del codice ufficiale rilevati; i tentativi identici vengono saltati senza far scattare la riparazione")
print("REFINE MODES TESTS PASSED")
