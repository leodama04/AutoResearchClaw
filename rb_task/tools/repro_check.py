#!/usr/bin/env python3
"""Why do the baselines change from one run to another? (question after the review of the internship report, 2026-10-23)

What the saved runs show (RUN-003..RUN-006, three confirmations per run, seeds 100-109):
  - inside one run the confirmations give almost the same result seed by seed (baseline_graphsage: mean |difference|
    0.002 per seed; baseline_tuned: 10-seed means within 0.006);
  - between runs the same seeds give different results (baseline_graphsage: 0.035 per seed; baseline_tuned means from
    0.772 to 0.802), even when every file executed for the baselines is byte-identical (RUN-005 vs RUN-006).
So something is constant inside a run and changes between runs. This tool tests the two candidates:
  1. the PREPARED DATA: column types (stypes.json) and materialised tables, GloVe text embeddings included, written to
     RB_CACHE_DIR (/tmp of the container, deleted with the container) by the first experiment of every run and reused by
     all the following experiments of that run;
  2. the SOFTWARE ENVIRONMENT (library versions, GPU): recorded for every container (the image layers are recorded by
     run.sh on the host).

Protocol (./run.sh repro-check, ~15-20 min, no LLM, ~4 GB of GPU):
  container A: fresh cache, main.py of the official seed project run twice (like two confirmations of one run);
  container B: fresh cache, run twice (a second "run");
  container C: A's cache copied in, run once.
How to read it:
  A1 = A2, B1 = B2, A != B and C = A  -> the prepared data explain the difference between runs;
  A != B and C != A                    -> not (only) the prepared data: something else changes per container;
  A = B                                -> with this image the containers agree (the old runs differed for another reason).
The summary also compares the caches of A and B file by file (column types, category lists, tensors).

Subcommands (inside the container, from the repo root):
  python3 rb_task/tools/repro_check.py run --out artifacts/repro_X --name A --repeat 2 [--cache-from artifacts/repro_X/A/cache]
  python3 rb_task/tools/repro_check.py compare --out artifacts/repro_X
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import shutil
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
HARNESS = Path(os.environ.get("RB_HARNESS", REPO / "researchclaw" / "experiment" / "harness_template.py"))
SEED_DIR = REPO / "rb_task" / "seed_project"
BASELINES = ("baseline_graphsage", "baseline_tuned")
LIBS = ("torch", "torch_geometric", "pytorch_frame", "relbench", "pyg_lib", "pandas", "numpy", "scikit-learn",
        "sentence-transformers", "transformers", "scipy")


# ----------------------------------------------------------------------------------------------------------- run
def environment() -> dict:
    import importlib.metadata as md

    env = {"hostname": socket.gethostname(), "python": sys.version.split()[0],
           "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
           "NVIDIA_VISIBLE_DEVICES": os.environ.get("NVIDIA_VISIBLE_DEVICES")}
    env["libs"] = {}
    for name in LIBS:
        try:
            env["libs"][name] = md.version(name)
        except Exception:  # noqa: BLE001
            env["libs"][name] = None
    try:
        import torch

        env["torch_cuda"] = torch.version.cuda
        env["cudnn"] = torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            env["gpu"] = {"name": p.name, "uuid": str(getattr(p, "uuid", "")), "total_gb": round(p.total_memory / 1e9, 1)}
    except Exception as e:  # noqa: BLE001
        env["torch_error"] = repr(e)
    try:
        env["nvidia_smi"] = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,uuid,driver_version,memory.used,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:  # noqa: BLE001
        env["nvidia_smi"] = None
    return env


def all_packages() -> list[str]:
    import importlib.metadata as md

    return sorted({f"{d.metadata['Name']}=={d.version}" for d in md.distributions() if d.metadata["Name"]}, key=str.lower)


def fingerprint(cache: Path) -> dict:
    """relative path -> md5 and size of every file of the prepared-data cache."""
    out = {}
    for p in sorted(cache.rglob("*")):
        if p.is_file():
            out[p.relative_to(cache).as_posix()] = {"md5": hashlib.md5(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
    return out


def execute_main(project: Path, rd: Path, env: dict) -> dict:
    """Run main.py of a fresh copy of `project` in rd/project (like one experiment of the pipeline); keep log and results."""
    work = rd / "project"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    for f in project.glob("*.py"):
        shutil.copy2(f, work / f.name)
    if (work / "rb_model_minimal.py").is_file():  # code mode of the pipeline: proposed starts from the official model
        shutil.copy2(work / "rb_model_minimal.py", work / "rb_model.py")
    shutil.copy2(HARNESS, work / "experiment_harness.py")
    t0 = time.time()
    with open(rd / "log.txt", "w", encoding="utf-8") as log:
        rc = subprocess.run([sys.executable, "main.py"], cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    rec = {"returncode": rc, "seconds": round(time.time() - t0)}
    if (work / "results.json").is_file():
        shutil.copy2(work / "results.json", rd / "results.json")
    else:
        rec["error"] = f"no results.json (exit code {rc}); see {rd / 'log.txt'}"
    shutil.rmtree(work, ignore_errors=True)
    return rec


def cmd_run(a) -> int:
    if not HARNESS.is_file():
        print(f"missing {HARNESS}", file=sys.stderr)
        return 1
    project = Path(a.project) if a.project else SEED_DIR
    d = Path(a.out) / a.name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    cache = (d / "cache").resolve()
    if a.cache_from:
        src = Path(a.cache_from)
        if not src.is_dir() or not any(src.rglob("*")):
            print(f"--cache-from {src}: empty or missing", file=sys.stderr)
            return 1
        shutil.copytree(src, cache)
    else:
        cache.mkdir()
    info = {"name": a.name, "repeat": a.repeat, "cache_from": a.cache_from or None, "dataset": a.dataset, "task": a.task,
            "seeds": [a.seed_offset, a.seed_offset + a.n_seeds - 1], "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": environment(), "runs": []}
    (d / "packages.txt").write_text("\n".join(all_packages()) + "\n", encoding="utf-8")
    if a.cache_from:
        info["cache_at_start"] = fingerprint(cache)
    env = dict(os.environ, RB_CACHE_DIR=str(cache), RB_DATASET=a.dataset, RB_TASK=a.task, RB_RECIPE="tuned",
               RB_SEED_OFFSET=str(a.seed_offset), RB_N_SEEDS=str(a.n_seeds), RB_TIME_BUDGET_SEC=str(a.time_budget),
               PYTHONUNBUFFERED="1")
    for i in range(1, a.repeat + 1):
        rd = d / f"run{i}"
        print(f"=== container {a.name}, run {i}/{a.repeat} (cache {'from ' + a.cache_from if a.cache_from else 'fresh' if i == 1 else 'of run 1'}) ...",
              flush=True)
        rec = {"run": i, **execute_main(project, rd, env)}
        info["runs"].append(rec)
        if i == 1:
            info["cache_after_run1"] = fingerprint(cache)
        print("   " + (rec.get("error") or ", ".join(f"{k}: test {v:.4f}" for k, v in test_means(rd).items())), flush=True)
    info["cache_at_end"] = fingerprint(cache)
    info["cache_changed_after_run1"] = info["cache_at_end"] != info.get("cache_after_run1")
    (d / "info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return 0 if all("error" not in r for r in info["runs"]) else 1


# ------------------------------------------------------------------------------------------------------- compare
def per_seed(rd: Path) -> dict:
    """condition -> {seed: (val, test)}"""
    p = rd / "results.json"
    if not p.is_file():
        return {}
    out: dict = {}
    for r in json.loads(p.read_text(encoding="utf-8")).get("results") or []:
        out.setdefault(r["condition"], {})[r["seed"]] = (r["val"], r["test"])
    return out


def test_means(rd: Path) -> dict:
    return {c: statistics.mean(t for _, t in v.values()) for c, v in per_seed(rd).items() if c in BASELINES}


def mean_abs_diff(x: dict, y: dict, k: int = 1) -> float | None:
    seeds = sorted(set(x) & set(y))
    return statistics.mean(abs(x[s][k] - y[s][k]) for s in seeds) if seeds else None


def deep_cache_diff(ca: Path, cb: Path, max_items: int = 12) -> list[str]:
    """What differs between two prepared-data caches: column types, then the materialised tables (columns, statistics
    such as category lists, tensors). Best effort: any failure is reported, never raised."""
    lines = []
    for sp in sorted(set(p.relative_to(ca).as_posix() for p in ca.rglob("stypes.json")) |
                     set(p.relative_to(cb).as_posix() for p in cb.rglob("stypes.json"))):
        try:
            ja, jb = json.loads((ca / sp).read_text()), json.loads((cb / sp).read_text())
        except Exception as e:  # noqa: BLE001
            lines.append(f"- `{sp}`: non confrontabile ({e!r})")
            continue
        diff = [f"{t}.{c}: {ja.get(t, {}).get(c)} / {jb.get(t, {}).get(c)}"
                for t in sorted(set(ja) | set(jb)) for c in sorted(set(ja.get(t, {})) | set(jb.get(t, {})))
                if ja.get(t, {}).get(c) != jb.get(t, {}).get(c)]
        order = [t for t in ja if list(ja[t]) != list(jb.get(t, {}))]
        lines.append(f"- `{sp}` (tipi delle colonne): " + ("identici" if not diff else f"{len(diff)} colonne diverse: " + "; ".join(diff[:max_items])))
        if not diff and order:
            lines.append(f"  - stessi tipi ma ordine delle colonne diverso nelle tabelle: {', '.join(order)}")
    pts = sorted(p.relative_to(ca).as_posix() for p in ca.rglob("*.pt"))
    try:
        import torch
        import torch_frame
    except Exception as e:  # noqa: BLE001
        return lines + [f"- tabelle materializzate: confronto dettagliato non disponibile ({e!r})"]
    for rel in pts:
        if not (cb / rel).is_file():
            lines.append(f"- `{rel}`: solo nella prima cache")
            continue
        if (ca / rel).read_bytes() == (cb / rel).read_bytes():
            continue
        try:
            tfa, sa = torch_frame.load(str(ca / rel))
            tfb, sb = torch_frame.load(str(cb / rel))
        except Exception as e:  # noqa: BLE001
            lines.append(f"- `{rel}`: file diversi, non caricabili ({e!r})")
            continue
        found = []
        if tfa.col_names_dict != tfb.col_names_dict:
            found.append("colonne o loro ordine diversi")
        for col in sorted(set(sa or {}) | set(sb or {})):
            if repr((sa or {}).get(col)) != repr((sb or {}).get(col)):
                found.append(f"statistiche della colonna `{col}` diverse")
        for st in sorted(set(tfa.feat_dict) | set(tfb.feat_dict), key=str):
            xa, xb = tfa.feat_dict.get(st), tfb.feat_dict.get(st)
            # MultiEmbeddingTensor / MultiNestedTensor (text embeddings, multicategorical) keep their data in .values;
            # a plain tensor also has a .values method (sparse tensors), so unwrap only non-tensors
            xa = xa if torch.is_tensor(xa) else getattr(xa, "values", xa)
            xb = xb if torch.is_tensor(xb) else getattr(xb, "values", xb)
            if not (torch.is_tensor(xa) and torch.is_tensor(xb)):
                found.append(f"{st}: non confrontabile")
            elif xa.shape != xb.shape:
                found.append(f"{st}: forme diverse {tuple(xa.shape)} / {tuple(xb.shape)}")
            elif not torch.equal(xa, xb):
                da = (xa.double() - xb.double()).abs()
                da = da[~torch.isnan(da)]
                found.append(f"{st}: valori diversi (max |diff| {da.max().item() if da.numel() else float('nan'):.3g}, "
                             f"{(da > 0).float().mean().item() * 100:.1f}% degli elementi)")
        lines.append(f"- `{rel}`: " + ("file diversi ma contenuto uguale (solo serializzazione)" if not found
                                       else "; ".join(found[:max_items])))
    return lines


def cmd_compare(a) -> int:
    out = Path(a.out)
    conts = {}
    for d in sorted(p for p in out.iterdir() if (p / "info.json").is_file()):
        conts[d.name] = {"info": json.loads((d / "info.json").read_text(encoding="utf-8")),
                         "runs": {r.name: per_seed(r) for r in sorted(d.glob("run*")) if (r / "results.json").is_file()},
                         "packages": (d / "packages.txt").read_text(encoding="utf-8").splitlines() if (d / "packages.txt").is_file() else []}
    if not conts:
        print(f"no container results in {out}", file=sys.stderr)
        return 1
    L = ["# Riproducibilità tra container (prova senza LLM)", "",
         "Stesso codice (progetto ufficiale del kit), stessi semi, task "
         f"`{next(iter(conts.values()))['info']['task']}`. Ogni container è come una run della pipeline: i dati preparati "
         "(tipi delle colonne, tabelle materializzate, embedding del testo) vengono costruiti dal primo esperimento e "
         "riusati dagli altri. A e B partono da una cache vuota; C riusa la cache di A.", "",
         "## 1. Medie di test (10 semi)", "",
         "| container | esecuzione | cache | " + " | ".join(f"{c} test" for c in BASELINES) + " |", "|---|---|---|" + "---|" * len(BASELINES)]
    for n, c in conts.items():
        for rn, ps in c["runs"].items():
            src = f"da {Path(c['info']['cache_from']).parent.name}" if c["info"].get("cache_from") else ("nuova" if rn == "run1" else "di run1")
            L.append(f"| {n} | {rn} | {src} | " + " | ".join(
                f"{statistics.mean(t for _, t in ps[b].values()):.4f}" if b in ps else "-" for b in BASELINES) + " |")
    # pairwise per-seed differences
    keys = [(n, rn) for n, c in conts.items() for rn in c["runs"]]
    L += ["", "## 2. Differenza media per seme (|test_1 − test_2|, stessi semi)", "",
          "Dentro lo stesso container misura il non determinismo dell'addestramento; tra container diversi tutto il resto.", "",
          "| confronto | tipo | " + " | ".join(BASELINES) + " |", "|---|---|" + "---|" * len(BASELINES)]
    groups: dict = {}
    for (n1, r1), (n2, r2) in itertools.combinations(keys, 2):
        kind = "stesso container" if n1 == n2 else f"{n1} vs {n2}"
        vals = [mean_abs_diff(conts[n1]["runs"][r1].get(b, {}), conts[n2]["runs"][r2].get(b, {})) for b in BASELINES]
        groups.setdefault(kind, []).append(vals)
        L.append(f"| {n1}/{r1} – {n2}/{r2} | {kind} | " + " | ".join("-" if v is None else f"{v:.4f}" for v in vals) + " |")
    agg = {k: [statistics.mean(x[i] for x in v if x[i] is not None) if any(x[i] is not None for x in v) else None
               for i in range(len(BASELINES))] for k, v in groups.items()}
    L += ["", "Riassunto (media dei confronti dello stesso tipo):", "", "| tipo | " + " | ".join(BASELINES) + " |",
          "|---|" + "---|" * len(BASELINES)]
    for k, v in agg.items():
        L.append(f"| {k} | " + " | ".join("-" if x is None else f"{x:.4f}" for x in v) + " |")
    w = agg.get("stesso container", [None])[0]
    ab = next((v[0] for k, v in agg.items() if k in ("A vs B", "B vs A")), None)
    ac = next((v[0] for k, v in agg.items() if k in ("A vs C", "C vs A")), None)
    if None not in (w, ab, ac):
        thr = max(3 * w, 0.005)
        if ab <= thr:
            verdict = "A e B coincidono: con questa immagine i container danno gli stessi risultati."
        elif ac <= thr:
            verdict = "A e B differiscono, mentre C (cache di A) coincide con A: la differenza viene dai dati preparati."
        else:
            verdict = "A e B differiscono e anche C differisce da A: non sono (solo) i dati preparati."
        L += ["", f"**Lettura indicativa** (su `baseline_graphsage`, soglia {thr:.4f} = 3 volte la differenza dentro lo "
                  f"stesso container): {verdict} Contano i numeri delle tabelle."]
    # per-seed table for baseline_graphsage
    seeds = sorted({s for c in conts.values() for ps in c["runs"].values() for s in ps.get(BASELINES[0], {})})
    L += ["", f"## 3. Test per seme di `{BASELINES[0]}`", "", "| esecuzione | " + " | ".join(str(s) for s in seeds) + " |",
          "|---|" + "---|" * len(seeds)]
    for n, c in conts.items():
        for rn, ps in c["runs"].items():
            v = ps.get(BASELINES[0], {})
            L.append(f"| {n}/{rn} | " + " | ".join(f"{v[s][1]:.3f}" if s in v else "-" for s in seeds) + " |")
    # caches
    L += ["", "## 4. Dati preparati (cache)", ""]
    fps = {n: c["info"].get("cache_after_run1") or {} for n, c in conts.items()}
    for n, c in conts.items():
        ch = c["info"].get("cache_changed_after_run1")
        L.append(f"- {n}: {len(fps[n])} file{'; modificata dopo la prima esecuzione' if ch else ''}"
                 f"{'; copiata da ' + c['info']['cache_from'] if c['info'].get('cache_from') else ''}")
    names = list(conts)
    for n1, n2 in itertools.combinations(names, 2):
        f1, f2 = fps[n1], fps[n2]
        diff = sorted(k for k in set(f1) | set(f2) if (f1.get(k) or {}).get("md5") != (f2.get(k) or {}).get("md5"))
        L.append(f"- {n1} vs {n2}: " + ("cache identiche (stessi file, byte per byte)" if not diff
                                        else f"{len(diff)} file diversi: " + ", ".join(f"`{x}`" for x in diff[:15])))
        if diff:
            try:
                L += ["  " + x for x in deep_cache_diff(out / n1 / "cache", out / n2 / "cache")]
            except Exception as e:  # noqa: BLE001
                L.append(f"  - confronto dettagliato fallito: {e!r}")
    # environment
    L += ["", "## 5. Ambiente", ""]
    for n, c in conts.items():
        e = c["info"]["environment"]
        L.append(f"- {n}: GPU {(e.get('gpu') or {}).get('name')} `{(e.get('gpu') or {}).get('uuid')}`, CUDA {e.get('torch_cuda')}, "
                 f"cuDNN {e.get('cudnn')}, " + ", ".join(f"{k} {v}" for k, v in e.get("libs", {}).items() if v))
    base = names[0]
    for n in names[1:]:
        p0, p1 = set(conts[base]["packages"]), set(conts[n]["packages"])
        L.append(f"- pacchetti {base} vs {n}: " + ("identici" if p0 == p1 else
                 f"diversi: solo {base}: {sorted(p0 - p1)[:10]}; solo {n}: {sorted(p1 - p0)[:10]}"))
    img = out / "image.txt"
    if img.is_file():
        L += ["", "Immagine Docker (dall'host: id, data di creazione e strati):", "", "```",
              *img.read_text(encoding="utf-8", errors="replace").splitlines()[:40], "```"]
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


# -------------------------------------------------------------------------------------------------------- stypes
# Test per seme di baseline_graphsage (semi 100-109, conferma finale) delle run salvate e della prova del 23/10: le run
# cadono in pochi "mondi" (RUN-003 = RUN-005, RUN-004 = RUN-008, RUN-006 ~ prova del 23/10).
OLD_RUNS = {
    "RUN-003": [0.7776, 0.7887, 0.7896, 0.7723, 0.7827, 0.6503, 0.755, 0.7891, 0.7398, 0.7974],
    "RUN-004": [0.7411, 0.7791, 0.7574, 0.7707, 0.7843, 0.7541, 0.7443, 0.761, 0.7595, 0.7065],
    "RUN-005": [0.7739, 0.7857, 0.7895, 0.7717, 0.7844, 0.6507, 0.757, 0.7854, 0.7521, 0.8028],
    "RUN-006": [0.8098, 0.677, 0.7614, 0.6789, 0.7385, 0.6901, 0.7687, 0.7859, 0.7746, 0.7629],
    "RUN-008": [0.7381, 0.7806, 0.7654, 0.763, 0.7813, 0.7527, 0.7389, 0.7584, 0.7576, 0.7126],
    "prova 23/10": [0.805, 0.678, 0.765, 0.682, 0.758, 0.722, 0.770, 0.785, 0.770, 0.761],
}


def stype_proposals(project: Path, dataset: str, task: str, n: int) -> dict:
    """Column types exactly as the first experiment of a run infers them (rb_data.prepare_data, no stypes.json yet):
    relbench's get_stype_proposal looks at a RANDOM sample of 1000 rows per table (DataFrame.sample without a seed).
    Here the sample is drawn n times with numpy seeds 0..n-1. Returns {json text: [seeds]} with the JSON written as
    rb_data writes stypes.json."""
    sys.path.insert(0, str(project.resolve()))
    import numpy as np
    import rb_loader  # noqa: E402  (the project's offline-first loader)
    from relbench.modeling.utils import get_stype_proposal

    dataset_obj, _task, _src = rb_loader.load_dataset_and_task(dataset, task)
    db = dataset_obj.get_db()
    out: dict = {}
    for k in range(n):
        np.random.seed(k)
        text = json.dumps(get_stype_proposal(db), indent=2, default=str)
        out.setdefault(text, []).append(k)
    return out


def cmd_stypes(a) -> int:
    if not HARNESS.is_file():
        print(f"missing {HARNESS}", file=sys.stderr)
        return 1
    project = Path(a.project) if a.project else SEED_DIR
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    props = stype_proposals(project, a.dataset, a.task, a.n)
    variants = sorted(props.items(), key=lambda kv: -len(kv[1]))
    print(f"{a.n} samples -> {len(variants)} different column-type proposals ({time.time() - t0:.0f}s)", flush=True)
    parsed = [json.loads(t) for t, _ in variants]
    ref = parsed[0]
    cols = sorted({(t, c) for v in parsed for t in v for c in v[t]})
    changing = {f"{t}.{c}": {} for t, c in cols if len({v.get(t, {}).get(c) for v in parsed}) > 1}
    for (text, seeds), v in zip(variants, parsed):
        for tc in changing:
            t, c = tc.split(".", 1)
            val = v.get(t, {}).get(c)
            changing[tc][val] = changing[tc].get(val, 0) + len(seeds)
    sd = out / "stypes"
    sd.mkdir(exist_ok=True)
    for i, (text, seeds) in enumerate(variants, 1):
        (sd / f"variant_{i}.json").write_text(text, encoding="utf-8")
    # one evaluation per variant (most frequent first): the cache starts with that stypes.json, like a run whose first
    # experiment drew that sample
    env_base = dict(os.environ, RB_DATASET=a.dataset, RB_TASK=a.task, RB_RECIPE="tuned", RB_SEED_OFFSET=str(a.seed_offset),
                    RB_N_SEEDS=str(a.n_seeds), RB_TIME_BUDGET_SEC=str(a.time_budget), PYTHONUNBUFFERED="1")
    worlds = []
    for i, (text, seeds) in enumerate(variants[: a.max_worlds], 1):
        wd = out / "worlds" / f"v{i}"
        if wd.exists():
            shutil.rmtree(wd)
        cache = (wd / "cache").resolve()
        (cache / a.dataset).mkdir(parents=True)
        (cache / a.dataset / "stypes.json").write_text(text, encoding="utf-8")
        print(f"=== variant {i}/{min(len(variants), a.max_worlds)} ({len(seeds)}/{a.n} samples) ...", flush=True)
        rec = {"variant": i, **execute_main(project, wd, dict(env_base, RB_CACHE_DIR=str(cache)))}
        if (cache / a.dataset / "stypes.json").read_text(encoding="utf-8") != text:
            rec["warning"] = "stypes.json changed by main.py"
        rec["per_seed"] = per_seed(wd)
        worlds.append(rec)
        print("   " + (rec.get("error") or ", ".join(f"{k}: test {v:.4f}" for k, v in test_means(wd).items())), flush=True)
    info = {"n_samples": a.n, "variants": [{"variant": i, "samples": len(s), "seeds": s[:20]} for i, (_, s) in enumerate(variants, 1)],
            "changing_columns": changing, "worlds": [{k: v for k, v in w.items() if k != "per_seed"} for w in worlds],
            "environment": environment()}
    (out / "stypes_info.json").write_text(json.dumps(info, indent=2, default=str), encoding="utf-8")
    # report
    L = ["# Tipi delle colonne e risultati dei baseline", "",
         "All'inizio di ogni run il primo esperimento decide il tipo di ogni colonna (numerica, categorica, testo, data) con "
         "`get_stype_proposal` di RelBench, che guarda un campione **casuale** di 1000 righe per tabella "
         "(`DataFrame.sample` senza seme), e lo salva in `stypes.json`; tutti gli esperimenti successivi della run lo "
         f"riusano. Qui il campione è estratto {a.n} volte (semi numpy 0–{a.n - 1}).", "",
         f"## 1. Esiti diversi: {len(variants)}", "", "| variante | campioni | colonne diverse dalla variante 1 |", "|---|---|---|"]
    for i, ((text, seeds), v) in enumerate(zip(variants, parsed), 1):
        diff = [f"`{tc}`: {v.get(tc.split('.', 1)[0], {}).get(tc.split('.', 1)[1])}" for tc in changing
                if v.get(tc.split('.', 1)[0], {}).get(tc.split('.', 1)[1]) != ref.get(tc.split('.', 1)[0], {}).get(tc.split('.', 1)[1])]
        L.append(f"| {i} | {len(seeds)}/{a.n} | {', '.join(diff) if diff else '(riferimento)'} |")
    if changing:
        L += ["", "Colonne il cui tipo dipende dal campione (numero di campioni per tipo):", ""]
        L += [f"- `{tc}`: " + ", ".join(f"{k} {n}" for k, n in sorted(cnt.items(), key=lambda x: -x[1])) for tc, cnt in changing.items()]
    else:
        L += ["", "Il tipo di ogni colonna è sempre lo stesso: la variabilità tra le run **non** viene da qui."]
    if worlds:
        L += ["", "## 2. Baseline con ciascuna variante (semi "
              f"{a.seed_offset}–{a.seed_offset + a.n_seeds - 1}) e confronto con le run salvate", "",
              "Distanza = differenza media per seme del test di `baseline_graphsage` (dentro la stessa run è circa 0.002).", "",
              "| variante | baseline_graphsage test | baseline_tuned test | " + " | ".join(OLD_RUNS) + " | più vicina |",
              "|---|---|---|" + "---|" * len(OLD_RUNS) + "---|"]
        for w in worlds:
            ps = w["per_seed"]
            g = ps.get("baseline_graphsage", {})
            if not g:
                L.append(f"| {w['variant']} | {w.get('error', 'nessun risultato')} | | " + " | " * len(OLD_RUNS) + " |")
                continue
            dist = {}
            for name, vals in OLD_RUNS.items():
                common = [(g[a.seed_offset + j][1], vals[j]) for j in range(len(vals)) if a.seed_offset + j in g]
                if common and a.seed_offset == 100 and a.task == "driver-top3":
                    dist[name] = statistics.mean(abs(x - y) for x, y in common)
            best = min(dist, key=dist.get) if dist else "-"
            tm = statistics.mean(t for _, t in ps["baseline_tuned"].values()) if ps.get("baseline_tuned") else float("nan")
            L.append(f"| {w['variant']} | {statistics.mean(t for _, t in g.values()):.4f} | {tm:.4f} | "
                     + " | ".join(f"{dist[n]:.4f}" if n in dist else "-" for n in OLD_RUNS) + f" | {best} |")
        L += ["", "Test per seme di `baseline_graphsage`:", "", "| | " + " | ".join(str(a.seed_offset + j) for j in range(a.n_seeds)) + " |",
              "|---|" + "---|" * a.n_seeds]
        for name, vals in OLD_RUNS.items():
            L.append(f"| {name} | " + " | ".join(f"{x:.3f}" for x in vals[: a.n_seeds]) + " |")
        for w in worlds:
            g = w["per_seed"].get("baseline_graphsage", {})
            L.append(f"| **variante {w['variant']}** | " + " | ".join(f"{g[a.seed_offset + j][1]:.3f}" if a.seed_offset + j in g else "-"
                                                             for j in range(a.n_seeds)) + " |")
    (out / "summary_stypes.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0 if all("error" not in w for w in worlds) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--name", required=True)
    r.add_argument("--repeat", type=int, default=2)
    r.add_argument("--cache-from", default="")
    r.add_argument("--project", default="", help="project to run (default: the kit's seed project)")
    r.add_argument("--dataset", default="rel-f1")
    r.add_argument("--task", default="driver-top3")
    r.add_argument("--seed-offset", type=int, default=100)
    r.add_argument("--n-seeds", type=int, default=10)
    r.add_argument("--time-budget", type=int, default=3600)
    c = sub.add_parser("compare")
    c.add_argument("--out", required=True)
    t = sub.add_parser("stypes", help="does the random sample used to infer column types change the results?")
    t.add_argument("--out", required=True)
    t.add_argument("--n", type=int, default=50, help="number of random samples (numpy seeds 0..n-1)")
    t.add_argument("--max-worlds", type=int, default=4, help="variants evaluated with main.py (most frequent first)")
    t.add_argument("--project", default="")
    t.add_argument("--dataset", default="rel-f1")
    t.add_argument("--task", default="driver-top3")
    t.add_argument("--seed-offset", type=int, default=100)
    t.add_argument("--n-seeds", type=int, default=10)
    t.add_argument("--time-budget", type=int, default=3600)
    a = ap.parse_args()
    return {"run": cmd_run, "compare": cmd_compare, "stypes": cmd_stypes}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
