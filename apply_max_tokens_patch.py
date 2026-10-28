#!/usr/bin/env python3
"""Aggiunge a researchclaw/llm/client.py un moltiplicatore del limite di token in uscita,
controllato da variabili d'ambiente (utile quando Qwen ha il thinking acceso e
il ragionamento consuma parte del budget di ogni chiamata).

  ARC_MAX_TOKENS_MULT   moltiplicatore (default 1 = nessun effetto), es. 3
  ARC_MAX_TOKENS_CAP    tetto massimo assoluto (default 32768)

Uso (dalla root del repo):  python3 apply_max_tokens_patch.py
Idempotente; crea un backup client.py.bak.
"""
import re
import shutil
import sys
from pathlib import Path

TARGET = Path("researchclaw/llm/client.py")
PATTERN = re.compile(
    r"^(?P<ind>[ \t]*)max_tok = max_tokens or self\.config\.max_tokens[ \t]*$",
    re.MULTILINE,
)
MARK = "ARC_MAX_TOKENS_MULT"


def main() -> int:
    if not TARGET.is_file():
        print(f"ERRORE: non trovo {TARGET}. Lancialo dalla root del repo.", file=sys.stderr)
        return 1
    src = TARGET.read_text(encoding="utf-8")
    if MARK in src:
        print("Patch gia' applicata, niente da fare.")
        return 0
    matches = PATTERN.findall(src)
    if len(matches) != 1:
        print(
            f"ERRORE: attese 1 occorrenza della riga 'max_tok = max_tokens or self.config.max_tokens', "
            f"trovate {len(matches)}. Non modifico nulla.",
            file=sys.stderr,
        )
        return 1

    def repl(m: "re.Match[str]") -> str:
        i = m.group("ind")
        return (
            f"{i}max_tok = max_tokens or self.config.max_tokens\n"
            f"{i}try:  # ARC_MAX_TOKENS_MULT patch\n"
            f"{i}    import os as _os\n"
            f"{i}    _mult = float(_os.environ.get(\"ARC_MAX_TOKENS_MULT\", \"1\"))\n"
            f"{i}    if _mult > 1:\n"
            f"{i}        _cap = int(_os.environ.get(\"ARC_MAX_TOKENS_CAP\", \"32768\"))\n"
            f"{i}        max_tok = int(min(max_tok * _mult, max(_cap, max_tok)))\n"
            f"{i}except ValueError:\n"
            f"{i}    pass"
        )

    shutil.copy2(TARGET, TARGET.with_suffix(".py.bak"))
    TARGET.write_text(PATTERN.sub(repl, src, count=1), encoding="utf-8")
    print(f"Patch applicata a {TARGET} (backup: client.py.bak)")
    return 0


if __name__ == "__main__":
    sys.exit(main())