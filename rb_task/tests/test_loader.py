#!/usr/bin/env python3
"""Offline unit test of rb_loader (no network, no real RelBench data)."""
import sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "seed_project"))
import rb_loader as L

calls = []
class Obj:
    def __init__(self, kind, name, download): self.kind, self.name, self.download = kind, name, download

def make_fakes(task_hash_error=False, db_hash_error=False, other_error=False):
    def gd(name, download=False):
        calls.append(("db", name, download))
        if download and db_hash_error:
            raise ValueError("SHA256 hash of downloaded file (db.zip) does not match the known hash")
        return Obj("db", name, download)
    def gt(ds, name, download=False):
        calls.append(("task", name, download))
        if download and task_hash_error:
            raise ValueError("SHA256 hash of downloaded file (driver-dnf.zip) does not match the known hash")
        if download and other_error:
            raise ValueError("something else is wrong")
        return Obj("task", name, download)
    return gd, gt

def fresh_cache(db=False, task=False, name="driver-top3"):
    root = Path(tempfile.mkdtemp())
    if db:
        (root / "rel-f1" / "db").mkdir(parents=True); (root / "rel-f1" / "db" / "x.parquet").write_text("x")
    if task:
        t = root / "rel-f1" / "tasks" / name; t.mkdir(parents=True)
        for s in L.SPLITS: (t / f"{s}.parquet").write_text("x")
    L._cache_root = lambda r=root: r
    return root

# 1) tutto in cache -> nessun download, nessun errore di hash possibile
fresh_cache(db=True, task=True); calls.clear()
L.get_dataset, L.get_task = make_fakes(task_hash_error=True, db_hash_error=True)
ds, task, src = L.load_dataset_and_task("rel-f1", "driver-top3")
assert all(c[2] is False for c in calls), calls
assert src == {"db": "cache", "task": "cache"}, src
print("OK 1: cache completa -> offline, nessun controllo hash")

# 2) niente in cache, download riuscito
fresh_cache(); calls.clear()
L.get_dataset, L.get_task = make_fakes()
ds, task, src = L.load_dataset_and_task("rel-f1", "driver-top3")
assert src == {"db": "download", "task": "download"}, src
print("OK 2: download riuscito")

# 3) hash mismatch sul task -> fallback locale (download=False) e provenienza registrata
root = fresh_cache(db=True); calls.clear()
L.get_dataset, L.get_task = make_fakes(task_hash_error=True)
ds, task, src = L.load_dataset_and_task("rel-f1", "driver-dnf")
assert src["task"] == "local" and task.download is False, (src, task.download)
assert ("task", "driver-dnf", True) in calls and ("task", "driver-dnf", False) in calls, calls
assert L.read_source("rel-f1", "driver-dnf")["task"] == "local"
print("OK 3: hash mismatch -> task calcolato localmente, provenienza registrata:", src)

# 4) una seconda esecuzione con cache completa riporta la provenienza registrata
t = root / "rel-f1" / "tasks" / "driver-dnf"; t.mkdir(parents=True)
for s in L.SPLITS: (t / f"{s}.parquet").write_text("x")
ds, task, src = L.load_dataset_and_task("rel-f1", "driver-dnf")
assert src.get("task") == "local" and src.get("from_cache") is True, src
print("OK 4: run successiva legge la provenienza dalla cache:", src)

# 5) mismatch sul database -> fallback locale
fresh_cache(); calls.clear()
L.get_dataset, L.get_task = make_fakes(db_hash_error=True)
ds, task, src = L.load_dataset_and_task("rel-f1", "driver-top3")
assert src["db"] == "local", src
print("OK 5: hash mismatch sul database -> elaborazione locale")

# 6) errori non legati all'hash non vengono nascosti
fresh_cache(db=True)
L.get_dataset, L.get_task = make_fakes(other_error=True)
try:
    L.load_dataset_and_task("rel-f1", "driver-top3"); raise SystemExit("doveva fallire")
except ValueError as e:
    assert "something else" in str(e)
print("OK 6: errori diversi dall'hash propagati")
print("LOADER TESTS PASSED")
