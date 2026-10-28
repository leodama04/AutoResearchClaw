#!/usr/bin/env python3
"""Test of rb_task/tools/tool_stats.py on a toy run directory (no real run needed).

Checks: official code imported by an attempt is read from the attempt's own code also when the field arc_official_code
is missing (runs of kits before 0.6), vendor files themselves do not count, the gnn_type comes from PROPOSED_OVERRIDES and
not from BASELINE, the val-test correlation reports how many attempts it uses,
a final model that does not import official code says 'no'.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "tools" / "tool_stats.py"
tmp = Path(tempfile.mkdtemp())
run = tmp / "rc-20260101-000000-test"
(run / "stage-10" / "experiment").mkdir(parents=True)
(run / "stage-10" / "experiment" / "rb_model.py").write_text("def build_model():\n    return 0\n")
d = run / "stage-13"
CFG = 'BASELINE = {"gnn_type": "sage"}\nPROPOSED_OVERRIDES = {"gnn_type": "%s"}\nPROPOSED_SOURCE = "K1: x"\n'
its = []
for i, (gt, code, field) in enumerate([
        ("relgt", "from vendor_relgt_model import RelGT\n", None),        # old kit: no field, import in the code
        ("gatv2", "import torch\n", None),                                # no official code
        ("relgnn", "import torch\n", ["vendor_relgnn_model"]),            # field only (kit >= 0.6)
        ("gatv2", "import torch\n", None)]):
    v = d / f"v{i}"
    v.mkdir(parents=True)
    (v / "rb_config.py").write_text(CFG % gt)
    (v / "rb_model.py").write_text(code + "def build_model():\n    return 1\n")
    (v / "vendor_other.py").write_text("import vendor_inner\n")              # vendor files never count
    it = {"version_dir": f"v{i}/", "metric": 0.7 + 0.01 * i, "improved": i == 1,
          "sandbox": {"returncode": 0, "metrics": {"proposed_val_roc_auc_mean": 0.8 + 0.01 * i,
                                                   "proposed_test_roc_auc_mean": 0.75 + 0.01 * i}}}
    if field is not None:
        it["arc_official_code"] = field
    its.append(it)
fin = d / "experiment_final"
fin.mkdir()
(fin / "rb_config.py").write_text(CFG % "gatv2")
(fin / "rb_model.py").write_text("import torch\ndef build_model():\n    return 1\n")
(fin / "vendor_relgt_model.py").write_text("class RelGT: pass\n")    # vendored but not imported
(d / "refinement_log.json").write_text(json.dumps({"generated": "2026-01-01T00:00:00", "iterations": its}))
out = tmp / "stats"
r = subprocess.run([sys.executable, str(TOOL), str(run), "--out", str(out)], capture_output=True, text=True)
print(r.stdout[-800:], r.stderr[-800:])
assert r.returncode == 0
md = Path(str(out) + ".md").read_text()
row = next(ln for ln in md.splitlines() if ln.startswith("| tentativi con codice ufficiale importato"))
assert row.split("|")[2].strip() == "2", row
mods = next(ln for ln in md.splitlines() if ln.startswith("| moduli ufficiali importati"))
assert "vendor_relgt_model: 1" in mods and "vendor_relgnn_model: 1" in mods and "vendor_inner" not in mods, mods
gts = next(ln for ln in md.splitlines() if ln.startswith("| più provati"))
assert "gatv2: 2" in gts and "sage" not in gts, gts
cor = next(ln for ln in md.splitlines() if ln.startswith("| correlazione val-test"))
assert "(n=4)" in cor, cor
fu = next(ln for ln in md.splitlines() if ln.startswith("| modello finale: usa codice ufficiale"))
assert fu.split("|")[2].strip() == "no", fu
print("TOOL STATS TEST PASSED")
