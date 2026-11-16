#!/usr/bin/env python3
"""Tokens and cost so far, from the usage log of a run (llm_usage_<date>_<llm>.jsonl).

    python3 rb_task/tools/llm_usage_summary.py llm_usage_20261116-101500_gemini.jsonl [--price 2,12]

Can be run while the run is going. Output tokens = total - prompt, so the
reasoning tokens that Gemini bills as output are included even when the
API does not list them under completion_tokens.
"""
import argparse
import json
import time

ap = argparse.ArgumentParser()
ap.add_argument("log")
ap.add_argument("--price", default="2,12", help="IN,OUT in USD per 1M tokens (default Gemini 3.1 Pro: 2,12)")
a = ap.parse_args()
pin, pout = map(float, a.price.split(","))

n = p = c = o = 0
t0 = t1 = None
for line in open(a.log, encoding="utf-8"):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    u = r.get("usage") or {}
    pt = int(u.get("prompt_tokens", 0) or 0)
    ct = int(u.get("completion_tokens", 0) or 0)
    tt = int(u.get("total_tokens", 0) or 0)
    n += 1
    p += pt
    c += ct
    o += max(tt - pt, ct)
    t0 = r["t"] if t0 is None else t0
    t1 = r["t"]

cost = p / 1e6 * pin + o / 1e6 * pout
hours = (t1 - t0) / 3600 if n > 1 else 0
print(f"calls: {n}   prompt: {p / 1e6:.2f} M   output: {o / 1e6:.2f} M (completion {c / 1e6:.2f} M + reasoning)")
print(f"cost so far: {cost:.2f} $  (prices {pin}/{pout} $ per 1M)")
if hours >= 0.25:  # a rate over less than 15 minutes is meaningless
    print(f"over {hours:.2f} h since the first call: {cost / hours:.2f} $/h "
          f"-> about {cost / hours * 3:.2f} $ for 3 h at this rate")
print(f"last call: {time.strftime('%H:%M:%S', time.localtime(t1)) if t1 else '-'}")
