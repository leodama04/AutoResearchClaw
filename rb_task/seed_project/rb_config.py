"""Experiment configuration for the RelBench GNN study (seed project).

The pipeline's refinement loop is expected to modify ONLY the `PROPOSED` entry
(and, if needed, `rb_model.py` / training options). `BASELINE` is the official
RelBench GraphSAGE configuration and must stay unchanged.
"""

import os

DATASET = os.environ.get("RB_DATASET", "rel-f1")
TASK = os.environ.get("RB_TASK", "driver-top3")
CACHE_DIR = os.environ.get("RB_CACHE_DIR", "/tmp/relbench_materialized")

# Harness time budget (seconds). The harness asks us to stop at 80% of it.
TIME_BUDGET_SEC = int(os.environ.get("RB_TIME_BUDGET_SEC", "1500"))

# rel-f1 is small and noisy (validation: ~600 rows): 10 seeds; one run takes only seconds.
# SEED_OFFSET lets the pipeline re-evaluate the final model on FRESH seeds (never used for selection).
SEED_OFFSET = int(os.environ.get("RB_SEED_OFFSET", "0"))
N_SEEDS = int(os.environ.get("RB_N_SEEDS", "10"))
SEEDS = [SEED_OFFSET + i for i in range(N_SEEDS)]

# Default training settings (identical to the official RelBench GNN example).
TRAIN = {
    "lr": 0.005,
    "epochs": 10,
    "batch_size": 512,
    "max_steps_per_epoch": 2000,
    "num_neighbors": 128,
    # Upper bound on prod(fanouts) over the layers (official 2-layer config: 128*64 = 8192).
    # Deeper models get smaller per-layer fanouts so that memory stays comparable; with
    # disjoint temporal subgraphs memory grows with the PRODUCT of the fanouts.
    "max_fanout_product": 8192,
    "temporal_strategy": "uniform",
    "num_workers": 0,
    "weight_decay": 0.0,
}

# Official RelBench baseline: 2-layer heterogeneous GraphSAGE, 128 channels.
BASELINE = {
    "gnn_type": "sage",
    "num_layers": 2,
    "channels": 128,
    "aggr": "sum",
    "norm": "batch_norm",
    "dropout": 0.0,
    "residual": False,
    "heads": 4,
}

# Training recipe. "official" = the RelBench example settings: 1353 examples / batch 512 = 3 optimiser steps
# per epoch -> only 30 updates in total (under-trained: validation AUROC is bimodal across seeds).
# "tuned" = same architecture and optimiser, batch_size 128 (4x more updates), chosen with `./run.sh sweep`
# (val AUROC 0.768 vs 0.694, 1 GB peak, 3 s/run). With "tuned" a third condition, `baseline_tuned`, is added so
# that gains of `proposed` can be attributed to ARCHITECTURE and not to simply training longer; the recipe is
# then FIXED (the refinement may only change the architecture). Set with the env var RB_RECIPE.
RECIPE = os.environ.get("RB_RECIPE", "official")
TUNED_TRAIN = {"batch_size": 128}

# Current proposal (to be improved iteratively). Starts as a mild variation of the baseline.
# NOTE: on rel-f1 every extra message-passing layer makes each seed's temporal subgraph reach a
# large part of the database (measured: a 3-layer model needs >20 GB at batch 512 while the
# 2-layer baseline peaks at ~3.8 GB). Deeper models work (micro-batching keeps memory bounded)
# but are much slower per epoch.
PROPOSED = {
    "gnn_type": "sage",
    "num_layers": 2,
    "channels": 128,
    "aggr": "sum",
    "norm": "batch_norm",
    "dropout": 0.1,
    "residual": True,
    "heads": 4,
}

# Memory control (see rb_data.build_loaders): every condition processes about as many sampled
# nodes per optimiser step as the official baseline; larger batches are split into micro-batches
# (gradient accumulation). Scale < 1 shrinks the budget for ALL conditions (e.g. 0.5 to fit in
# less free VRAM when the LLM server is loaded). Set from the environment: RB_NODE_BUDGET_SCALE.
NODE_BUDGET_SCALE = float(os.environ.get("RB_NODE_BUDGET_SCALE", "1.0") or 1.0)

# ---- REFINEMENT INTERFACE ---------------------------------------------------------------------------
# The refinement loop changes ONLY this dictionary (and, in code mode, rb_model.py). It is merged onto the
# proposed configuration: an empty dict means `proposed` == `baseline_tuned`. Allowed keys/values: see
# rb_task/task_spec/search_space.json (architecture only; the training recipe is fixed).
PROPOSED_OVERRIDES = {}
# ---- END REFINEMENT INTERFACE -----------------------------------------------------------------------

BASELINE_TUNED = {**BASELINE, **TUNED_TRAIN}
if RECIPE == "tuned":
    PROPOSED = {**BASELINE_TUNED, **PROPOSED_OVERRIDES}  # empty overrides: starts identical to baseline_tuned
    CONDITIONS = {
        "baseline_graphsage": BASELINE,
        "baseline_tuned": BASELINE_TUNED,
        "proposed": PROPOSED,
    }
else:
    PROPOSED = {**PROPOSED, **PROPOSED_OVERRIDES}
    CONDITIONS = {
        "baseline_graphsage": BASELINE,
        "proposed": PROPOSED,
    }
PRIMARY_CONDITION = "proposed"

_TRAIN_KEYS = (
    "lr",
    "epochs",
    "batch_size",
    "max_steps_per_epoch",
    "num_neighbors",
    "max_fanout_product",
    "temporal_strategy",
    "num_workers",
    "weight_decay",
)


def merged_train_cfg(cfg: dict) -> dict:
    """Training settings for one condition: defaults overridden by cfg entries."""
    out = dict(TRAIN)
    out.update({k: cfg[k] for k in _TRAIN_KEYS if k in cfg})
    return out
