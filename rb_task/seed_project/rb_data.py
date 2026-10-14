"""Data loading for RelBench entity tasks (graph construction + neighbour loaders).

Follows the official RelBench v1 example (examples/gnn_node.py). Do NOT change
the evaluation protocol here: train/val tables are used for fitting/selection,
the test table is only used to report the final number.
"""

import json
import warnings
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import torch

# torch_frame prints this warning for every cached table; it filled the logs and hid the real errors
warnings.filterwarnings("ignore", message=".*Weights only load failed.*")
from torch_frame import stype
from torch_frame.config.text_embedder import TextEmbedderConfig
from torch_geometric.data import HeteroData
from torch_geometric.loader import NeighborLoader

from relbench.base import Dataset, EntityTask, Table
from relbench.modeling.graph import get_node_train_table_input, make_pkey_fkey_graph
from relbench.modeling.utils import get_stype_proposal

import rb_config as C
import rb_loader
import rb_text


@dataclass
class DataContext:
    dataset: Dataset
    task: EntityTask
    data: HeteroData
    col_stats_dict: Dict[str, Any]
    tables: Dict[str, Table]  # "train", "val", "test" (test has no labels)
    table_inputs: Dict[str, Any]
    entity_table: str


def prepare_data(
    dataset_name: str,
    task_name: str,
    cache_dir: str,
    device: torch.device,
    text_embedder=None,
) -> DataContext:
    # Data and task tables are pre-downloaded in the Docker image (offline-first loader).
    dataset, task, source = rb_loader.load_dataset_and_task(dataset_name, task_name)
    print(f"data source: {source}")

    stypes_cache_path = Path(f"{cache_dir}/{dataset_name}/stypes.json")
    try:
        with open(stypes_cache_path, "r") as f:
            col_to_stype_dict = json.load(f)
        for table, col_to_stype in col_to_stype_dict.items():
            for col, stype_str in col_to_stype.items():
                col_to_stype[col] = stype(stype_str)
    except FileNotFoundError:
        col_to_stype_dict = get_stype_proposal(dataset.get_db())
        Path(stypes_cache_path).parent.mkdir(parents=True, exist_ok=True)
        with open(stypes_cache_path, "w") as f:
            json.dump(col_to_stype_dict, f, indent=2, default=str)

    embedder = (
        text_embedder
        if text_embedder is not None
        else rb_text.GloveTextEmbedding(device=device)
    )

    data, col_stats_dict = make_pkey_fkey_graph(
        dataset.get_db(),
        col_to_stype_dict=col_to_stype_dict,
        text_embedder_cfg=TextEmbedderConfig(
            text_embedder=embedder, batch_size=256
        ),
        cache_dir=f"{cache_dir}/{dataset_name}/materialized",
    )

    tables: Dict[str, Table] = {}
    table_inputs: Dict[str, Any] = {}
    for split in ["train", "val", "test"]:
        tables[split] = task.get_table(split)  # test labels are masked by RelBench
        table_inputs[split] = get_node_train_table_input(
            table=tables[split], task=task
        )

    return DataContext(
        dataset=dataset,
        task=task,
        data=data,
        col_stats_dict=col_stats_dict,
        tables=tables,
        table_inputs=table_inputs,
        entity_table=task.entity_table,
    )


def fanouts_for(cfg: dict) -> list:
    """Neighbours sampled per layer.

    Default (official RelBench rule): num_neighbors / 2**i. Because every seed node gets its
    own temporal subgraph, memory grows with the product of the fanouts; if that product
    exceeds `max_fanout_product` all fanouts are scaled down. The official 2-layer baseline
    ([128, 64], product 8192) is never altered. `cfg["fanouts"]` (one int per layer) overrides.
    """
    tc = C.merged_train_cfg(cfg)
    num_layers = int(cfg["num_layers"])
    explicit = cfg.get("fanouts")
    if explicit:
        fan = [max(1, int(x)) for x in explicit]
        if len(fan) != num_layers:
            raise ValueError(f"fanouts has {len(fan)} entries but num_layers={num_layers}")
        return fan
    fan = [max(1, int(tc["num_neighbors"] / 2**i)) for i in range(num_layers)]
    budget = int(tc["max_fanout_product"])
    scale = 1.0
    prod = 1
    for x in fan:
        prod *= x
    if budget > 0 and prod > budget:
        scale = (budget / prod) ** (1.0 / num_layers)
        fan = [max(1, int(x * scale)) for x in fan]
    return fan


def plan_micro_batches(nodes_per_batch: float, ref_nodes: float, batch_size: int):
    """(micro_batch_size, accumulation_steps) so that a micro-batch has about as many sampled
    nodes as the reference (official baseline) batch. Pure function (unit-tested)."""
    if ref_nodes <= 0 or nodes_per_batch <= ref_nodes * 1.05:
        return batch_size, 1
    accum = int(math.ceil(nodes_per_batch / ref_nodes))
    accum = min(accum, max(1, batch_size // 8))  # micro-batches of at least 8 seeds
    micro = int(math.ceil(batch_size / accum))
    return micro, int(math.ceil(batch_size / micro))


def _make_loader(ctx: DataContext, fanouts: list, split: str, batch_size: int,
                 tc: dict, shuffle: bool) -> NeighborLoader:
    table_input = ctx.table_inputs[split]
    return NeighborLoader(
        ctx.data,
        num_neighbors=fanouts,
        time_attr="time",
        input_nodes=table_input.nodes,
        input_time=table_input.time,
        transform=table_input.transform,
        batch_size=batch_size,
        temporal_strategy=tc["temporal_strategy"],
        shuffle=shuffle,
        num_workers=int(tc["num_workers"]),
        persistent_workers=int(tc["num_workers"]) > 0,
    )


def mean_nodes_per_batch(ctx: DataContext, cfg: dict, n_batches: int = 2) -> float:
    """Average number of sampled nodes in a training batch (measured on CPU, no GPU needed)."""
    tc = C.merged_train_cfg(cfg)
    loader = _make_loader(ctx, fanouts_for(cfg), "train", int(tc["batch_size"]), tc, True)
    total, n = 0, 0
    for batch in loader:
        total += sum(batch[nt].num_nodes for nt in batch.node_types)
        n += 1
        if n >= n_batches:
            break
    return total / max(n, 1)


def reference_nodes(ctx: DataContext, base_cfg: dict) -> float:
    """Node budget = nodes per batch of the official baseline x NODE_BUDGET_SCALE."""
    ref = mean_nodes_per_batch(ctx, base_cfg) * C.NODE_BUDGET_SCALE
    print(f"node budget per optimiser step: {ref:,.0f} sampled nodes (scale {C.NODE_BUDGET_SCALE})")
    return ref


def build_loaders(ctx: DataContext, cfg: dict, ref_nodes: float = 0.0) -> Dict[str, Any]:
    """Temporal neighbour loaders for one condition.

    If `ref_nodes` > 0 and this condition samples more nodes per batch than the reference, the
    batch is split into `accum` micro-batches (gradient accumulation, same effective batch size
    and same number of optimiser steps) -- memory stays comparable to the baseline.
    The returned dict has the keys "train", "val", "test" and "_accum" (an int).
    """
    tc = C.merged_train_cfg(cfg)
    fan = fanouts_for(cfg)
    bs = int(tc["batch_size"])
    micro, accum = bs, 1
    npb = 0.0
    if ref_nodes > 0:
        npb = mean_nodes_per_batch(ctx, cfg)
        micro, accum = plan_micro_batches(npb, ref_nodes, bs)
        print(f"  layers={cfg['num_layers']} fanouts={fan} nodes/batch={npb:,.0f} "
              f"-> micro_batch={micro} x accum={accum} (effective batch {bs})")
    else:
        print(f"  layers={cfg['num_layers']} fanouts={fan} batch_size={bs}")
    loaders: Dict[str, Any] = {
        split: _make_loader(ctx, fan, split, micro, tc, shuffle=split == "train")
        for split in ["train", "val", "test"]
    }
    loaders["_accum"] = accum
    return loaders
