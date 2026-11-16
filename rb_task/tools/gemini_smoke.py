#!/usr/bin/env python3
"""Check the Gemini setup before a run: key, model name, parameters, token usage.

Used by:  ./run.sh gemini-test      (inside the container, no GPU, no llama-server)

It uses the same client as the pipeline, with the Gemini config, and makes:
  0. a list of the Gemini models visible with this key;
  1. a plain call (like most stages);
  2. a call in JSON mode (like the stages that parse JSON);
and prints answer, finish reason, token usage and time of each call.
The two calls cost a fraction of a cent.
"""
import json
import os
import sys
import time
import urllib.request

import yaml

from researchclaw.llm.client import create_client_from_yaml

cfg_path = sys.argv[1] if len(sys.argv) > 1 else "/app/config.arc.relbench.code.gemini.yaml"
with open(cfg_path, encoding="utf-8") as f:
    llm = yaml.safe_load(f)["llm"]
key = os.environ.get(llm.get("api_key_env", "GEMINI_API_KEY"), "")
if not key:
    sys.exit("ERROR: GEMINI_API_KEY is empty inside the container.")
base = llm["base_url"].rstrip("/") + "/"
model = llm["primary_model"]
print(f"config: {cfg_path}\nendpoint: {base}\nmodel in config: {model}\n")

# 0. models visible with this key
try:
    req = urllib.request.Request(base + "models", headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ids = sorted(m.get("id", "") for m in json.loads(r.read()).get("data", []))
    gem = [i for i in ids if "gemini" in i and ("pro" in i or "flash" in i)]
    print("Gemini Pro/Flash models visible with this key:")
    for i in gem:
        print("  ", i, "  <-- in config" if i.split("/")[-1] == model else "")
    if not any(i.split("/")[-1] == model for i in gem):
        print(f"WARNING: '{model}' is not in the list: check primary_model in {cfg_path}")
    print()
except Exception as e:  # noqa: BLE001
    print(f"(could not list the models: {e})\n")

client = create_client_from_yaml(cfg_path)
client.config.timeout_sec = 600
ok = True
for name, kwargs, check in [
    ("plain", dict(messages=[{"role": "user", "content": "Reply with exactly: OK"}], max_tokens=4096), None),
    ("json", dict(messages=[{"role": "user", "content": 'Return a JSON object with the key "ok" set to true.'}],
                  max_tokens=4096, json_mode=True), "json"),
]:
    t0 = time.time()
    try:
        resp = client.chat(**kwargs)
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"[{name}] FAILED after {time.time() - t0:.1f}s: {e}\n")
        continue
    usage = resp.raw.get("usage", {})
    print(f"[{name}] {time.time() - t0:.1f}s  finish={resp.finish_reason!r}")
    print(f"   answer: {resp.content.strip()[:200]!r}")
    print(f"   usage:  {json.dumps(usage)}")
    if check == "json":
        txt = resp.content.strip().strip("`")
        txt = txt[txt.find("{"): txt.rfind("}") + 1]
        try:
            json.loads(txt)
            print("   JSON: parsed")
        except Exception:  # noqa: BLE001
            ok = False
            print("   JSON: NOT parsed")
    print()

print("RESULT:", "OK, ready for the run" if ok else "something failed: send me this output")
sys.exit(0 if ok else 1)
