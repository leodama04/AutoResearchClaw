"""Offline-first loading of a RelBench dataset + task (relbench 1.1.0).

Why this exists: relbench 1.1.0 verifies the downloaded files against SHA256 hashes
shipped in the package. Some files on relbench.stanford.edu were modified after the
1.1.0 release (observed: rel-f1/tasks/driver-dnf.zip), so `get_task(..., download=True)`
can raise "SHA256 hash ... does not match". This module:

  1. uses the local cache when it is complete (no network, no hash check);
  2. otherwise tries the official download;
  3. on a hash mismatch, falls back to computing the task tables locally from the
     database with the relbench 1.1.0 task definition (the "v1" definition);
  4. records where the data came from (cache dir / rb_sources.json) for provenance.
"""

import json
from pathlib import Path

import pooch

from relbench.datasets import get_dataset
from relbench.tasks import get_task

SPLITS = ("train", "val", "test")


def _cache_root() -> Path:
    return Path(pooch.os_cache("relbench"))


def _db_cached(dataset_name: str) -> bool:
    db = _cache_root() / dataset_name / "db"
    return db.is_dir() and any(db.iterdir())


def _task_cached(dataset_name: str, task_name: str) -> bool:
    base = _cache_root() / dataset_name / "tasks" / task_name
    return all((base / f"{s}.parquet").is_file() for s in SPLITS)


def _is_hash_error(exc: Exception) -> bool:
    return isinstance(exc, ValueError) and "hash" in str(exc).lower()


def _sources_path() -> Path:
    return _cache_root() / "rb_sources.json"


def read_source(dataset_name: str, task_name: str):
    try:
        data = json.loads(_sources_path().read_text())
        return data.get(f"{dataset_name}/{task_name}")
    except (OSError, ValueError):
        return None


def record_source(dataset_name: str, task_name: str, src: dict) -> None:
    try:
        path = _sources_path()
        data = json.loads(path.read_text()) if path.is_file() else {}
        data[f"{dataset_name}/{task_name}"] = src
        path.write_text(json.dumps(data, indent=2))
    except (OSError, ValueError):
        pass


def load_dataset_and_task(dataset_name: str, task_name: str):
    """Return (dataset, task, source) where source = {"db": ..., "task": ...} with
    values "cache", "download" or "local" (computed from the database)."""
    src = {"db": "cache", "task": "cache"}
    recorded = read_source(dataset_name, task_name)
    dataset = None
    task = None

    if _db_cached(dataset_name):
        dataset = get_dataset(dataset_name, download=False)
    else:
        try:
            dataset = get_dataset(dataset_name, download=True)
            src["db"] = "download"
        except ValueError as exc:
            if not _is_hash_error(exc):
                raise
            print(f"WARNING: hash mismatch for database {dataset_name}: {exc}\n"
                  "         processing it locally instead")
            dataset = get_dataset(dataset_name, download=False)
            src["db"] = "local"

    if _task_cached(dataset_name, task_name):
        task = get_task(dataset_name, task_name, download=False)
    else:
        try:
            task = get_task(dataset_name, task_name, download=True)
            src["task"] = "download"
        except ValueError as exc:
            if not _is_hash_error(exc):
                raise
            print(f"WARNING: the server file for task {dataset_name}/{task_name} does not match the "
                  f"relbench 1.1.0 hash ({exc}).\n         Computing the task tables locally from the "
                  "database with the relbench 1.1.0 definition.")
            task = get_task(dataset_name, task_name, download=False)
            src["task"] = "local"

    if src == {"db": "cache", "task": "cache"} and recorded:
        src = {**recorded, "from_cache": True}
    else:
        record_source(dataset_name, task_name, src)
    return dataset, task, src
