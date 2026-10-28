"""Ripara i YAML 'quasi validi' prodotti dall'LLM per il blueprint del CodeAgent.

Errori tipici visti nelle run con Qwen:
  - annotazioni dopo una lista:   input_shape: [B, C, H, W] (e.g., [64, 1, 28, 28])
  - valori con ': ' non quotati:  signature: (config: X) -> (a, b)
  - voci di lista con backtick:   - Time budget guard (`time.monotonic()`) exists
"""

from __future__ import annotations

import re

import yaml


def _q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', "'") + '"'


def sanitize_blueprint_yaml(text: str) -> str:
    out = []
    for line in text.splitlines():
        m = re.match(r"^(\s*(?:- )?[\w.\-]+:\s*\[[^\]]*\])\s+\(.*\)\s*$", line)
        if m:
            line = m.group(1)

        m = re.match(r"^(\s*(?:- )?)([\w.\-]+):\s+(.+?)\s*$", line)
        if m:
            ind, key, val = m.groups()
            if val[0] not in "\"'[{|>&*!%@`" and (
                ": " in val or val.startswith("(") or " #" in val or "`" in val
            ):
                line = f"{ind}{key}: {_q(val)}"
            elif val[0] == "`":
                line = f"{ind}{key}: {_q(val)}"
        else:
            m = re.match(r"^(\s*)- (.+?)\s*$", line)
            if m:
                ind, val = m.groups()
                is_kv = re.match(r"^[\w.\-]+:(\s|$)", val)
                if (
                    not is_kv
                    and val[0] not in "\"'[{|>&*!%@"
                    and (": " in val or "`" in val or " #" in val or val.startswith("("))
                ):
                    line = f"{ind}- {_q(val)}"
        out.append(line)
    return "\n".join(out)


def safe_load_blueprint(text: str):
    """yaml.safe_load con un secondo tentativo dopo la sanificazione.
    Solleva yaml.YAMLError come l'originale se anche il secondo tentativo fallisce."""
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return yaml.safe_load(sanitize_blueprint_yaml(text))


def extra_candidates(*texts: str) -> list[str]:
    """Versioni sanificate dei testi dati (senza duplicati e senza gli originali),
    da provare DOPO i tentativi gia' presenti in _parse_blueprint."""
    seen = set(texts)
    out: list[str] = []
    for t in texts:
        try:
            s = sanitize_blueprint_yaml(t)
        except Exception:  # noqa: BLE001
            continue
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out
