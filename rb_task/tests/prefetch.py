"""Build-time prefetch: RelBench dataset + tasks (robust to hash mismatches) and GloVe.

The target task (RB_TASK, default driver-top3) must succeed; the other tasks of the
dataset are prefetched on a best-effort basis (so switching task later needs no network).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rb_loader as L  # noqa: E402
from relbench.tasks import get_task_names  # noqa: E402

DATASET = os.environ.get("RB_DATASET", "rel-f1")
TARGET = os.environ.get("RB_TASK", "driver-top3")

summary = {}
for t in [TARGET] + [x for x in get_task_names(DATASET) if x != TARGET]:
    try:
        ds, task, src = L.load_dataset_and_task(DATASET, t)
        if t == TARGET:
            db = ds.get_db()
            print(f"{DATASET} tables:", {k: len(v.df) for k, v in db.table_dict.items()})
        sizes = {s: len(task.get_table(s)) for s in ("train", "val", "test")}  # also caches parquet
        summary[t] = {"sizes": sizes, **src}
        print(f"[ok] {t:16s} sizes={sizes} source={src}")
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] task {t} not prefetched: {exc!r}")
        if t == TARGET:
            raise

print("PREFETCH SUMMARY:", json.dumps(summary))

from sentence_transformers import SentenceTransformer  # noqa: E402

m = SentenceTransformer("sentence-transformers/average_word_embeddings_glove.6B.300d")
emb = m.encode(["Lewis Hamilton", "http://en.wikipedia.org/wiki/Monza"])
assert emb.shape == (2, 300), emb.shape
print("GloVe cached and verified, embedding shape", emb.shape)
