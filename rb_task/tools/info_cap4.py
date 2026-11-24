"""Facts for Chapter 4 (read-only: prints statistics, changes nothing).

Run on the node, inside the RelBench image, without the LLM:

  docker run --rm -e ARC_NO_LLM=1 -v ~/AutoResearchClaw:/app arc-relbench:latest \
      python3 /app/rb_task/tools/info_cap4.py > info_cap4.txt 2>&1

Prints: library versions, the tables of rel-f1 (rows, columns,
primary and foreign keys, time column, time span), and for each task the size of each split, the positives
(classification) or the label statistics (regression).
"""
import importlib.metadata as md
import platform
import subprocess
import sys

sys.path.insert(0, "/app/rb_task/seed_project")

print("=== software ===")
print("python", platform.python_version())
for pkg in ("torch", "torch_geometric", "pytorch_frame", "pyg_lib", "relbench", "sentence-transformers",
            "transformers", "pandas", "numpy", "scikit-learn", "lightgbm"):
    try:
        print(pkg, md.version(pkg))
    except Exception as exc:  # noqa: BLE001
        print(pkg, "n/a", type(exc).__name__)
try:
    import torch
    print("torch cuda", torch.version.cuda, "| cudnn", torch.backends.cudnn.version())
except Exception as exc:  # noqa: BLE001
    print("torch cuda n/a", exc)
try:
    out = subprocess.run(["/opt/llama/llama-server", "--version"], capture_output=True, text=True, timeout=60)
    print("llama-server:", (out.stdout + out.stderr).strip().splitlines()[-2:])
except Exception as exc:  # noqa: BLE001
    print("llama-server --version n/a", exc)
try:
    print("os (container):", open("/etc/os-release").read().split("PRETTY_NAME=")[1].splitlines()[0])
except Exception:  # noqa: BLE001
    pass

import rb_loader  # noqa: E402

print("\n=== rel-f1: tables (full database, upto_test_timestamp=False) ===")
dataset, task, source = rb_loader.load_dataset_and_task("rel-f1", "driver-top3")
print("data source:", source)
print("val_timestamp", dataset.val_timestamp, "| test_timestamp", dataset.test_timestamp)
for upto in (False, True):
    db = dataset.get_db(upto_test_timestamp=upto)
    tot_rows = sum(len(t.df) for t in db.table_dict.values())
    tot_cols = sum(len(t.df.columns) for t in db.table_dict.values())
    print(f"\nupto_test_timestamp={upto}: {len(db.table_dict)} tables, {tot_rows} rows, {tot_cols} columns")
    if upto:
        continue
    print("table | rows | columns | pkey | fkeys -> table | time col | first | last")
    for name, t in sorted(db.table_dict.items()):
        tc = t.time_col
        span = ("", "")
        if tc and tc in t.df:
            span = (str(t.df[tc].min())[:10], str(t.df[tc].max())[:10])
        fk = ", ".join(f"{c}->{p}" for c, p in (t.fkey_col_to_pkey_table or {}).items())
        print(f"{name} | {len(t.df)} | {len(t.df.columns)} | {t.pkey_col} | {fk or '-'} | {tc or '-'} | {span[0]} | {span[1]}")

print("\n=== tasks ===")
for tname in ("driver-top3", "driver-dnf", "driver-position"):
    try:
        _, tk, src = rb_loader.load_dataset_and_task("rel-f1", tname)
        print(f"\n{tname}: source={src} type={tk.task_type} entity={tk.entity_table}.{tk.entity_col} "
              f"target={tk.target_col} timedelta={tk.timedelta}")
        for split in ("train", "val", "test"):
            df = tk.get_table(split, mask_input_cols=False).df
            y = df[tk.target_col]
            line = (f"  {split}: rows={len(df)} entities={df[tk.entity_col].nunique()} "
                    f"timestamps={df[tk.time_col].nunique()} ({str(df[tk.time_col].min())[:10]} .. {str(df[tk.time_col].max())[:10]})")
            if "CLASSIFICATION" in str(tk.task_type):
                line += f" positives={int((y == 1).sum())} ({(y == 1).mean():.3f})"
            else:
                line += f" label mean={y.mean():.3f} std={y.std():.3f} min={y.min():.2f} max={y.max():.2f}"
            print(line)
    except Exception as exc:  # noqa: BLE001
        print(f"{tname}: failed: {exc!r}")
