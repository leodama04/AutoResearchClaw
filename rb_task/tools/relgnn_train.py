#!/usr/bin/env python3
"""Train the OFFICIAL RelGNN model with the AUTHORS' configuration in OUR training loop, next to the two baselines.

Question (after RUN-008 / RUN-009): RelGNN used by Qwen in RUN-008 reached test AUROC 0.733 on driver-top3, the authors'
checkpoint 0.8585 with our data and evaluation code. Is the gap the CONFIGURATION (Qwen: 2 layers / 4 heads / batch 128;
authors: 1 layer / 2 heads / batch 256) or the TRAINING (the authors' training recipe is not published: their repository
only evaluates the checkpoints)? And does longer training help (the co-supervisor's question on training steps)?

What is trained, for every task, every number of epochs in --epochs and every seed (default seeds 100-109):
  - baseline_graphsage : official RDL model, official recipe (batch 512)            -- rb_model_official, our loader
  - baseline_tuned     : same model, batch 128                                     -- rb_model_official, our loader
  - relgnn_authors     : RelGNN_Model from the official repository, model AND loader configuration of the authors
                         (examples/utils.py get_configs: layers, channels, heads, simplified_MP, batch, fanouts, hops,
                         subgraph_type)
  - relgnn_run008      : the same official model with the configuration Qwen used in RUN-008 (2 layers, 4 heads,
                         simplified_MP as the authors) and our tuned loader (batch 128): isolates the configuration
Everything else is the pipeline's code: data (rb_data.prepare_data), training loop and model selection
(rb_train.run_one: Adam, lr of the recipe, best epoch on VALIDATION, test evaluated once), metrics (rb_train.evaluate_task).
Nothing is chosen on the test split. Paired differences against baseline_tuned on the same seeds.

Usage, in the container (from the repo root):
  ./run.sh relgnn-train                                   (driver-top3, driver-dnf, driver-position; 10 and 30 epochs)
  ./run.sh relgnn-train --tasks driver-top3 --epochs 10,30,60
Options: --variants authors,run008  --no-baselines  --lr 0.005  --seed-offset 100 --n-seeds 10  --repo <RelGNN clone>
Output: artifacts/relgnn_train_<date>/summary.md, summary.json, results.json (one row per condition x seed).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
SEED = Path(os.environ.get("RB_SEED_DIR", TASK_DIR / "seed_project"))
sys.path.insert(0, str(HERE))

import relgnn_checkpoint_eval as E  # noqa: E402  (find_repo, import_relgnn, PAPER)
from transfer_eval import fmt_pair, paired  # noqa: E402

# Test values of the authors' checkpoints measured with OUR code (RUN-009, docs/runs/RUN-009_checkpoint_relgnn_2026-10-14.md)
CKPT_OURS = {("rel-f1", "driver-top3"): 0.8585, ("rel-f1", "driver-dnf"): 0.7489, ("rel-f1", "driver-position"): 3.7479}
# Configuration used by Qwen for RelGNN in RUN-008 (2 layers, 4 heads; simplified_MP varied between attempts: kept as the
# authors' so that only layers / heads / batch differ)
RUN008_MODEL = {"num_model_layers": 2, "num_heads": 4}


class _NoStop:
    """run_one asks the harness whether to stop; here there is no time budget."""

    def should_stop(self):
        return False


def relgnn_builder(RelGNN_Model, get_atomic_routes):
    """Builder with the signature of rb_model.build_model; the model is the authors' class, never re-implemented."""

    def build(data, col_stats_dict, cfg, out_channels):
        return RelGNN_Model(data=data, col_stats_dict=col_stats_dict, out_channels=out_channels, norm="batch_norm",
                            atomic_routes=get_atomic_routes(data.edge_types), **cfg["relgnn_model"])

    return build


def install_builder(rb_train, build):
    """rb_train.run_one builds the model with rb_train.builder_for(cfg): RelGNN conditions get the official class,
    the baselines keep the frozen official RDL model (rb_model_official)."""
    original = rb_train.builder_for
    rb_train.builder_for = lambda cfg: build if cfg.get("model_impl") == "relgnn" else original(cfg)
    return original


def authors_loaders(ctx, loader_config: dict, num_workers: int = 0) -> dict:
    """NeighborLoader as in the authors' relgnn_task_node.py (fanouts halve at every hop, their batch size and
    subgraph_type), shuffled for training."""
    from torch_geometric.loader import NeighborLoader

    out = {}
    for split in ("train", "val", "test"):
        ti = ctx.table_inputs[split]
        out[split] = NeighborLoader(
            ctx.data,
            num_neighbors=[int(loader_config["num_neighbors"] / 2 ** i) for i in range(loader_config["num_layers"])],
            time_attr="time", input_nodes=ti.nodes, input_time=ti.time, transform=ti.transform,
            subgraph_type=loader_config.get("subgraph_type", "directional"), batch_size=int(loader_config["batch_size"]),
            temporal_strategy="uniform", shuffle=split == "train", num_workers=num_workers,
            persistent_workers=num_workers > 0,
        )
    out["_accum"] = 1
    return out


def conditions(C, model_config: dict, loader_config: dict, epochs: int, lr: float, variants, baselines: bool) -> dict:
    """name -> {"cfg": training config for rb_train.run_one, "loader": "ours" | loader config of the authors}."""
    out = {}
    if baselines:
        out["baseline_graphsage"] = {"cfg": {**C.BASELINE, "epochs": epochs, "lr": lr}, "loader": "ours"}
        out["baseline_tuned"] = {"cfg": {**C.BASELINE_TUNED, "epochs": epochs, "lr": lr}, "loader": "ours"}
    base = {"model_impl": "relgnn", "epochs": epochs, "lr": lr, "weight_decay": 0.0}
    if "authors" in variants:
        out["relgnn_authors"] = {"cfg": {**base, "relgnn_model": dict(model_config),
                                         "batch_size": int(loader_config["batch_size"])},
                                 "loader": dict(loader_config)}
    if "run008" in variants:
        tuned = C.merged_train_cfg(C.BASELINE_TUNED)
        out["relgnn_run008"] = {
            "cfg": {**base, "relgnn_model": {**model_config, **RUN008_MODEL}, "num_layers": 2,
                    "batch_size": int(tuned["batch_size"])},
            "loader": "ours"}  # our tuned loader: batch 128, fanouts [128, 64], directional
    return out


def updates_per_epoch(loaders: dict) -> int:
    try:
        return int(math.ceil(len(loaders["train"]) / max(1, int(loaders.get("_accum", 1)))))
    except TypeError:
        return -1


def run_task(ctx, conds: dict, seeds, device, rb_train, rb_data, C, ours_factory=None, authors_factory=None,
             log=print) -> list:
    """Train every condition on every seed (seed-major, as main.py). Returns one row per condition x seed."""
    loaders = {}
    ref_nodes = None
    for name, spec in conds.items():
        if spec["loader"] == "ours":
            if ours_factory is not None:
                loaders[name] = ours_factory(ctx, spec["cfg"])
            else:
                if ref_nodes is None:
                    ref_nodes = rb_data.reference_nodes(ctx, C.BASELINE)  # same node budget as main.py
                loaders[name] = rb_data.build_loaders(ctx, spec["cfg"], ref_nodes)
        else:
            loaders[name] = (authors_factory or authors_loaders)(ctx, spec["loader"])
    rows = []
    for seed in seeds:
        for name, spec in conds.items():
            t1 = time.time()
            res = rb_train.run_one(ctx, loaders[name], spec["cfg"], seed, device, _NoStop())
            upe = updates_per_epoch(loaders[name])
            rows.append({"condition": name, "seed": seed, "epochs": int(spec["cfg"]["epochs"]), "updates_per_epoch": upe,
                         "seconds": round(time.time() - t1, 1), **res})
            log(f"  {name} seed={seed} epochs={spec['cfg']['epochs']} val={res['val']:.4f} test={res['test']:.4f} "
                f"best_epoch<= {res['epochs_run']} updates/epoch={upe} time={time.time() - t1:.0f}s")
    return rows


def summarize(rows: list) -> dict:
    """Per condition: mean/std of val and test, updates; paired differences against baseline_tuned."""
    out = {"conditions": {}, "paired": {}}
    if not rows:
        return out
    higher = bool(rows[0].get("higher_is_better", True))
    out["metric"], out["higher"] = rows[0].get("tune_metric", "?"), higher
    for cond in dict.fromkeys(r["condition"] for r in rows):
        rr = [r for r in rows if r["condition"] == cond]
        sd = lambda xs: statistics.stdev(xs) if len(xs) > 1 else 0.0  # noqa: E731
        out["conditions"][cond] = {
            "n": len(rr), "val_mean": statistics.mean(r["val"] for r in rr), "val_std": sd([r["val"] for r in rr]),
            "test_mean": statistics.mean(r["test"] for r in rr), "test_std": sd([r["test"] for r in rr]),
            "updates_per_epoch": rr[0].get("updates_per_epoch"), "epochs": rr[0].get("epochs")}
    for cond in out["conditions"]:
        if cond != "baseline_tuned":
            for k in ("val", "test"):
                out["paired"][f"{cond}-baseline_tuned:{k}"] = paired(rows, cond, "baseline_tuned", k, higher)
    return out


LABELS = {"baseline_graphsage": "baseline_graphsage (RDL, ricetta ufficiale)",
          "baseline_tuned": "baseline_tuned (RDL, batch 128)",
          "relgnn_authors": "RelGNN, configurazione degli autori",
          "relgnn_run008": "RelGNN, configurazione di Qwen in RUN-008 (2 strati, 4 teste, batch 128)"}


def render(dataset: str, blocks: list, a, repo: str) -> str:
    lines = [f"# RelGNN con la configurazione degli autori, allenato con il nostro codice ({dataset})", "",
             f"Semi {a.seed_offset}–{a.seed_offset + a.n_seeds - 1} (mai usati dalla pipeline per scegliere); Adam, lr {a.lr}; "
             "epoca migliore scelta sulla validazione (come la pipeline), test valutato una volta. "
             f"Codice di RelGNN: `{repo}`. Differenze appaiate contro `baseline_tuned`: media [IC 95%] p del test di "
             "permutazione (semi in cui la condizione è meglio).", ""]
    for b in blocks:
        key = (dataset, b["task"])
        paper = E.PAPER.get(key) or {}
        lines += [f"## {b['task']}", ""]
        if b.get("model_config") is not None:
            lines += [f"Configurazione degli autori: modello `{b.get('model_config')}`, loader `{b.get('loader_config')}`.", ""]
        if "error" in b:
            lines += [f"ERRORE: {b['error']}", ""]
            continue
        first = b["by_epochs"][0][1] if b["by_epochs"] else {}
        metric = first.get("metric", "?") + ("" if first.get("higher", True) else ", più basso è meglio")
        lines += [f"Riferimenti (test): RelGNN nel paper {paper.get('RelGNN', '?')}, checkpoint degli autori con il nostro "
                  f"codice {CKPT_OURS.get(key, '?')} (RUN-009), RDL nel paper {paper.get('RDL', '?')}.", "",
                  f"| epoche | condizione | aggiornamenti dei pesi | val ({metric}) | test ({metric}) | Δ test vs baseline_tuned | Δ val vs baseline_tuned |",
                  "|---|---|---|---|---|---|---|"]
        for ep, s in b["by_epochs"]:
            for cond, c in s["conditions"].items():
                upd = c["updates_per_epoch"] * c["epochs"] if (c.get("updates_per_epoch") or 0) > 0 else "?"
                lines.append(f"| {ep} | {LABELS.get(cond, cond)} | {upd} | {c['val_mean']:.4f} ± {c['val_std']:.4f} | "
                             f"{c['test_mean']:.4f} ± {c['test_std']:.4f} | "
                             f"{fmt_pair(s['paired'].get(f'{cond}-baseline_tuned:test'))} | "
                             f"{fmt_pair(s['paired'].get(f'{cond}-baseline_tuned:val'))} |")
        lines.append("")
    lines += ["Aggiornamenti dei pesi = batch per epoca × epoche (massimo possibile: l'epoca migliore può essere precedente).",
              "Il codice di addestramento degli autori non è pubblicato: learning rate ed epoche sono quelli della nostra ricetta."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="rel-f1")
    ap.add_argument("--tasks", default="driver-top3,driver-dnf,driver-position")
    ap.add_argument("--epochs", default="10,30", help="comma-separated; the same epochs for every condition")
    ap.add_argument("--variants", default="authors,run008", help="RelGNN variants: authors, run008")
    ap.add_argument("--no-baselines", action="store_true")
    ap.add_argument("--lr", type=float, default=None, help="default: the recipe's (0.005)")
    ap.add_argument("--seed-offset", type=int, default=100)
    ap.add_argument("--n-seeds", type=int, default=10)
    ap.add_argument("--repo", default=None)
    ap.add_argument("--out", default=f"artifacts/relgnn_train_{time.strftime('%Y%m%d-%H%M%S')}")
    a = ap.parse_args()

    sys.path.insert(0, str(SEED))
    import torch

    import rb_config as C
    import rb_data
    import rb_train

    a.lr = float(a.lr if a.lr is not None else C.TRAIN["lr"])
    examples = E.find_repo(a.repo)
    RelGNN_Model, get_atomic_routes, get_configs = E.import_relgnn(examples)
    install_builder(rb_train, relgnn_builder(RelGNN_Model, get_atomic_routes))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.set_num_threads(1)
        free = torch.cuda.mem_get_info()[0] / 1e9
        need = float(os.environ.get("RB_MIN_FREE_GB", "4.5") or 0)
        print(f"gpu free={free:.1f} GB", flush=True)
        if free < need:
            print(f"GPU_UNAVAILABLE: only {free:.1f} GB free, {need:.1f} GB needed (is the pipeline / llama-server running?)")
            return 3
    seeds = list(range(a.seed_offset, a.seed_offset + a.n_seeds))
    epochs_list = [int(x) for x in a.epochs.split(",") if x.strip()]
    variants = {v.strip() for v in a.variants.split(",") if v.strip()}
    print(f"RelGNN code: {examples}\ndevice: {device}  seeds: {seeds}  epochs: {epochs_list}  lr: {a.lr}\n", flush=True)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    blocks, all_rows = [], []
    for task_name in [t.strip() for t in a.tasks.split(",") if t.strip()]:
        b = {"task": task_name, "by_epochs": []}
        t0 = time.time()
        try:
            model_config, loader_config = get_configs(a.dataset, task_name)
            b.update(model_config=model_config, loader_config=loader_config)
            print(f"=== {a.dataset}/{task_name}: authors' model {model_config}, loader {loader_config}", flush=True)
            ctx = rb_data.prepare_data(a.dataset, task_name, C.CACHE_DIR, device)
            for ep in epochs_list:
                conds = conditions(C, model_config, loader_config, ep, a.lr, variants, not a.no_baselines)
                rows = run_task(ctx, conds, seeds, device, rb_train, rb_data, C,
                                log=lambda m: print(m, flush=True))
                for r in rows:
                    r.update(task=task_name)
                all_rows += rows
                s = summarize(rows)
                b["by_epochs"].append((ep, s))
                for cond, c in s["conditions"].items():
                    print(f"  [{task_name}, {ep} epochs] {cond}: val {c['val_mean']:.4f} test {c['test_mean']:.4f} | "
                          f"vs baseline_tuned (test): {fmt_pair(s['paired'].get(f'{cond}-baseline_tuned:test'))}", flush=True)
                (out_dir / "results.json").write_text(json.dumps(all_rows, indent=2, default=str), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            import traceback

            traceback.print_exc()
            b["error"] = f"{type(exc).__name__}: {exc}"
        b["seconds"] = round(time.time() - t0)
        blocks.append(b)
    md = render(a.dataset, blocks, a, str(examples))
    (out_dir / "summary.json").write_text(json.dumps(blocks, indent=2, default=str), encoding="utf-8")
    (out_dir / "summary.md").write_text(md, encoding="utf-8")
    print("\n" + md + f"\nsaved: {out_dir}/summary.md")
    return 0 if all("error" not in b for b in blocks) else 1


if __name__ == "__main__":
    sys.exit(main())
