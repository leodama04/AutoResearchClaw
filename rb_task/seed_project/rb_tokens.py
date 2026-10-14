"""Per-seed token sets (do not edit).

Some models (for example token/sequence-based models over a node's neighbourhood) expect, for every seed entity,
a fixed-length sequence of K "tokens": the seed node first, then the nodes of its sampled neighbourhood, each with
its features, node type, hop distance from the seed and relative time. Our NeighborLoader returns instead one
heterogeneous graph per batch. This helper converts the latter into the former, so that official code with that
input format can be IMPORTED instead of re-implemented.

Usage (inside rb_model.py, after the encoder and the temporal encoding have produced x_dict):

    from rb_tokens import seed_token_sets
    tok = seed_token_sets(batch, x_dict, entity_table, k=K)   # tok["tokens"]: [B, K, C], seed at position 0
"""

from __future__ import annotations

from typing import Dict

import torch


def node_type_ids(x_dict: Dict[str, torch.Tensor]) -> Dict[str, int]:
    """Stable integer id per node type (sorted names)."""
    return {nt: i for i, nt in enumerate(sorted(x_dict))}


def hop_distances(batch, x_dict: Dict[str, torch.Tensor], entity_table: str, num_seeds: int,
                  max_hops: int = 3) -> Dict[str, torch.Tensor]:
    """Hop distance of every sampled node from its own seed (edges taken in both directions).
    Nodes not reached within max_hops get max_hops + 1."""
    dev = x_dict[entity_table].device
    inf = max_hops + 1
    hop = {nt: torch.full((x.size(0),), inf, dtype=torch.long, device=dev) for nt, x in x_dict.items()}
    hop[entity_table][:num_seeds] = 0
    edges = [(et, ei.to(dev)) for et, ei in batch.edge_index_dict.items() if et[0] in hop and et[2] in hop]
    for h in range(1, max_hops + 1):
        changed = False
        for (src, _, dst), ei in edges:
            for a, b, ia, ib in ((src, dst, ei[0], ei[1]), (dst, src, ei[1], ei[0])):
                reach = hop[a][ia] == h - 1
                if not bool(reach.any()):
                    continue
                tgt = ib[reach]
                new = hop[b][tgt] > h
                if bool(new.any()):
                    hop[b][tgt[new]] = h
                    changed = True
        if not changed:
            break
    return hop


def seed_token_sets(batch, x_dict: Dict[str, torch.Tensor], entity_table: str, k: int = 128,
                    max_hops: int = 3) -> Dict[str, torch.Tensor]:
    """For each seed: the K closest sampled nodes (seed first, then by hop distance).

    Returns a dict with
      tokens    [B, K, C] node representations taken from x_dict (zeros where padded)
      mask      [B, K]    True for real tokens
      node_type [B, K]    integer node type (see node_type_ids), 0 where padded
      hop       [B, K]    hop distance from the seed (0 for the seed), 0 where padded
      rel_time  [B, K]    days between the seed time and the node time (0 if the table has no time), 0 where padded
    """
    seed_time = batch[entity_table].seed_time
    num_seeds = int(seed_time.size(0))
    dev = x_dict[entity_table].device
    types = node_type_ids(x_dict)
    hops = hop_distances(batch, x_dict, entity_table, num_seeds, max_hops)
    batch_dict = getattr(batch, "batch_dict", {}) or {}
    time_dict = getattr(batch, "time_dict", {}) or {}

    feats, seed_of, type_of, hop_of, time_of = [], [], [], [], []
    for nt, x in x_dict.items():
        n = x.size(0)
        if n == 0:
            continue
        sid = batch_dict.get(nt)
        sid = sid.to(dev) if sid is not None else torch.zeros(n, dtype=torch.long, device=dev)
        if nt == entity_table:  # seeds belong to themselves
            sid = sid.clone()
            sid[:num_seeds] = torch.arange(num_seeds, device=dev)
        t = time_dict.get(nt)
        if t is not None:
            rel = (seed_time.to(dev)[sid] - t.to(dev)).float() / 86400.0
        else:
            rel = torch.zeros(n, device=dev)
        feats.append(x)
        seed_of.append(sid.long())
        type_of.append(torch.full((n,), types[nt], dtype=torch.long, device=dev))
        hop_of.append(hops[nt])
        time_of.append(rel)
    feats = torch.cat(feats)
    seed_of, type_of = torch.cat(seed_of), torch.cat(type_of)
    hop_of, time_of = torch.cat(hop_of), torch.cat(time_of)

    # seed first, then closer hops first (stable inside a hop)
    key = seed_of * (max_hops + 3) + hop_of
    order = torch.sort(key, stable=True).indices
    seed_s = seed_of[order]
    counts = torch.bincount(seed_s, minlength=num_seeds)
    offsets = torch.cumsum(counts, 0) - counts
    pos = torch.arange(seed_s.size(0), device=dev) - offsets[seed_s]
    keep = pos < k
    rows, cols, idx = seed_s[keep], pos[keep], order[keep]

    out = {
        "tokens": torch.zeros(num_seeds, k, feats.size(1), dtype=feats.dtype, device=dev),
        "mask": torch.zeros(num_seeds, k, dtype=torch.bool, device=dev),
        "node_type": torch.zeros(num_seeds, k, dtype=torch.long, device=dev),
        "hop": torch.zeros(num_seeds, k, dtype=torch.long, device=dev),
        "rel_time": torch.zeros(num_seeds, k, dtype=torch.float, device=dev),
    }
    out["tokens"][rows, cols] = feats[idx]
    out["mask"][rows, cols] = True
    out["node_type"][rows, cols] = type_of[idx]
    out["hop"][rows, cols] = hop_of[idx]
    out["rel_time"][rows, cols] = time_of[idx]
    return out
