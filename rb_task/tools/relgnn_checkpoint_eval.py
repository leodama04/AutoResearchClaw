#!/usr/bin/env python3
"""Evaluate the OFFICIAL RelGNN checkpoints (Hugging Face `tianlangchen/RelGNN`) on rel-f1 tasks, with OUR data code.

Question (co-supervisor, call of 2026-10-13): before optimising anything, do the published numbers reproduce in our
environment? No training here, only evaluation:
  - data / graph: `rb_data.prepare_data` of the seed project (the official RelBench pipeline: get_stype_proposal +
    GloVe text embeddings + make_pkey_fkey_graph), i.e. the same code used by every run of the pipeline;
  - model: `RelGNN_Model` from the official repository (examples/), with the authors' configuration for the task
    (`get_configs(dataset, task)` in examples/utils.py) and their loader settings;
  - weights: the authors' checkpoint `<dataset>_<task>.pth`, loaded strictly (a mismatch is reported, not hidden);
  - metric: `task.evaluate` of relbench on validation and test, over a few neighbour-sampling seeds (sampling is random).

Usage, in the container (from the repo root):
  ./run.sh exec python3 rb_task/tools/relgnn_checkpoint_eval.py --tasks driver-top3,driver-dnf,driver-position
Options: --repo <RelGNN clone> (default: the one cloned by a pipeline run, artifacts/*/stage-06/paper_repos/relgnn,
or a fresh `git clone`), --ckpt-dir (default artifacts/relgnn_checkpoints), --seeds 0,1,2, --out <file prefix>.
The checkpoints are downloaded from https://huggingface.co/tianlangchen/RelGNN/resolve/main/<dataset>_<task>.pth;
if the container has no network, download them on the host into --ckpt-dir (wget/curl), the script then uses them.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
SEED = Path(os.environ.get("RB_SEED_DIR", TASK_DIR / "seed_project"))

# Test values reported in the RelGNN paper (arXiv 2502.06784, Table on RelBench entity tasks; RDL = Hetero-GNN of RelBench).
PAPER = {
    ("rel-f1", "driver-top3"): {"metric": "roc_auc", "RDL": 0.7554, "RelGNN": 0.8569},
    ("rel-f1", "driver-dnf"): {"metric": "roc_auc", "RDL": 0.7262, "RelGNN": 0.7529},
    ("rel-f1", "driver-position"): {"metric": "mae", "RDL": 4.022, "RelGNN": 3.798},
}
HF_URL = "https://huggingface.co/tianlangchen/RelGNN/resolve/main/{name}"


def find_repo(arg: str | None) -> Path:
    """examples/ directory of the official RelGNN repository."""
    cands = [arg] if arg else sorted(glob.glob("artifacts/*/stage-06/paper_repos/relgnn"), reverse=True) + \
        sorted(glob.glob("artifacts/*/stage-05/code_repos/RelGNN"), reverse=True)
    for c in cands:
        if c and (Path(c) / "examples" / "relgnn_model.py").is_file():
            return Path(c) / "examples"
    dest = Path("/tmp/RelGNN")
    if not (dest / "examples" / "relgnn_model.py").is_file():
        print("cloning https://github.com/snap-stanford/RelGNN ...", flush=True)
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/snap-stanford/RelGNN", str(dest)], check=True)
    return dest / "examples"


def get_checkpoint(ckpt_dir: Path, dataset: str, task: str) -> Path:
    name = f"{dataset}_{task}.pth"
    path = ckpt_dir / name
    if path.is_file() and path.stat().st_size > 0:
        return path
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    print(f"downloading {HF_URL.format(name=name)} ...", flush=True)
    tmp = path.with_suffix(".part")
    with urllib.request.urlopen(HF_URL.format(name=name), timeout=300) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    tmp.rename(path)
    return path


def import_relgnn(examples_dir: Path):
    """The official modules (imported from the repository, never re-implemented)."""
    sys.path.insert(0, str(examples_dir))
    from atomic_routes import get_atomic_routes  # noqa: E402
    from relgnn_model import RelGNN_Model  # noqa: E402
    from utils import get_configs  # noqa: E402

    return RelGNN_Model, get_atomic_routes, get_configs


def build_model(RelGNN_Model, get_atomic_routes, ctx, model_config: dict, out_channels: int):
    return RelGNN_Model(
        data=ctx.data, col_stats_dict=ctx.col_stats_dict, out_channels=out_channels, norm="batch_norm",
        atomic_routes=get_atomic_routes(ctx.data.edge_types), **model_config,
    )


def official_loader(ctx, split: str, loader_config: dict, num_workers: int = 0):
    """Loader exactly as in the authors' relgnn_task_node.py (fanouts halve at every hop)."""
    from torch_geometric.loader import NeighborLoader

    ti = ctx.table_inputs[split]
    return NeighborLoader(
        ctx.data,
        num_neighbors=[int(loader_config["num_neighbors"] / 2 ** i) for i in range(loader_config["num_layers"])],
        time_attr="time", input_nodes=ti.nodes, input_time=ti.time, transform=ti.transform,
        subgraph_type=loader_config["subgraph_type"], batch_size=loader_config["batch_size"],
        temporal_strategy="uniform", shuffle=False, num_workers=num_workers, persistent_workers=num_workers > 0,
    )


def predict(model, loader, ctx, device, clamp=None, binary=True):
    import torch

    model.train(False)
    out = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            pred = model(batch, ctx.entity_table)
            if clamp is not None:
                pred = torch.clamp(pred, clamp[0], clamp[1])
            if binary:
                pred = torch.sigmoid(pred)
            pred = pred.view(-1) if pred.size(1) == 1 else pred
            out.append(pred.detach().cpu())
    return torch.cat(out, dim=0).numpy()


def evaluate_checkpoint(ctx, RelGNN_Model, get_atomic_routes, model_config, loader_config, ckpt_path, device,
                        seeds=(0, 1, 2), loader_factory=None) -> dict:
    """Strict load of the checkpoint, then validation and test metric for every sampling seed."""
    import numpy as np
    import torch
    from relbench.base import TaskType

    task = ctx.task
    binary = task.task_type == TaskType.BINARY_CLASSIFICATION
    key = "roc_auc" if binary else "mae"
    clamp = None
    if task.task_type == TaskType.REGRESSION:  # as in the authors' script: clamp to the 2nd-98th train percentile
        clamp = tuple(np.percentile(ctx.tables["train"].df[task.target_col].to_numpy(), [2, 98]))
    model = build_model(RelGNN_Model, get_atomic_routes, ctx, model_config, 1).to(device)
    state = torch.load(ckpt_path, map_location=device, weights_only=True)
    res = model.load_state_dict(state, strict=False)
    missing, unexpected = list(res.missing_keys), list(res.unexpected_keys)
    out = {"metric": key, "params": int(sum(p.numel() for p in model.parameters())), "missing_keys": missing[:20],
           "unexpected_keys": unexpected[:20], "val": [], "test": []}
    if missing or unexpected:
        out["error"] = f"checkpoint does not match the model: {len(missing)} missing, {len(unexpected)} unexpected keys"
        return out
    make = loader_factory or (lambda split: official_loader(ctx, split, loader_config))
    for s in seeds:
        for split in ("val", "test"):
            torch.manual_seed(s)
            pred = predict(model, make(split), ctx, device, clamp, binary)
            m = task.evaluate(pred, ctx.tables["val"]) if split == "val" else task.evaluate(pred)
            out[split].append(float(m[key]))
    for split in ("val", "test"):
        v = out[split]
        out[f"{split}_mean"] = statistics.mean(v)
        out[f"{split}_std"] = statistics.stdev(v) if len(v) > 1 else 0.0
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="rel-f1")
    ap.add_argument("--tasks", default="driver-top3,driver-dnf,driver-position")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--ckpt-dir", default="artifacts/relgnn_checkpoints")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--out", default=f"artifacts/relgnn_checkpoint_eval_{time.strftime('%Y%m%d-%H%M%S')}")
    a = ap.parse_args()

    sys.path.insert(0, str(SEED))
    import torch

    import rb_config as C  # noqa: F401  (cache dir defaults)
    import rb_data

    examples = find_repo(a.repo)
    RelGNN_Model, get_atomic_routes, get_configs = import_relgnn(examples)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    seeds = [int(x) for x in a.seeds.split(",") if x.strip()]
    print(f"RelGNN code: {examples}\ndevice: {device}\n", flush=True)
    rows = []
    for task_name in [t.strip() for t in a.tasks.split(",") if t.strip()]:
        t0 = time.time()
        rec = {"dataset": a.dataset, "task": task_name}
        try:
            model_config, loader_config = get_configs(a.dataset, task_name)
            rec.update(model_config=model_config, loader_config=loader_config)
            ckpt = get_checkpoint(Path(a.ckpt_dir), a.dataset, task_name)
            ctx = rb_data.prepare_data(a.dataset, task_name, C.CACHE_DIR, device)
            rec.update(evaluate_checkpoint(ctx, RelGNN_Model, get_atomic_routes, model_config, loader_config, ckpt,
                                           device, seeds))
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"
        rec["seconds"] = round(time.time() - t0)
        rec["paper"] = PAPER.get((a.dataset, task_name))
        rows.append(rec)
        print(json.dumps({k: v for k, v in rec.items() if k not in ("missing_keys", "unexpected_keys")}, default=str), flush=True)

    lines = ["# RelGNN: checkpoint ufficiale valutato con il nostro codice dei dati", "",
             f"Codice del modello: `{examples}`; semi di campionamento: {seeds}. Nessun addestramento.", "",
             "| task | metrica | val (nostro) | test (nostro) | test RelGNN (paper) | test RDL (paper) | note |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        p = r.get("paper") or {}
        if "test_mean" in r:
            lines.append(f"| {r['task']} | {r['metric']} | {r['val_mean']:.4f} ± {r['val_std']:.4f} | "
                         f"{r['test_mean']:.4f} ± {r['test_std']:.4f} | {p.get('RelGNN', '?')} | {p.get('RDL', '?')} | "
                         f"{r.get('params', 0):,} parametri |")
        else:
            lines.append(f"| {r['task']} | - | - | - | {p.get('RelGNN', '?')} | {p.get('RDL', '?')} | ERRORE: {r.get('error')} |")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out + ".json").write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    Path(a.out + ".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines) + f"\n\nsaved: {a.out}.md / .json")
    return 0 if all("test_mean" in r for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
