"""FROZEN copy of the official model, used ONLY by the baseline conditions (do not edit).

The refinement may change rb_model.py (used by `proposed`) but never this file, so the baselines
stay the official RelBench model whatever the LLM writes.

Heterogeneous GNN for RelBench entity tasks.

`Model` mirrors the official RelBench example (examples/model.py): a
PyTorch-Frame feature encoder, a relative-time encoder, a heterogeneous GNN and
an MLP head. The GNN type, depth, width, normalisation, dropout and residual
connections are controlled by the condition config (see rb_config.py).

This is the file the refinement loop is expected to edit (encoder choice,
forward pass, GNN layers, readout head).
"""

from typing import Any, Dict, List

import torch
import torch.nn.functional as F
from torch import Tensor
from torch.nn import Embedding, ModuleDict
from torch_frame.data.stats import StatType
from torch_geometric.data import HeteroData
from torch_geometric.nn import (
    MLP,
    GATv2Conv,
    GINConv,
    HeteroConv,
    LayerNorm,
    ResGatedGraphConv,
    SAGEConv,
    TransformerConv,
)
from torch_geometric.typing import EdgeType, NodeType

from relbench.modeling.nn import HeteroEncoder, HeteroGraphSAGE, HeteroTemporalEncoder

GNN_TYPES = ("sage", "gatv2", "gin", "transformer", "resgated")


def _gin_mlp(channels: int) -> torch.nn.Module:
    return torch.nn.Sequential(
        torch.nn.Linear(channels, channels),
        torch.nn.ReLU(),
        torch.nn.Linear(channels, channels),
    )


def make_conv(gnn_type: str, channels: int, aggr: str, heads: int):
    """One bipartite-capable convolution for a single edge type."""
    if gnn_type == "sage":
        return SAGEConv((channels, channels), channels, aggr=aggr)
    if gnn_type == "resgated":
        return ResGatedGraphConv((channels, channels), channels)
    if gnn_type == "gatv2":
        return GATv2Conv(
            (channels, channels),
            channels,
            heads=heads,
            concat=False,
            add_self_loops=False,
        )
    if gnn_type == "gin":
        return GINConv(_gin_mlp(channels))
    if gnn_type == "transformer":
        return TransformerConv(
            (channels, channels), channels, heads=heads, concat=False
        )
    raise ValueError(f"Unknown gnn_type {gnn_type!r}; choose from {GNN_TYPES}")


class HeteroGNN(torch.nn.Module):
    """Configurable heterogeneous message passing stack."""

    def __init__(
        self,
        node_types: List[NodeType],
        edge_types: List[EdgeType],
        channels: int,
        gnn_type: str = "sage",
        aggr: str = "sum",
        num_layers: int = 2,
        heads: int = 4,
        dropout: float = 0.0,
        residual: bool = False,
        jk: str = "last",
    ):
        super().__init__()
        self.dropout = dropout
        self.residual = residual
        self.jk = jk
        self.num_layers = num_layers
        # Jumping knowledge: concatenate the input and every layer output, project back to `channels`.
        self.jk_proj = ModuleDict()
        if jk == "cat":
            for node_type in node_types:
                self.jk_proj[node_type] = torch.nn.Linear((num_layers + 1) * channels, channels)

        self.convs = torch.nn.ModuleList()
        self.norms = torch.nn.ModuleList()
        for _ in range(num_layers):
            self.convs.append(
                HeteroConv(
                    {
                        edge_type: make_conv(gnn_type, channels, aggr, heads)
                        for edge_type in edge_types
                    },
                    aggr="sum",
                )
            )
            norm_dict = ModuleDict()
            for node_type in node_types:
                norm_dict[node_type] = LayerNorm(channels, mode="node")
            self.norms.append(norm_dict)

    def reset_parameters(self):
        for conv in self.convs:
            conv.reset_parameters()
        for norm_dict in self.norms:
            for norm in norm_dict.values():
                norm.reset_parameters()
        for lin in self.jk_proj.values():
            lin.reset_parameters()

    def forward(
        self,
        x_dict: Dict[NodeType, Tensor],
        edge_index_dict: Dict[EdgeType, Tensor],
        num_sampled_nodes_dict=None,
        num_sampled_edges_dict=None,
    ) -> Dict[NodeType, Tensor]:
        history = [x_dict]
        for conv, norm_dict in zip(self.convs, self.norms):
            out = conv(x_dict, edge_index_dict)
            out = {key: norm_dict[key](x) for key, x in out.items()}
            out = {key: x.relu() for key, x in out.items()}
            if self.dropout > 0.0:
                out = {
                    key: F.dropout(x, p=self.dropout, training=self.training)
                    for key, x in out.items()
                }
            if self.residual:
                out = {
                    key: x + x_dict[key] if key in x_dict else x
                    for key, x in out.items()
                }
            x_dict = out
            history.append(x_dict)
        final = dict(x_dict)
        if self.jk == "cat":
            for node_type, lin in self.jk_proj.items():
                if all(node_type in h for h in history):  # node types missing in a layer keep the last output
                    final[node_type] = lin(torch.cat([h[node_type] for h in history], dim=-1))
            return final
        return x_dict


def build_gnn(data: HeteroData, channels: int, cfg: dict) -> torch.nn.Module:
    gnn_type = cfg.get("gnn_type", "sage")
    dropout = float(cfg.get("dropout", 0.0))
    residual = bool(cfg.get("residual", False))
    jk = cfg.get("jk", "last")
    if gnn_type == "sage" and dropout == 0.0 and not residual and jk == "last":
        # Exactly the official RelBench GraphSAGE.
        return HeteroGraphSAGE(
            node_types=data.node_types,
            edge_types=data.edge_types,
            channels=channels,
            aggr=cfg.get("aggr", "sum"),
            num_layers=int(cfg["num_layers"]),
        )
    return HeteroGNN(
        node_types=data.node_types,
        edge_types=data.edge_types,
        channels=channels,
        gnn_type=gnn_type,
        aggr=cfg.get("aggr", "sum"),
        num_layers=int(cfg["num_layers"]),
        heads=int(cfg.get("heads", 4)),
        dropout=dropout,
        residual=residual,
        jk=jk,
    )


# Defaults of the official RelBench example (encoder: PyTorch Frame ResNet, 4 layers, width 128, dropout 0.2).
ENC_DEFAULTS = {"enc_layers": 4, "enc_width": 128, "enc_dropout": 0.2}


def build_encoder(data: HeteroData, col_stats_dict, channels: int, cfg: dict) -> torch.nn.Module:
    """Feature/column encoder. Exactly the official HeteroEncoder unless enc_* options differ."""
    kwargs = {}
    layers = int(cfg.get("enc_layers", ENC_DEFAULTS["enc_layers"]))
    width = int(cfg.get("enc_width", ENC_DEFAULTS["enc_width"]))
    drop = float(cfg.get("enc_dropout", ENC_DEFAULTS["enc_dropout"]))
    if (layers, width, drop) != (
        ENC_DEFAULTS["enc_layers"], ENC_DEFAULTS["enc_width"], ENC_DEFAULTS["enc_dropout"]
    ):
        kwargs["torch_frame_model_kwargs"] = {
            "channels": width, "num_layers": layers, "dropout_prob": drop,
        }
    return HeteroEncoder(
        channels=channels,
        node_to_col_names_dict={
            node_type: data[node_type].tf.col_names_dict for node_type in data.node_types
        },
        node_to_col_stats=col_stats_dict,
        **kwargs,
    )


class Model(torch.nn.Module):
    def __init__(
        self,
        data: HeteroData,
        col_stats_dict: Dict[str, Dict[str, Dict[StatType, Any]]],
        cfg: dict,
        out_channels: int,
        shallow_list: List[NodeType] = [],
    ):
        super().__init__()
        channels = int(cfg["channels"])

        self.use_time_encoding = bool(cfg.get("time_encoding", True))
        self.encoder = build_encoder(data, col_stats_dict, channels, cfg)
        self.temporal_encoder = HeteroTemporalEncoder(
            node_types=[
                node_type for node_type in data.node_types if "time" in data[node_type]
            ],
            channels=channels,
        )
        self.gnn = build_gnn(data, channels, cfg)
        head_layers = int(cfg.get("head_layers", 1))
        head_kwargs = {"hidden_channels": channels} if head_layers > 1 else {}
        self.head = MLP(
            channels,
            out_channels=out_channels,
            norm=cfg.get("norm", "batch_norm"),
            num_layers=head_layers,
            **head_kwargs,
        )
        self.embedding_dict = ModuleDict(
            {
                node: Embedding(data.num_nodes_dict[node], channels)
                for node in shallow_list
            }
        )
        self.reset_parameters()

    def reset_parameters(self):
        self.encoder.reset_parameters()
        self.temporal_encoder.reset_parameters()
        self.gnn.reset_parameters()
        self.head.reset_parameters()
        for embedding in self.embedding_dict.values():
            torch.nn.init.normal_(embedding.weight, std=0.1)

    def forward(self, batch: HeteroData, entity_table: NodeType) -> Tensor:
        seed_time = batch[entity_table].seed_time
        x_dict = self.encoder(batch.tf_dict)

        rel_time_dict = {}
        if self.use_time_encoding:
            rel_time_dict = self.temporal_encoder(
                seed_time, batch.time_dict, batch.batch_dict
            )
            for node_type, rel_time in rel_time_dict.items():
                x_dict[node_type] = x_dict[node_type] + rel_time

        for node_type, embedding in self.embedding_dict.items():
            x_dict[node_type] = x_dict[node_type] + embedding(batch[node_type].n_id)

        x_dict = self.gnn(
            x_dict,
            batch.edge_index_dict,
            batch.num_sampled_nodes_dict,
            batch.num_sampled_edges_dict,
        )
        return self.head(x_dict[entity_table][: seed_time.size(0)])


def build_model(data, col_stats_dict, cfg: dict, out_channels: int) -> Model:
    return Model(data, col_stats_dict, cfg, out_channels)
