#!/usr/bin/env python3
"""End-to-end smoke test of seed_project/main.py on RelBench's FakeDataset.

Patches only the data access (dataset/task/text embedder) and runs the real main(),
then parses stdout with the pipeline's own metric parser.
Run in the container:   ./run.sh smoke
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = Path(os.environ.get("RB_SEED_DIR", HERE.parent / "seed_project"))
HARNESS = Path(os.environ.get(
    "RB_HARNESS", "/app/researchclaw/experiment/harness_template.py"))
tmp = Path(tempfile.mkdtemp())
shutil.copy(HARNESS, tmp / "experiment_harness.py")
sys.path[:0] = [str(tmp), str(SEED), str(HERE)]
os.chdir(tmp)  # harness.finalize() writes results.json in the cwd

import torch
from torch_frame.testing.text_embedder import HashTextEmbedder
from relbench.datasets.fake import FakeDataset
from relbench.tasks.amazon import UserChurnTask

import rb_config as C
import rb_data
import rb_loader
import rb_text
import smoke_fake as SF

DS = FakeDataset()
rb_loader.load_dataset_and_task = lambda d, t: (DS, UserChurnTask(DS), {"db": "fake", "task": "fake"})
rb_text.GloveTextEmbedding = lambda device=None: HashTextEmbedder(8)
if not SF.HAS_PYG_LIB:
    rb_data._make_loader = lambda ctx_, fan, split, bs, tc, shuffle: SF._FullGraphLoader(
        ctx_, ctx_.table_inputs[split], bs, shuffle)

C.SEEDS = [0, 1]
C.TRAIN.update(epochs=2, max_steps_per_epoch=4, batch_size=32, num_neighbors=16)
C.CACHE_DIR = str(tmp / "cache")

import main as M

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    M.main()
out = buf.getvalue()
print(out[-1800:])

try:
    from researchclaw.pipeline._helpers import _parse_metrics_from_stdout
except Exception:  # noqa: BLE001
    sys.path.insert(0, os.environ.get("ARC_ROOT", "/app"))
    from researchclaw.pipeline._helpers import _parse_metrics_from_stdout

m = _parse_metrics_from_stdout(out)
need = ["primary_metric", "proposed_val_roc_auc_mean", "baseline_graphsage_val_roc_auc_mean",
        "proposed_test_roc_auc_mean", "improvement_over_baseline_val"]
missing = [k for k in need if k not in m]
assert not missing, f"metriche mancanti nello stdout: {missing}\n{sorted(m)}"
assert abs(m["primary_metric"] - m["proposed_val_roc_auc_mean"]) < 1e-9
assert m["proposed_n_seeds"] == 2 and m["baseline_graphsage_n_seeds"] == 2
if C.RECIPE == "tuned":
    for k in ("baseline_tuned_val_roc_auc_mean", "baseline_tuned_n_seeds",
              "improvement_over_baseline_tuned_val", "improvement_over_baseline_tuned_test"):
        assert k in m, f"manca {k} con RB_RECIPE=tuned"
    assert m["baseline_tuned_n_seeds"] == 2
    print("recipe=tuned: baseline_tuned presente, miglioramenti calcolati anche rispetto a baseline_tuned")
assert (tmp / "results.json").exists()
print("parsed metrics:", {k: round(v, 4) for k, v in m.items() if "mean" in k or k == "primary_metric"})
print("SMOKE MAIN PASSED")
