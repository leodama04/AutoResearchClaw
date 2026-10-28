#!/usr/bin/env python3
"""Aggiunge tentativi di parsing extra a CodeAgent._parse_blueprint
(researchclaw/pipeline/code_agent.py).

Uso (dalla root del repo, con _blueprint_yaml_fix.py accanto a questo script):
    python3 apply_blueprint_yaml_patch.py
Idempotente; crea un backup code_agent.py.bak.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(".").resolve()
TARGET = ROOT / "researchclaw/pipeline/code_agent.py"
HELPER_SRC = Path(__file__).with_name("_blueprint_yaml_fix.py")
HELPER_DST = ROOT / "researchclaw/pipeline/_blueprint_yaml_fix.py"

ANCHOR = "        for attempt_text in (sanitized, yaml_text):\n"
NEW = '''        # ARC patch: tentativi extra con sanificatore piu' tollerante
        try:
            from researchclaw.pipeline._blueprint_yaml_fix import (
                extra_candidates as _arc_extra,
            )

            _arc_cands = _arc_extra(sanitized, yaml_text)
        except Exception:  # noqa: BLE001
            _arc_cands = []
        for attempt_text in (sanitized, yaml_text, *_arc_cands):
'''


def main() -> int:
    if not TARGET.is_file():
        print(f"ERRORE: non trovo {TARGET}. Lancialo dalla root del repo.", file=sys.stderr)
        return 1
    if not HELPER_SRC.is_file():
        print(f"ERRORE: manca {HELPER_SRC} accanto a questo script.", file=sys.stderr)
        return 1
    src = TARGET.read_text(encoding="utf-8")
    if "_arc_extra" in src:
        print("Patch gia' applicata.")
    else:
        if src.count(ANCHOR) != 1:
            print(f"ERRORE: attesa 1 occorrenza dell'ancora, trovate {src.count(ANCHOR)}. "
                  "Non modifico nulla.", file=sys.stderr)
            return 1
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak"))
        TARGET.write_text(src.replace(ANCHOR, NEW), encoding="utf-8")
        print(f"Patch applicata a {TARGET} (backup: .py.bak)")
    shutil.copy2(HELPER_SRC, HELPER_DST)
    print(f"Helper copiato in {HELPER_DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
