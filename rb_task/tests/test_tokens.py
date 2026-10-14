#!/usr/bin/env python3
"""rb_tokens: per-seed token sets on a hand-made batch, then through the OFFICIAL RelGT local layer if available."""
import os, sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "seed_project")]
import torch
from rb_tokens import seed_token_sets, hop_distances

# grafo eterogeneo minimo: 2 semi (piloti 0 e 1); risultati collegati ai piloti; gare collegate ai risultati
class B(dict):
    pass
batch = B()
batch["drivers"] = SimpleNamespace(seed_time=torch.tensor([1000 * 86400, 2000 * 86400]))
batch.edge_index_dict = {
    # results -> drivers (risultato r0, r1 del seme 0; r2 del seme 1)
    ("results", "f2p_driverId", "drivers"): torch.tensor([[0, 1, 2], [0, 0, 1]]),
    # races -> results (gara g0 collegata a r0; g1 a r2)
    ("races", "rev_f2p_raceId", "results"): torch.tensor([[0, 1], [0, 2]]),
}
x_dict = {"drivers": torch.randn(3, 4), "results": torch.randn(3, 4), "races": torch.randn(2, 4)}
batch.batch_dict = {"drivers": torch.tensor([0, 1, 0]), "results": torch.tensor([0, 0, 1]), "races": torch.tensor([0, 1])}
batch.time_dict = {"results": torch.tensor([990, 995, 1990]) * 86400, "races": torch.tensor([980, 1980]) * 86400}

hops = hop_distances(batch, x_dict, "drivers", 2, max_hops=3)
assert hops["drivers"].tolist() == [0, 0, 4] and hops["results"].tolist() == [1, 1, 1] and hops["races"].tolist() == [2, 2], hops
tok = seed_token_sets(batch, x_dict, "drivers", k=4)
assert tok["tokens"].shape == (2, 4, 4) and tok["mask"].tolist() == [[True, True, True, True], [True, True, True, False]], tok["mask"]
assert torch.equal(tok["tokens"][0, 0], x_dict["drivers"][0]) and torch.equal(tok["tokens"][1, 0], x_dict["drivers"][1])  # seme in posizione 0
assert tok["hop"][0].tolist() == [0, 1, 1, 2] and tok["hop"][1].tolist()[:3] == [0, 1, 2]
assert abs(float(tok["rel_time"][0, 1]) - 10.0) < 1e-4 and abs(float(tok["rel_time"][1, 2]) - 20.0) < 1e-4
tok2 = seed_token_sets(batch, x_dict, "drivers", k=2)
assert tok2["hop"][0].tolist() == [0, 1], "con K piccolo si tengono i nodi piu' vicini"
print("OK 1: token per seme (seme per primo, ordinati per salti, tempo relativo in giorni, padding)")

# 2) passaggio nel layer locale UFFICIALE di RelGT (se il repository e einops sono disponibili)
relgt = os.environ.get("RELGT_DIR", "/tmp/relgt_probe")
if Path(relgt, "model.py").exists():
    sys.path.insert(0, relgt)
    try:
        from model import RelGTLayer
        from encoders import NeighborHopEncoder, NeighborNodeTypeEncoder
    except ImportError as exc:
        print("codice RelGT non importabile qui:", exc)
    else:
        layer = RelGTLayer(in_channels=4, out_channels=4, local_num_layers=1, global_dim=4, num_nodes=10,
                           heads=1, conv_type="local", sample_node_len=4)
        hop_enc = NeighborHopEncoder(max_neighbor_hop=4, embedding_dim=4)
        h = tok["tokens"] + hop_enc(tok["hop"])
        out = layer(h, None, None)
        assert out.shape[0] == 2, out.shape
        print("OK 2: i token passano nel RelGTLayer ufficiale (conv_type='local') ->", tuple(out.shape))
# 3) su un batch vero della pipeline (FakeDataset di RelBench), con le rappresentazioni prodotte dall'encoder ufficiale
sys.path.insert(0, str(HERE))
try:
    import smoke_fake as SF
except Exception as exc:  # noqa: BLE001
    print("smoke_fake non disponibile:", exc)
else:
    import rb_model, rb_config as C
    ctx = SF.build_ctx()
    model = rb_model.build_model(ctx.data, ctx.col_stats_dict, dict(C.BASELINE), 1)
    batch = next(iter(SF._FullGraphLoader(ctx, ctx.table_inputs["train"], 8, False)))
    x_dict = model.encoder(batch.tf_dict)
    tok = seed_token_sets(batch, x_dict, ctx.entity_table, k=32)
    nseed = batch[ctx.entity_table].seed_time.size(0)
    assert tok["tokens"].shape == (nseed, 32, x_dict[ctx.entity_table].size(1)) and bool(tok["mask"][:, 0].all())
    assert int(tok["hop"][:, 0].max()) == 0 and int(tok["hop"][tok["mask"]].max()) >= 1
    print(f"OK 3: batch reale -> token {tuple(tok['tokens'].shape)}, salti fino a {int(tok['hop'][tok['mask']].max())}")
print("TOKENS TESTS PASSED")
