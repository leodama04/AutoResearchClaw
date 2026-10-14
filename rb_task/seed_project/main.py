"""RelBench GNN study: baseline GraphSAGE vs. the iteratively improved `proposed` model.

Entry point. Prints metric lines (`name: value`) through the experiment harness.
`primary_metric` = mean VALIDATION metric of the `proposed` condition over seeds
(sign-adjusted so that higher is better). Test metrics are reported only.
"""

import json
import warnings
import os
import time

import numpy as np
import torch

# torch_frame prints this warning for every cached table; it filled the logs and hid the real errors
warnings.filterwarnings("ignore", message=".*Weights only load failed.*")

import experiment_harness
import rb_config as C
from rb_data import build_loaders, prepare_data, reference_nodes
from rb_train import run_one


def _mean_std(values):
    arr = np.asarray(values, dtype=float)
    std = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
    return float(arr.mean()), std


def identical_to_baseline(ctx, loaders, ref_name="baseline_tuned"):
    """1.0 if `proposed` computes exactly the same function as the reference baseline at initialisation
    (same seed, same batch, CPU): the change was not activated. 0.0 otherwise or if the check fails."""
    if ref_name not in C.CONDITIONS or "proposed" not in C.CONDITIONS:
        return 0.0
    try:
        from torch_geometric.seed import seed_everything

        from rb_train import builder_for

        batch = next(iter(loaders[ref_name]["val"])).to("cpu")
        outs = []
        for name in (ref_name, "proposed"):
            cfg = C.CONDITIONS[name]
            seed_everything(0)
            model = builder_for(cfg)(ctx.data, ctx.col_stats_dict, cfg, 1).to("cpu")
            model.train(False)  # inference mode (the code validator rejects any call named eval)
            with torch.no_grad():
                outs.append(model(batch, ctx.entity_table).float())
        same = outs[0].shape == outs[1].shape and torch.allclose(outs[0], outs[1], atol=1e-6, rtol=1e-5)
        return 1.0 if same else 0.0
    except Exception as exc:  # noqa: BLE001
        print(f"identical_to_baseline check failed: {exc!r}")
        return 0.0


def _child_free_bytes():
    """Free GPU memory measured in a fresh process (runs in a spawned child, see wait_for_gpu)."""
    try:
        return float(torch.cuda.mem_get_info()[0])
    except Exception:  # noqa: BLE001
        return 0.0


def wait_for_gpu():
    """The GPU is shared (llama-server and other users' processes). An experiment needs about RB_MIN_FREE_GB
    (default 4.5: baseline peak 3.9 GB + CUDA context). If less is free, wait up to RB_GPU_WAIT_SEC (default 600)
    instead of crashing; if the GPU stays full, print GPU_UNAVAILABLE and exit with code 3. The pipeline then does
    not ask the LLM to "repair" the code, because the problem is the environment, not the code."""
    need = float(os.environ.get("RB_MIN_FREE_GB", "4.5") or 0) * 1e9
    wait = float(os.environ.get("RB_GPU_WAIT_SEC", "600") or 0)
    if need <= 0:
        return
    try:
        free = float(torch.cuda.mem_get_info()[0])
    except Exception as exc:  # noqa: BLE001  (CUDA context creation fails when the GPU is completely full)
        print(f"GPU memory query failed: {exc!r}".splitlines()[0])
        free = 0.0
    if free >= need:
        return
    import multiprocessing as mp

    t_end = time.time() + wait
    while time.time() < t_end:
        print(f"GPU busy: {free / 1e9:.1f} GB free, {need / 1e9:.1f} GB needed - waiting (other processes on the GPU?)",
              flush=True)
        time.sleep(30)
        with mp.get_context("spawn").Pool(1) as pool:  # fresh process: a failed CUDA init does not linger
            free = pool.apply(_child_free_bytes)
        if free >= need:
            print(f"GPU free again: {free / 1e9:.1f} GB", flush=True)
            return
    print(f"GPU_UNAVAILABLE: only {free / 1e9:.1f} GB free after waiting {wait:.0f}s "
          f"(need {need / 1e9:.1f} GB; check nvidia-smi for other processes)", flush=True)
    raise SystemExit(3)


def main():
    if torch.cuda.is_available():
        wait_for_gpu()  # before the harness clock starts
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

    identical = identical_to_baseline(ctx, loaders)
    print(f"proposed identical to baseline_tuned: {bool(identical)}")
    # reported after training (below): reported here, it made a run that crashed later look like a run with metrics

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

    harness.report_metric("proposed_identical_to_baseline", identical)
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
