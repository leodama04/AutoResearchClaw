#!/usr/bin/env python3
"""Train the final model of a pipeline run on another task (or the same one), next to the two baselines.

Co-supervisor (call of 2026-10-13): "once you have the best network, try it on the task you optimised and on the other
tasks, to see whether it generalises"; and "optimise task 1 and task 2, then use the solution of task 1 on task 2 and
vice versa". The project of a run (stage-13/experiment_final: rb_model.py + rb_config.py with PROPOSED_OVERRIDES, plus
the vendored files it imports) is copied unchanged and run with main.py for each requested task:
  - conditions baseline_graphsage (official RDL recipe), baseline_tuned (same model, batch 128) and proposed (the run's
    model, same recipe as baseline_tuned), 10 seeds each (default seeds 100-109: never used by the pipeline to choose);
  - nothing is selected on the test split; the summary reports means and paired differences over the same seeds.
Optional --epochs N: the same number of epochs for EVERY condition (e.g. to check that a gain survives longer training).

Usage, in the container (from the repo root):
  ./run.sh transfer --projects artifacts/rc-20261013-131020-9b9601 --tasks driver-top3,driver-dnf,driver-position
  ./run.sh transfer --projects artifacts/rc-A,artifacts/rc-B --tasks driver-dnf --epochs 30
A project can be a run directory (its last stage-13 pass is used) or a directory with main.py.
Output: artifacts/transfer_<date>/ (one folder per project x task with log and results.json; summary.md / summary.json).
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
HARNESS = REPO / "researchclaw" / "experiment" / "harness_template.py"
SEED_DIR = REPO / "rb_task" / "seed_project"
# Files the pipeline never lets the LLM change (ARC_PROTECTED_FILES): with --infra current (default) they are taken from the
# current seed project, so that kit fixes apply (e.g. the rmse of regression tasks, 0.6.6); the MODEL of the run
# (rb_model.py, rb_config.py with PROPOSED_OVERRIDES, new files, vendored code) is always the run's.
INFRA = ("main.py", "rb_data.py", "rb_loader.py", "rb_text.py", "rb_train.py", "rb_model_official.py", "rb_tokens.py")
EPOCHS_HOOK = '''

# --- added by rb_task/tools/transfer_eval.py: the same number of epochs for every condition ---
import os as _tf_os
if _tf_os.environ.get("RB_EPOCHS_ALL"):
    for _tf_cfg in CONDITIONS.values():
        _tf_cfg["epochs"] = int(_tf_os.environ["RB_EPOCHS_ALL"])
'''


def resolve_project(p: str) -> tuple[Path, str]:
    """(project dir with main.py, label)."""
    path = Path(p)
    if (path / "main.py").is_file():
        return path, path.as_posix()
    passes = [path / "stage-13"] + sorted(path.glob("stage-13_v*"), key=lambda x: x.name, reverse=True)
    for d in passes:
        if (d / "experiment_final" / "main.py").is_file():
            return d / "experiment_final", f"{path.name}/{d.name}"
    raise FileNotFoundError(f"no main.py nor stage-13*/experiment_final in {p}")


def proposed_of(project: Path) -> dict:
    import re

    cfg = (project / "rb_config.py").read_text(encoding="utf-8") if (project / "rb_config.py").is_file() else ""
    ov = re.search(r"^PROPOSED_OVERRIDES\s*=\s*(.*)$", cfg, re.M)
    src = re.search(r"^PROPOSED_SOURCE\s*=\s*(.*)$", cfg, re.M)
    return {"overrides": ov.group(1).strip() if ov else "", "source": src.group(1).strip() if src else ""}


def paired(results: list, a: str, b: str, key: str, higher: bool) -> dict | None:
    """a - b over common seeds: mean, bootstrap 95% CI, exact sign-flip p, seeds where a is better."""
    va = {r["seed"]: r[key] for r in results if r.get("condition") == a and key in r}
    vb = {r["seed"]: r[key] for r in results if r.get("condition") == b and key in r}
    seeds = sorted(set(va) & set(vb))
    if len(seeds) < 3:
        return None
    d = [va[s] - vb[s] for s in seeds]
    n, mean = len(d), statistics.mean(d)
    if n <= 16:
        flips = [abs(statistics.mean([x * s for x, s in zip(d, sg)])) >= abs(mean) - 1e-12
                 for sg in itertools.product([-1, 1], repeat=n)]
        p = sum(flips) / len(flips)
    else:
        p = float("nan")
    import random

    rng = random.Random(0)
    boots = sorted(statistics.mean(rng.choice(d) for _ in range(n)) for _ in range(5000))
    better = sum(1 for x in d if (x > 0 if higher else x < 0))
    return {"n": n, "mean_diff": mean, "ci95": [boots[124], boots[4874]], "p_signflip": p, "seeds_better": better}


def run_one(project: Path, task: str, out: Path, args) -> dict:
    work = out / "project"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    for f in project.glob("*.py"):
        shutil.copy2(f, work / f.name)
    shutil.copy2(HARNESS, work / "experiment_harness.py")
    if args.infra == "current":
        for name in INFRA:
            if (SEED_DIR / name).is_file():
                shutil.copy2(SEED_DIR / name, work / name)
    if args.epochs:
        with open(work / "rb_config.py", "a", encoding="utf-8") as fh:
            fh.write(EPOCHS_HOOK)
    env = dict(os.environ, RB_DATASET=args.dataset, RB_TASK=task, RB_RECIPE="tuned", RB_SEED_OFFSET=str(args.seed_offset),
               RB_N_SEEDS=str(args.n_seeds), RB_TIME_BUDGET_SEC=str(args.time_budget), PYTHONUNBUFFERED="1")
    if args.epochs:
        env["RB_EPOCHS_ALL"] = str(args.epochs)
    t0 = time.time()
    with open(out / "log.txt", "w", encoding="utf-8") as log:
        rc = subprocess.run([sys.executable, "main.py"], cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    rec = {"returncode": rc, "seconds": round(time.time() - t0)}
    rj = work / "results.json"
    if not rj.is_file():
        rec["error"] = f"no results.json (exit code {rc}); see {out / 'log.txt'}"
        return rec
    shutil.copy2(rj, out / "results.json")
    data = json.loads(rj.read_text(encoding="utf-8"))
    res = data.get("results") or []
    if not res:
        rec["error"] = "results.json without per-seed results"
        return rec
    metric, higher = res[0].get("tune_metric", "?"), bool(res[0].get("higher_is_better", True))
    rec.update(metric=metric, higher=higher, conditions={})
    for cond in sorted({r["condition"] for r in res}):
        rows = [r for r in res if r["condition"] == cond]
        rec["conditions"][cond] = {
            "n": len(rows),
            "val_mean": statistics.mean(r["val"] for r in rows), "val_std": statistics.stdev([r["val"] for r in rows]) if len(rows) > 1 else 0.0,
            "test_mean": statistics.mean(r["test"] for r in rows), "test_std": statistics.stdev([r["test"] for r in rows]) if len(rows) > 1 else 0.0,
        }
    rec["paired"] = {f"proposed-{b}:{k}": paired(res, "proposed", b, k, higher)
                     for b in ("baseline_tuned", "baseline_graphsage") for k in ("val", "test")}
    rec["identical_to_baseline"] = (data.get("metrics") or {}).get("proposed_identical_to_baseline")
    return rec


def fmt_pair(st: dict | None) -> str:
    if not st:
        return "-"
    return (f"{st['mean_diff']:+.4f} [{st['ci95'][0]:+.4f}, {st['ci95'][1]:+.4f}] p={st['p_signflip']:.3f} "
            f"({st['seeds_better']}/{st['n']})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", required=True, help="comma-separated run dirs or project dirs")
    ap.add_argument("--tasks", default="driver-top3,driver-dnf,driver-position")
    ap.add_argument("--dataset", default="rel-f1")
    ap.add_argument("--seed-offset", type=int, default=100)
    ap.add_argument("--n-seeds", type=int, default=10)
    ap.add_argument("--epochs", type=int, default=0, help="same number of epochs for every condition (0 = recipe)")
    ap.add_argument("--time-budget", type=int, default=14400)
    ap.add_argument("--infra", choices=("current", "run"), default="current",
                    help="protected files (main.py, rb_train.py, ...) from the current kit (default) or from the run")
    ap.add_argument("--out", default=f"artifacts/transfer_{time.strftime('%Y%m%d-%H%M%S')}")
    a = ap.parse_args()
    if not HARNESS.is_file():
        print(f"missing {HARNESS}", file=sys.stderr)
        return 1
    out_root = Path(a.out)
    rows = []
    for p in [x.strip() for x in a.projects.split(",") if x.strip()]:
        project, label = resolve_project(p)
        info = proposed_of(project)
        for task in [t.strip() for t in a.tasks.split(",") if t.strip()]:
            out = out_root / f"{label.replace('/', '__')}__{task}"
            out.mkdir(parents=True, exist_ok=True)
            print(f"=== {label} on {a.dataset}/{task} (seeds {a.seed_offset}..{a.seed_offset + a.n_seeds - 1}"
                  f"{', epochs ' + str(a.epochs) if a.epochs else ''}) ...", flush=True)
            rec = {"project": label, "task": task, **info, **run_one(project, task, out, a)}
            rows.append(rec)
            c = rec.get("conditions", {})
            if "error" in rec:
                print("   ERROR:", rec["error"], flush=True)
            else:
                print("   " + ", ".join(f"{k}: test {v['test_mean']:.4f}" for k, v in c.items())
                      + f" | proposed - baseline_tuned (test): {fmt_pair(rec['paired'].get('proposed-baseline_tuned:test'))}",
                      flush=True)
    lines = [f"# Modelli delle run allenati su altri task ({a.dataset})", "",
             f"Semi {a.seed_offset}–{a.seed_offset + a.n_seeds - 1} (mai usati dalla pipeline per scegliere); ricetta `tuned`"
             f"{'; ' + str(a.epochs) + ' epoche per tutte le condizioni' if a.epochs else ' (10 epoche)'}; "
             f"file protetti {'del kit attuale' if a.infra == 'current' else 'della run'}, modello della run. "
             "Differenze appaiate: media [IC 95%] p del test di permutazione (semi in cui proposed è meglio).", "",
             "| progetto | task | metrica | baseline_graphsage test | baseline_tuned test | proposed test | proposed − baseline_tuned (test) | proposed − baseline_tuned (val) |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c = r.get("conditions", {})
        if "error" in r:
            lines.append(f"| {r['project']} | {r['task']} | - | - | - | - | ERRORE: {r['error']} | |")
            continue
        g = lambda k: (f"{c[k]['test_mean']:.4f} ± {c[k]['test_std']:.4f}" if k in c else "-")  # noqa: E731
        lines.append(f"| {r['project']} | {r['task']} | {r['metric']}{'' if r['higher'] else ' (più basso è meglio)'} | "
                     f"{g('baseline_graphsage')} | {g('baseline_tuned')} | {g('proposed')} | "
                     f"{fmt_pair(r['paired'].get('proposed-baseline_tuned:test'))} | {fmt_pair(r['paired'].get('proposed-baseline_tuned:val'))} |")
    lines += ["", "Modelli: " + "; ".join(sorted({f"`{r['project']}`: {r.get('source') or '-'} {r.get('overrides') or ''}" for r in rows}))]
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "summary.json").write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    (out_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines) + f"\n\nsaved: {out_root}/summary.md")
    return 0 if all("error" not in r for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
