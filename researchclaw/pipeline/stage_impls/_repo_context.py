"""Estrae estratti di codice dalle repo di riferimento clonate nello Stage 5,
da iniettare nel prompt di generazione codice (Stage 10)."""

from __future__ import annotations

from pathlib import Path

_SKIP_DIRS = {
    "tests", "test", "docs", "doc", "examples", "node_modules",
    "venv", "build", "dist", "data", "datasets", "figures", "notebooks",
}
_SKIP_FILES = {"setup.py", "__init__.py", "conftest.py"}
# Parole nel nome file che indicano codice utile (peso decrescente)
_PREFER = (("dropout", 4), ("mlp", 3), ("model", 2), ("net", 2), ("layer", 2),
           ("train", 1), ("main", 1))


def _score(name: str) -> int:
    n = name.lower()
    return sum(w for key, w in _PREFER if key in n)


def repo_source_excerpts(
    local_dir: Path,
    max_files: int = 3,
    max_chars_per_file: int = 2500,
    max_total_chars: int = 7000,
) -> str:
    """Restituisce un blocco di testo con i file .py piu' rilevanti della repo."""
    local_dir = Path(local_dir)
    if not local_dir.is_dir():
        return ""

    candidates = []
    for p in local_dir.rglob("*.py"):
        rel = p.relative_to(local_dir)
        if any(part.startswith(".") or part in _SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if p.name in _SKIP_FILES or p.name.startswith("test_"):
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size < 200 or size > 200_000:
            continue
        candidates.append((-_score(p.name), size, str(rel), p))

    candidates.sort(key=lambda t: (t[0], t[1]))

    out: list[str] = []
    used = 0
    for _, _, rel, p in candidates[:max_files]:
        if used >= max_total_chars:
            break
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        budget = min(max_chars_per_file, max_total_chars - used)
        snippet = text[:budget].rstrip()
        truncated = " (truncated)" if len(text) > budget else ""
        out.append(f"\n  Key source file `{rel}`{truncated}:\n```python\n{snippet}\n```")
        used += len(snippet)

    result = "".join(out)

    # Debug: salva cio' che viene iniettato nel prompt, accanto alla repo clonata
    try:
        (local_dir.parent / f"_excerpt_{local_dir.name}.txt").write_text(
            result or "(nessun file selezionato)", encoding="utf-8"
        )
    except OSError:
        pass

    return result