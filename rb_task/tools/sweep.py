#!/usr/bin/env python3
"""Quick sweep (no LLM): is the validation metric a reliable guide for optimisation here?

Runs a small set of hand-picked configurations (several seeds each) with the seed project and prints
validation/test ROC-AUC per configuration plus the Spearman correlation between the validation and the
test ranking of the configurations. If that correlation is low, validation-driven refinement
(what the pipeline does) cannot be trusted to improve the test metric.

Run:  ./run.sh sweep                       training-recipe / size / operator variants (default)
      RB_SWEEP_MODE=arch ./run.sh sweep    architecture variants under the fixed tuned recipe
      confirm the winners on NEW seeds:
        RB_SWEEP_MODE=arch RB_SWEEP_ONLY="aggr=max,transformer" RB_SWEEP_SEEDS=10 RB_SWEEP_SEED_OFFSET=100 ./run.sh sweep
      A/B on the measurement path (sweep vs main.py give different numbers for the same config): RB_SWEEP_THREADS=1
      env: RB_SWEEP_SEEDS=5, RB_SWEEP_DEEP=1 (adds 3-layer models), RB_SWEEP_RECIPE_JSON='{"batch_size":128}'
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

SEED = Path(os.environ.get("RB_SEED_DIR", Path(__file__).resolve().parent.parent / "seed_project"))
sys.path.insert(0, str(SEED))

import torch  # noqa: E402

import rb_config as C  # noqa: E402
import rb_data  # noqa: E402
import rb_train  # noqa: E402


class _NoStop:
    def should_stop(self):
        return False


def sweep_configs(deep: bool = False, mode: str = "recipe", recipe: dict = None) -> dict:
    """mode="recipe": training recipe / size / operator variants of the official baseline.
    mode="arch": ARCHITECTURE variants under a fixed training recipe (default: the tuned one)."""
    if mode == "arch":
        b = {**C.BASELINE, **(recipe if recipe is not None else C.TUNED_TRAIN)}
        cfgs = {
            "baseline (fixed recipe)": {},
            "layers=1": {"num_layers": 1},
            "dropout=0.1": {"dropout": 0.1},
            "residual": {"residual": True},
            "dropout=0.1 + residual": {"dropout": 0.1, "residual": True},
            "channels=64": {"channels": 64},
            "channels=256": {"channels": 256},
            "aggr=mean": {"aggr": "mean"},
            "aggr=max": {"aggr": "max"},
            "head norm=layer_norm": {"norm": "layer_norm"},
            "gatv2": {"gnn_type": "gatv2"},
            "gin": {"gnn_type": "gin"},
            "transformer": {"gnn_type": "transformer"},
            "resgated": {"gnn_type": "resgated"},
        }
        if deep:
            cfgs["layers=3"] = {"num_layers": 3}
        return {name: {**b, **over} for name, over in cfgs.items()}
    b = dict(C.BASELINE)
    cfgs = {
        "baseline (official)": {},
        "epochs=30": {"epochs": 30},
        "epochs=60": {"epochs": 60},
        "batch=128 (4x more steps)": {"batch_size": 128},
        "lr=1e-3, epochs=30": {"lr": 0.001, "epochs": 30},
        "dropout=0.1": {"dropout": 0.1},
        "residual": {"residual": True},
        "dropout=0.1 + residual": {"dropout": 0.1, "residual": True},
        "channels=64": {"channels": 64},
        "channels=256": {"channels": 256},
        "gatv2": {"gnn_type": "gatv2"},
        "gin": {"gnn_type": "gin"},
        "transformer": {"gnn_type": "transformer"},
        "resgated": {"gnn_type": "resgated"},
    }
    if deep:
        cfgs["3 layers"] = {"num_layers": 3}
    return {name: {**b, **over} for name, over in cfgs.items()}


def spearman(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3:
        return float("nan")
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def run_sweep(ctx, configs: dict, seeds: list, ref_nodes: float, device, log=print) -> list:
    rows = []
    for name, cfg in configs.items():
        loaders = rb_data.build_loaders(ctx, cfg, ref_nodes)
        vals, tests, peaks, t0 = [], [], [], time.time()
        for s in seeds:
            r = rb_train.run_one(ctx, loaders, cfg, s, device, _NoStop())
            vals.append(r["val"]); tests.append(r["test"]); peaks.append(r["peak_gpu_gb"])
        row = {
            "name": name,
            "val_mean": float(np.mean(vals)), "val_std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
            "test_mean": float(np.mean(tests)), "test_std": float(np.std(tests, ddof=1)) if len(tests) > 1 else 0.0,
            "sec_per_run": (time.time() - t0) / len(seeds), "peak_gb": float(max(peaks)),
            "val": vals, "test": tests,
        }
        rows.append(row)
        log(f"  {name:28s} val={row['val_mean']:.4f}±{row['val_std']:.3f} test={row['test_mean']:.4f}±{row['test_std']:.3f} "
            f"({row['sec_per_run']:.0f}s/run, peak {row['peak_gb']:.1f}GB)")
    return rows


def rho_ci(rho: float, n: int):
    """Approximate 95% confidence interval of a correlation (Fisher z)."""
    if n < 4 or not np.isfinite(rho) or abs(rho) >= 1:
        return float("nan"), float("nan")
    z, se = np.arctanh(rho), 1.0 / np.sqrt(n - 3)
    return float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se))


def verdict(rho: float, lo: float, hi: float) -> str:
    if not np.isfinite(rho):
        return "not enough configurations to say anything"
    if lo > 0.3:
        return "validation tracks the test metric reasonably well"
    if hi < 0.3:
        return "validation is a WEAK guide for the test metric on this task"
    return "INCONCLUSIVE (the confidence interval is wide: too few / too noisy configurations)"


def report(rows: list) -> dict:
    n_seeds = len(rows[0]["val"])
    rho = spearman([r["val_mean"] for r in rows], [r["test_mean"] for r in rows])
    lo, hi = rho_ci(rho, len(rows))
    best_val = max(rows, key=lambda r: r["val_mean"])
    best_test = max(rows, key=lambda r: r["test_mean"])
    base = rows[0]
    print("\n=== Sweep summary (sorted by the validation metric) ===")
    print(f"{'config':30s} {'val':>16s} {'test':>16s}")
    for r in sorted(rows, key=lambda r: -r["val_mean"]):
        print(f"{r['name']:30s} {r['val_mean']:.4f}±{r['val_std']:.3f}   {r['test_mean']:.4f}±{r['test_std']:.3f}")

    print(f"\n=== Difference from '{base['name']}' (in standard errors, {n_seeds} seeds each) ===")
    print(f"{'config':30s} {'dVal':>14s} {'dTest':>14s}  note")
    flagged = []
    for r in rows[1:]:
        dv, dt = r["val_mean"] - base["val_mean"], r["test_mean"] - base["test_mean"]
        sev = np.sqrt((r["val_std"] ** 2 + base["val_std"] ** 2) / n_seeds) or 1e-9
        set_ = np.sqrt((r["test_std"] ** 2 + base["test_std"] ** 2) / n_seeds) or 1e-9
        zv, zt = dv / sev, dt / set_
        note = ""
        if zv * zt < 0 and max(abs(zv), abs(zt)) > 3 and min(abs(zv), abs(zt)) > 1:
            note = "<- validation and test DISAGREE"
            flagged.append(r["name"])
        print(f"{r['name']:30s} {dv:+.3f} ({zv:+.1f}SE) {dt:+.3f} ({zt:+.1f}SE)  {note}")

    print(f"\nSpearman correlation of the config ranking, validation vs test: {rho:+.2f} "
          f"(95% CI [{lo:+.2f}, {hi:+.2f}], n={len(rows)} configs)")
    print(f"best on validation: {best_val['name']} (test {best_val['test_mean']:.4f}, reference test {base['test_mean']:.4f})")
    print(f"best on test:       {best_test['name']} (val {best_test['val_mean']:.4f})")
    print("->", verdict(rho, lo, hi))
    rho2, ci2 = None, [float("nan"), float("nan")]
    if flagged:
        print("   configurations where validation and test point in opposite directions:", ", ".join(flagged))
        print("   a validation-driven search would reject or favour these for the wrong reason.")
        kept = [r for r in rows if r["name"] not in flagged]
        if len(kept) >= 5:
            rho2 = spearman([r["val_mean"] for r in kept], [r["test_mean"] for r in kept])
            ci2 = list(rho_ci(rho2, len(kept)))
            print(f"   Spearman without them: {rho2:+.2f} (95% CI [{ci2[0]:+.2f}, {ci2[1]:+.2f}], n={len(kept)}) "
                  f"-> {verdict(rho2, *ci2)}")
    return {"spearman_val_test": rho, "spearman_ci95": [lo, hi], "disagree": flagged,
            "spearman_without_disagree": rho2, "spearman_without_disagree_ci95": ci2, "rows": rows}


def main():
    offset = int(os.environ.get("RB_SWEEP_SEED_OFFSET", "0"))
    seeds = list(range(offset, offset + int(os.environ.get("RB_SWEEP_SEEDS", "5"))))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    threads = os.environ.get("RB_SWEEP_THREADS", "").strip()
    if threads:  # main.py calls torch.set_num_threads(1) on GPU; the sweep did not -> A/B diagnostic
        torch.set_num_threads(int(threads))
    print(f"torch threads: {torch.get_num_threads()}")
    ctx = rb_data.prepare_data(C.DATASET, C.TASK, C.CACHE_DIR, device)
    ref = rb_data.reference_nodes(ctx, C.BASELINE)
    mode = os.environ.get("RB_SWEEP_MODE", "recipe")
    recipe = json.loads(os.environ["RB_SWEEP_RECIPE_JSON"]) if os.environ.get("RB_SWEEP_RECIPE_JSON") else None
    cfgs = sweep_configs(deep=os.environ.get("RB_SWEEP_DEEP", "0") == "1", mode=mode, recipe=recipe)
    custom = os.environ.get("RB_SWEEP_CONFIGS_JSON", "").strip()
    if custom:  # {"name": {overrides}, ...}; the first entry is the reference; recipe = tuned unless overridden
        spec = json.loads(Path(custom).read_text(encoding="utf-8"))
        cfgs = {name: {**C.BASELINE, **C.TUNED_TRAIN, **over} for name, over in spec.items() if not name.startswith("_")}
        mode = "custom"
    only = [x.strip().lower() for x in os.environ.get("RB_SWEEP_ONLY", "").split(",") if x.strip()]
    if only:  # keep the reference (first) configuration + those whose name contains one of the strings
        ref_name = next(iter(cfgs))
        cfgs = {n: c for n, c in cfgs.items() if n == ref_name or any(o in n.lower() for o in only)}
    print(f"sweep[{mode}]: {len(cfgs)} configs x {len(seeds)} seeds {seeds[0]}..{seeds[-1]} on {C.DATASET}/{C.TASK}")
    rows = run_sweep(ctx, cfgs, seeds, ref, device)
    out = report(rows)
    path = Path(os.environ.get("RB_SWEEP_OUT", "/app/sweep_results.json"))
    try:
        path.write_text(json.dumps(out, indent=2))
        print(f"saved {path}")
    except OSError:
        pass


if __name__ == "__main__":
    main()
