"""RelBench GNN study: baseline GraphSAGE vs. the iteratively improved `proposed` model.

Entry point. Prints metric lines (`name: value`) through the experiment harness.
`primary_metric` = mean VALIDATION metric of the `proposed` condition over seeds
(sign-adjusted so that higher is better). Test metrics are reported only.
"""

import json
import os
import time

import numpy as np
import torch

import experiment_harness
import rb_config as C
from rb_data import build_loaders, prepare_data, reference_nodes
from rb_train import run_one


def _mean_std(values):
    arr = np.asarray(values, dtype=float)
    std = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
    return float(arr.mean()), std


def main():
    harness = experiment_harness.get_harness(time_budget=C.TIME_BUDGET_SEC)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    budget_gb = float(os.environ.get("RB_GPU_MEM_BUDGET_GB", "0") or 0)
    if device.type == "cuda":
        torch.set_num_threads(1)
        free, total = torch.cuda.mem_get_info()
        if budget_gb > 0:  # optional hard cap, e.g. to leave room for the LLM server
            torch.cuda.set_per_process_memory_fraction(min(1.0, budget_gb * 1e9 / total))
        print(f"gpu free={free / 1e9:.1f}GB total={total / 1e9:.1f}GB budget_gb={budget_gb or 'none'}")
    print(f"dataset={C.DATASET} task={C.TASK} device={device} seeds={C.SEEDS}")
    for name, cfg in C.CONDITIONS.items():
        print("CONFIG", name, json.dumps(cfg, sort_keys=True))

    t0 = time.time()
    ctx = prepare_data(C.DATASET, C.TASK, C.CACHE_DIR, device)
    print(f"graph ready in {time.time() - t0:.1f}s, node types: {list(ctx.data.node_types)}")

    ref_nodes = reference_nodes(ctx, C.BASELINE)
    loaders = {name: build_loaders(ctx, cfg, ref_nodes) for name, cfg in C.CONDITIONS.items()}

    results = {name: [] for name in C.CONDITIONS}
    # Seed-major order so that both conditions get the same number of seeds
    # if the time budget runs out.
    for seed in C.SEEDS:
        for name, cfg in C.CONDITIONS.items():
            if harness.should_stop():
                break
            t1 = time.time()
            res = run_one(ctx, loaders[name], cfg, seed, device, harness)
            res["seed"] = seed
            results[name].append(res)
            print(
                f"condition={name} seed={seed} val={res['val']:.4f} "
                f"test={res['test']:.4f} epochs={res['epochs_run']} time={time.time() - t1:.0f}s "
                f"peak_gb={res['peak_gpu_gb']:.1f}"
            )
            harness.log_result({"condition": name, **{k: v for k, v in res.items()}})
            harness.step()

    sign = 1.0
    summary = {}
    for name, res_list in results.items():
        if not res_list:
            continue
        sign = 1.0 if res_list[0]["higher_is_better"] else -1.0
        tune = res_list[0]["tune_metric"]
        val_mean, val_std = _mean_std([r["val"] for r in res_list])
        test_mean, test_std = _mean_std([r["test"] for r in res_list])
        summary[name] = (val_mean, val_std, test_mean, test_std, len(res_list), tune)
        harness.report_metric(f"{name}_val_{tune}_mean", val_mean)
        harness.report_metric(f"{name}_val_{tune}_std", val_std)
        harness.report_metric(f"{name}_test_{tune}_mean", test_mean)
        harness.report_metric(f"{name}_test_{tune}_std", test_std)
        harness.report_metric(f"{name}_n_seeds", float(len(res_list)))

    peaks = [r["peak_gpu_gb"] for rl in results.values() for r in rl]
    if peaks and max(peaks) > 0:
        harness.report_metric("peak_gpu_mem_gb", max(peaks))

    if C.PRIMARY_CONDITION not in summary:
        harness.finalize()
        raise RuntimeError("No completed run for the primary condition")

    primary = sign * summary[C.PRIMARY_CONDITION][0]
    harness.report_metric("primary_metric", primary)
    for ref_name, suffix in (("baseline_graphsage", ""), ("baseline_tuned", "_tuned")):
        ref = summary.get(ref_name)
        if ref is not None:
            harness.report_metric(f"improvement_over_baseline{suffix}_val", primary - sign * ref[0])
            harness.report_metric(
                f"improvement_over_baseline{suffix}_test",
                sign * (summary[C.PRIMARY_CONDITION][2] - ref[2]),
            )
    harness.finalize()


if __name__ == "__main__":
    main()
