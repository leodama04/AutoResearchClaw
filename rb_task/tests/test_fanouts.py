#!/usr/bin/env python3
"""Offline test of the fanout rule (memory-safe sampling for deeper GNNs)."""
import sys
from math import prod
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "seed_project"))
import rb_config as C
import rb_data

f = rb_data.fanouts_for
base = dict(C.BASELINE)
assert f(base) == [128, 64], f(base)                                   # baseline ufficiale invariato
assert f({**base, "num_layers": 1}) == [128]
for L in (3, 4, 5):
    fan = f({**base, "num_layers": L})
    assert len(fan) == L and all(x >= 1 for x in fan), fan
    assert prod(fan) <= C.TRAIN["max_fanout_product"], (L, fan, prod(fan))
    assert fan == sorted(fan, reverse=True), fan                         # fanout decrescenti
print("fanouts 3/4/5 layer:", f({**base, "num_layers": 3}), f({**base, "num_layers": 4}), f({**base, "num_layers": 5}))
assert f({**base, "num_layers": 3, "fanouts": [20, 10, 5]}) == [20, 10, 5]   # override esplicito
assert f({**base, "num_layers": 3, "max_fanout_product": 10**9}) == [128, 64, 32]  # budget alzato a mano
try:
    f({**base, "num_layers": 3, "fanouts": [20, 10]}); raise SystemExit("doveva fallire")
except ValueError:
    pass
print("FANOUT TESTS PASSED")
