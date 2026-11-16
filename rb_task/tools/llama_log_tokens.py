#!/usr/bin/env python3
"""Tokens used by a local run, from the llama-server log.

    python3 rb_task/tools/llama_log_tokens.py llama-server.log [--attempts N]

For every request the log has: tokens generated ("eval time ... / N tokens"),
prompt tokens actually computed ("prompt eval time ... / N tokens", without the
part reused from the cache) and the total context at the end ("n_tokens = T").
The full prompt, which an API would bill, is T - generated + 1.
Prices are USD per million tokens (input, output); change them with --price.
"""
import argparse
import re
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("log")
ap.add_argument("--attempts", type=int, default=0, help="refinement attempts of the run (for per-attempt numbers)")
ap.add_argument("--price", action="append", default=[],
                help="NAME=IN,OUT in USD per 1M tokens (default: gemini-3.1-pro=2,12 and gemini-3.8-flash=0.75,3.75)")
a = ap.parse_args()
prices = {"gemini-3.1-pro": (2.0, 12.0), "gemini-3.8-flash": (0.75, 3.75)}
for p in a.price:
    n, v = p.split("=")
    i, o = v.split(",")
    prices[n] = (float(i), float(o))

ts_re = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+) ")
task_re = re.compile(r"task (\d+) \|")
pe_re = re.compile(r"prompt eval time =\s*([\d.]+) ms /\s*(\d+) tokens")
ev_re = re.compile(r"(?<!prompt )eval time =\s*([\d.]+) ms /\s*(\d+) tokens")
rel_re = re.compile(r"release:.*n_tokens = (\d+)")

tasks = defaultdict(dict)
first = last = None
with open(a.log, encoding="utf-8", errors="replace") as f:
    for line in f:
        m = ts_re.match(line)
        if m:
            mi, s, ms, us = map(int, m.groups())
            t = mi * 60 + s + ms / 1e3 + us / 1e6
            first = t if first is None else first
            last = t
        tm = task_re.search(line)
        if not tm:
            continue
        d = tasks[int(tm.group(1))]
        if (m2 := pe_re.search(line)):
            d["pe_ms"], d["pe_tok"] = float(m2.group(1)), int(m2.group(2))
        elif (m2 := ev_re.search(line)):
            d["ev_ms"], d["ev_tok"] = float(m2.group(1)), int(m2.group(2))
        elif (m2 := rel_re.search(line)):
            d["n_tokens"] = int(m2.group(1))

done = [d for d in tasks.values() if "ev_tok" in d and "n_tokens" in d]
gen = sum(d["ev_tok"] for d in done)
full_prompt = sum(max(d["n_tokens"] - d["ev_tok"] + 1, d.get("pe_tok", 0)) for d in done)
new_prompt = sum(d.get("pe_tok", 0) for d in done)
llm_sec = sum(d.get("pe_ms", 0) + d.get("ev_ms", 0) for d in done) / 1e3
hours = (last - first) / 3600 if first is not None else 0
M = 1e6

print(f"requests completed:        {len(done)}  (in the log: {len(tasks)})")
print(f"span of the log:           {hours:.2f} h;  time spent in LLM calls: {llm_sec / 3600:.2f} h")
print(f"prompt tokens (full):      {full_prompt / M:.2f} M   (computed, rest from cache: {new_prompt / M:.2f} M)")
print(f"generated tokens:          {gen / M:.2f} M   (incl. reasoning)")
if done:
    print(f"per request (mean / max):  prompt {full_prompt / len(done):,.0f} / "
          f"{max(d['n_tokens'] - d['ev_tok'] + 1 for d in done):,}   "
          f"generated {gen / len(done):,.0f} / {max(d['ev_tok'] for d in done):,}")
if hours:
    print(f"per hour of run:           prompt {full_prompt / hours / M:.2f} M, generated {gen / hours / M:.2f} M")
if a.attempts:
    print(f"per attempt ({a.attempts}):         prompt {full_prompt / a.attempts:,.0f}, generated {gen / a.attempts:,.0f}, "
          f"requests {len(done) / a.attempts:.1f}")
print("\nCost of the same tokens at API prices (USD; tokenizers differ, so take it as an order of magnitude):")
for name, (pi, po) in prices.items():
    tot = full_prompt / M * pi + gen / M * po
    line = f"  {name:18s} {tot:8.2f} $ for the whole log"
    if hours:
        line += f",  {tot / hours:6.2f} $ per hour"
    if a.attempts:
        line += f",  {tot / a.attempts:6.3f} $ per attempt"
    print(line)
