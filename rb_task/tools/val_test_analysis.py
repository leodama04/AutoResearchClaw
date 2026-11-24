#!/usr/bin/env python3
"""Why do validation and test disagree on rel-f1? A data-only comparison of the splits.

No model is trained and no GPU is used: the script reads the rel-f1 tables already stored in the
arc-relbench image and compares the validation split (timestamps 2005-2009) with the test split
(timestamps from 2010). Nothing is written to disk.

Run inside the arc-relbench container, from the repo root (/app):

    python3 rb_task/tools/val_test_analysis.py --tasks driver-top3,driver-dnf

Sections, for each task:
  1. size of the splits: examples, timestamps, positives, drivers;
  2. which drivers: overlap between the splits;
  3. who the positives are: drivers and teams with the most positive examples;
  4. how predictable each split is with simple rules computed only from the past
     (AUROC of each rule on train, validation and test, and per year);
and once for the database:
  5. how Formula 1 changed per season (cars per qualifying, teams, who takes the top 3, finishing rate).
"""
import argparse
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, "/app/rb_task/seed_project")
import rb_loader  # noqa: E402  (offline-first loader of the experiments)

ap = argparse.ArgumentParser()
ap.add_argument("--dataset", default="rel-f1")
ap.add_argument("--tasks", default="driver-top3,driver-dnf")
a = ap.parse_args()
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
SPLITS = ("train", "val", "test")
YEAR = pd.Timedelta(days=365)
YEAR_NS = int(YEAR / pd.Timedelta(1, "ns"))


def hr(title):
    print("\n" + "=" * 100 + f"\n{title}\n" + "=" * 100)


# ----------------------------------------------------------------------------- database
dataset, _, _ = rb_loader.load_dataset_and_task(a.dataset, "driver-top3")
db = dataset.get_db(upto_test_timestamp=False)  # the whole database, including the test period
T = {k: v.df.copy() for k, v in db.table_dict.items()}
races, drivers, constructors = T["races"], T["drivers"], T["constructors"]
qual, res = T["qualifying"], T["results"]
for df in (races, qual, res):
    df["date"] = pd.to_datetime(df["date"])
qual = qual.merge(races[["raceId", "year"]], on="raceId", how="left")
res = res.merge(races[["raceId", "year"]], on="raceId", how="left")
qual["position"] = pd.to_numeric(qual["position"], errors="coerce")
res["statusId"] = pd.to_numeric(res["statusId"], errors="coerce")
qual["top3"] = (qual["position"] <= 3).astype(float)
res["nofinish"] = (res["statusId"] != 1).astype(float)  # same definition as the driver-dnf task
dname = (drivers["forename"].astype(str) + " " + drivers["surname"].astype(str)).set_axis(drivers["driverId"]).to_dict()
cname = constructors.set_index("constructorId")["name"].to_dict()
print(f"val_timestamp {dataset.val_timestamp.date()}   test_timestamp {dataset.test_timestamp.date()}")
print(f"qualifying rows {len(qual):,} ({qual['date'].min().date()} .. {qual['date'].max().date()}), "
      f"results rows {len(res):,}")


def history(src, key, value):
    """key -> (sorted dates as int64, cumulative sum of value) for fast window means."""
    out = {}
    for k, g in src.sort_values("date").groupby(key):
        d = g["date"].values.astype("datetime64[ns]").astype(np.int64)
        out[k] = (d, np.concatenate([[0.0], np.cumsum(g[value].values)]))
    return out


def window_mean(hist, k, t0, t1):
    """Mean of value over rows with t0 < date <= t1 (NaN if none)."""
    if k not in hist:
        return np.nan
    d, cs = hist[k]
    i0 = np.searchsorted(d, t0, side="right")
    i1 = np.searchsorted(d, t1, side="right")
    return (cs[i1] - cs[i0]) / (i1 - i0) if i1 > i0 else np.nan


def last_value(src, key, col):
    """key -> (sorted dates, values) to read the last value at or before a time."""
    out = {}
    for k, g in src.sort_values("date").groupby(key):
        out[k] = (g["date"].values.astype("datetime64[ns]").astype(np.int64), g[col].values)
    return out


def at_or_before(lv, k, t):
    if k not in lv:
        return np.nan
    d, v = lv[k]
    i = np.searchsorted(d, t, side="right") - 1
    return v[i] if i >= 0 else np.nan


def first_after(lv, k, t):
    if k not in lv:
        return np.nan
    d, v = lv[k]
    i = np.searchsorted(d, t, side="right")
    return v[i] if i < len(d) else np.nan


def auroc(y, s):
    m = ~np.isnan(s)
    y, s = y[m], s[m]
    if len(np.unique(y)) < 2:
        return np.nan, int(m.sum())
    return roc_auc_score(y, s), int(m.sum())


# ----------------------------------------------------------------------------- per task
for task_name in [t.strip() for t in a.tasks.split(",") if t.strip()]:
    _, task, src = rb_loader.load_dataset_and_task(a.dataset, task_name)
    tabs = {s: task.get_table(s, mask_input_cols=False).df.copy() for s in SPLITS}
    ycol, ecol, tcol = task.target_col, task.entity_col, task.time_col
    for s in SPLITS:
        tabs[s][tcol] = pd.to_datetime(tabs[s][tcol])
    is_top3 = task_name == "driver-top3"
    ev_src = qual if is_top3 else res          # the table that defines the label
    ev_col = "top3" if is_top3 else "nofinish"
    ev_name = "top-3 qualifying" if is_top3 else "not finishing"
    ev_short = "top-3" if is_top3 else "no-finish"

    hr(f"{task_name}  (target '{ycol}', data source {src})")
    print("1. Size of the splits")
    rows = []
    for s in SPLITS:
        df = tabs[s]
        y = df[ycol].astype(int)
        pos_drivers = df.loc[y == 1, ecol].nunique()
        rows.append(dict(split=s, examples=len(df), timestamps=df[tcol].nunique(),
                         first=df[tcol].min().date(), last=df[tcol].max().date(),
                         positives=int(y.sum()), pos_rate=round(y.mean(), 3),
                         drivers=df[ecol].nunique(), drivers_with_a_positive=pos_drivers,
                         examples_per_driver=round(len(df) / df[ecol].nunique(), 1)))
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n2. Which drivers: overlap between the splits")
    dv = {s: set(tabs[s][ecol]) for s in SPLITS}
    te = tabs["test"]
    tp = te[te[ycol].astype(int) == 1]
    print(f"drivers in val {len(dv['val'])}, in test {len(dv['test'])}, in both {len(dv['val'] & dv['test'])}")
    print(f"test examples whose driver is also in val: {te[ecol].isin(dv['val']).mean():.1%}; "
          f"test positives whose driver is also in val: {tp[ecol].isin(dv['val']).mean():.1%}")
    vp = tabs["val"][tabs["val"][ycol].astype(int) == 1]
    print(f"val positives whose driver is also in test: {vp[ecol].isin(dv['test']).mean():.1%}")
    print(f"test drivers never seen in train or val: {len(dv['test'] - dv['train'] - dv['val'])} "
          f"({te[ecol].isin(dv['test'] - dv['train'] - dv['val']).mean():.1%} of the test examples)")

    print(f"\n3. Who the positives are ({ev_name})")
    team_next = last_value(ev_src, "driverId", "constructorId")
    for s in ("val", "test"):
        df = tabs[s].copy()
        df["y"] = df[ycol].astype(int)
        t_ns = df[tcol].values.astype("datetime64[ns]").astype(np.int64)
        df["team"] = [first_after(team_next, d, t) for d, t in zip(df[ecol], t_ns)]
        pos = df[df["y"] == 1]
        by_d = pos[ecol].value_counts()
        by_t = pos["team"].value_counts()
        top_d = ", ".join(f"{dname.get(k, k)} {v}" for k, v in by_d.head(8).items())
        top_t = ", ".join(f"{cname.get(k, k)} {v}" for k, v in by_t.head(6).items())
        print(f"[{s}] {len(pos)} positives from {pos[ecol].nunique()} drivers; "
              f"top 3 drivers {by_d.head(3).sum() / len(pos):.0%}, top 5 {by_d.head(5).sum() / len(pos):.0%}")
        print(f"   drivers: {top_d}")
        print(f"   teams:   {top_t}  (team of the driver's next {'qualifying' if is_top3 else 'race'})")

    print("\n3b. The 6 drivers with most positives in each split, seen in the other split (examples / positives)")
    cnt = {s: tabs[s].assign(y=tabs[s][ycol].astype(int)).groupby(ecol)["y"].agg(["size", "sum"]) for s in ("val", "test")}
    for s, o in (("test", "val"), ("val", "test")):
        top = cnt[s].sort_values("sum", ascending=False).head(6)
        cells = []
        for d, r in top.iterrows():
            ex, po = (int(cnt[o].loc[d, "size"]), int(cnt[o].loc[d, "sum"])) if d in cnt[o].index else (0, 0)
            cells.append(f"{dname.get(d, d)} {int(r['sum'])} in {s} -> {ex}/{po} in {o}")
        print(f"   top of {s}: " + "; ".join(cells))

    print("\n4. How predictable each split is with simple rules (AUROC; computed only from data before each timestamp)")
    print("   rate, 365 d: share of the driver's (or of his last team's) sessions in the 365 days before the timestamp\n"
          f"   that ended in {ev_name}; last qualifying position: lower is better")
    h_drv = history(ev_src, "driverId", ev_col)
    h_team = history(ev_src, "constructorId", ev_col)
    last_team = last_value(ev_src, "driverId", "constructorId")
    last_pos = last_value(qual, "driverId", "position")
    rules = {f"driver {ev_short} rate, 365 d": None,
             f"team {ev_short} rate, 365 d": None}
    if is_top3:
        rules["last qualifying position"] = None
    out_rows, per_year = [], []
    for s in SPLITS:
        df = tabs[s]
        y = df[ycol].astype(int).values
        t_ns = df[tcol].values.astype("datetime64[ns]").astype(np.int64)
        yr = df[tcol].dt.year.values
        y365 = YEAR_NS
        scores = {}
        k = list(rules)
        scores[k[0]] = np.array([window_mean(h_drv, d, t - y365, t) for d, t in zip(df[ecol], t_ns)])
        teams = [at_or_before(last_team, d, t) for d, t in zip(df[ecol], t_ns)]
        scores[k[1]] = np.array([window_mean(h_team, c, t - y365, t) if not pd.isna(c) else np.nan
                                 for c, t in zip(teams, t_ns)])
        if is_top3:
            scores[k[2]] = -np.array([at_or_before(last_pos, d, t) for d, t in zip(df[ecol], t_ns)], dtype=float)
        for name, sc in scores.items():
            au, n = auroc(y, sc)
            au_all, _ = auroc(y, np.where(np.isnan(sc), np.nanmin(sc) - 1, sc))  # no history -> lowest score
            out_rows.append(dict(rule=name, split=s, auroc=round(au, 3), auroc_all=round(au_all, 3), scored=n, of=len(y)))
            if s in ("val", "test"):
                for yy in sorted(set(yr)):
                    m = yr == yy
                    au_y, n_y = auroc(y[m], sc[m])
                    per_year.append(dict(rule=name, split=s, year=yy, auroc=round(au_y, 3),
                                         examples=int(m.sum()), positives=int(y[m].sum())))
    print(pd.DataFrame(out_rows).pivot(index="rule", columns="split", values="auroc")[list(SPLITS)].to_string())
    print("(rows without any history get no score and are left out; counts below. auroc_all: all rows, no history = lowest score)")
    print(pd.DataFrame(out_rows)[["rule", "split", "auroc", "auroc_all", "scored", "of"]].to_string(index=False))
    print("\n   per year of the timestamp, AUROC (examples/positives):")
    py = pd.DataFrame(per_year)
    for rule in py["rule"].unique():
        for s in ("val", "test"):
            g = py[(py["rule"] == rule) & (py["split"] == s)]
            cells = "  ".join(f"{r.year} {r.auroc:.2f} ({r.examples}/{r.positives})" for r in g.itertuples())
            print(f"   {rule:26s} {s:4s} {cells}")

# ----------------------------------------------------------------------------- seasons
hr("5. How Formula 1 changed per season (from the database)")
qs = qual.groupby("raceId").agg(year=("year", "first"), cars=("driverId", "nunique"))
season = qs.groupby("year").agg(races_with_qualifying=("cars", "size"), mean_cars_in_qualifying=("cars", "mean"))
season["teams"] = qual.groupby("year")["constructorId"].nunique()
season["drivers"] = qual.groupby("year")["driverId"].nunique()
t3 = qual[qual["position"] <= 3]
season["drivers_in_top3"] = t3.groupby("year")["driverId"].nunique()
team_share = t3.groupby(["year", "constructorId"]).size().groupby(level=0).apply(lambda s: s.max() / s.sum())
season["top_team_share_of_top3"] = team_share.round(2)
season["top_team"] = t3.groupby(["year", "constructorId"]).size().groupby(level=0).idxmax().map(lambda x: cname.get(x[1], x[1]))
season["finished_share"] = (1 - res.groupby("year")["nofinish"].mean()).round(2)
season["mean_cars_in_qualifying"] = season["mean_cars_in_qualifying"].round(1)
print(season.loc[(season.index >= 1998) & (season.index <= 2016)].to_string())
print("\nsplits: train < 2005-01-01 <= val < 2010-01-01 <= test (labels look 30 days ahead of each timestamp)")
