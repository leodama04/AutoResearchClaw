"""Riparazione automatica dello Stage 12 (EXPERIMENT_RUN).

Se l'esperimento crasha senza produrre metriche, passa traceback + codice all'LLM,
applica le correzioni (blocchi SEARCH/REPLACE) su una COPIA del progetto e riesegue.
Si ripete fino a ARC_STAGE12_REPAIRS volte (default 3).

Non tocca la guardia anti-risultati-inventati: se dopo le riparazioni non ci sono
metriche reali, lo stage fallisce come prima.
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

_EDIT_RE = re.compile(
    r"<<<<<<<[ \t]*SEARCH[ \t]+(?P<file>\S+)[ \t]*\r?\n"
    r"(?P<old>.*?)\r?\n=======[ \t]*\r?\n"
    r"(?P<new>.*?)\r?\n?>>>>>>>[ \t]*REPLACE",
    re.DOTALL,
)
_TB_RE = re.compile(r'File "([^"]+)", line (\d+)')
_MAX_CODE_CHARS = 50_000


# ---------------------------------------------------------------- utilita'
def parse_edits(text: str) -> list[tuple[str, str, str]]:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    return [(m["file"], m["old"], m["new"]) for m in _EDIT_RE.finditer(text)]


def apply_one(text: str, old: str, new: str) -> str | None:
    """Sostituisce `old` con `new` solo se la corrispondenza e' univoca."""
    if not old.strip():
        return None
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        return None
    # tentativo tollerante: ignora spazi a fine riga
    t_lines = text.split("\n")
    o_lines = [ln.rstrip() for ln in old.split("\n")]
    k = len(o_lines)
    hits = [
        i
        for i in range(len(t_lines) - k + 1)
        if [ln.rstrip() for ln in t_lines[i : i + k]] == o_lines
    ]
    if len(hits) != 1:
        return None
    i = hits[0]
    return "\n".join(t_lines[:i] + new.split("\n") + t_lines[i + k :])


def apply_edits(work: Path, edits: list[tuple[str, str, str]]) -> int:
    """Applica le modifiche ai file esistenti; ripristina un file se diventa non valido."""
    applied = 0
    for fname, old, new in edits:
        target = work / Path(fname).name
        if not target.is_file():
            cands = [p for p in work.rglob(Path(fname).name) if p.is_file()]
            if len(cands) != 1:
                continue
            target = cands[0]
        original = target.read_text(encoding="utf-8", errors="replace")
        updated = apply_one(original, old, new)
        if updated is None:
            continue
        if target.suffix == ".py":
            try:
                ast.parse(updated)
            except SyntaxError:
                continue
        target.write_text(updated, encoding="utf-8")
        applied += 1
    return applied


def _has_metrics(result: Any, parse_metrics: Callable[[str], dict]) -> bool:
    if getattr(result, "metrics", None):
        return True
    out = getattr(result, "stdout", "") or ""
    try:
        return bool(parse_metrics(out)) if out else False
    except Exception:  # noqa: BLE001
        return False


def _clean_tail(text: str, limit: int) -> str:
    lines = [ln for ln in (text or "").splitlines() if "%|" not in ln]
    return "\n".join(lines)[-limit:]


def _error_text(result: Any) -> str:
    rc = getattr(result, "returncode", None)
    stderr = _clean_tail(getattr(result, "stderr", "") or "", 4000)
    stdout = _clean_tail(getattr(result, "stdout", "") or "", 1500)
    if rc not in (0, None) or "Traceback" in stderr:
        return f"Exit code: {rc}\n--- STDERR (tail) ---\n{stderr}\n--- STDOUT (tail) ---\n{stdout}"
    elapsed = getattr(result, "elapsed_sec", None)
    return (
        f"The program exited with code {rc} after {elapsed}s but printed NO metrics.\n"
        f"Typical causes: missing `if __name__ == \"__main__\":` entry point, main() never "
        f"called, or metrics not reported via the harness.\n--- STDOUT (tail) ---\n{stdout}\n"
        f"--- STDERR (tail) ---\n{stderr}"
    )


def _read_sources(work: Path) -> str:
    files = sorted(  # vendored official code (read-only, possibly 100k+ characters) is not shown
        (p for p in work.rglob("*.py") if "__pycache__" not in p.parts and not p.name.startswith("vendor_")),
        key=lambda p: (p.name != "main.py", p.name),
    )
    parts, used = [], 0
    for p in files:
        body = p.read_text(encoding="utf-8", errors="replace")
        if used + len(body) > _MAX_CODE_CHARS:
            body = body[: max(0, _MAX_CODE_CHARS - used)] + "\n# ... (truncated)"
        parts.append(f"### FILE: {p.name}\n```python\n{body}\n```")
        used += len(body)
        if used >= _MAX_CODE_CHARS:
            break
    return "\n\n".join(parts)


def _failing_snippets(work: Path, err: str) -> str:
    out = []
    for path, line in _TB_RE.findall(err):
        p = work / Path(path).name
        if not p.is_file():
            continue
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        ln = int(line)
        lo, hi = max(1, ln - 8), min(len(lines), ln + 8)
        block = "\n".join(f"{i:5d}: {lines[i - 1]}" for i in range(lo, hi + 1))
        out.append(f"{p.name} around line {ln}:\n{block}")
    return "\n\n".join(out[-3:])


def _harness_source(stage_dir: Path) -> str:
    for p in stage_dir.glob("runs/sandbox/_project*/experiment_harness.py"):
        try:
            return p.read_text(encoding="utf-8", errors="replace")[:6000]
        except OSError:
            continue
    return ""


def _task_spec_suffix() -> str:
    """Optional task specification (env ARC_TASK_SPEC_FILE) appended to the repair prompt."""
    path = os.environ.get("ARC_TASK_SPEC_FILE", "").strip()
    if not path:
        return ""
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return f"\n\n=== TASK SPECIFICATION (authoritative) ===\n{text}" if text else ""


def _build_prompt(work: Path, err: str, stage_dir: Path, budget_sec: int) -> str:
    harness = _harness_source(stage_dir)
    return (
        "A Python research experiment crashed (or printed no metrics) when run in a sandbox.\n"
        "Fix ONLY what is needed to make it run to completion and report metrics. Keep the "
        "scientific design (conditions, hyperparameters being compared) unchanged.\n\n"
        "Hard rules:\n"
        "- Use only methods that really exist (check the harness source below; do not invent "
        "harness methods).\n"
        "- Do NOT pass lambdas or local functions to multiprocessing; prefer plain sequential "
        "loops (multiprocessing and CUDA do not mix well here).\n"
        f"- The whole run must finish well within {budget_sec} seconds. If the workload is far "
        "too large (e.g. hundreds of trials), reduce seeds/epochs/datasets so it fits in about "
        f"{budget_sec // 2} seconds, and stop gracefully via harness.should_stop() when it "
        "exists.\n"
        "- The program must have an entry point (`if __name__ == \"__main__\":`) that runs "
        "everything and reports metrics through the harness / prints them.\n\n"
        f"=== ERROR ===\n{err}\n\n"
        f"=== FAILING LOCATIONS ===\n{_failing_snippets(work, err) or '(not available)'}\n\n"
        f"=== HARNESS SOURCE (experiment_harness.py) ===\n{harness or '(not available)'}\n\n"
        f"=== PROJECT FILES ===\n{_read_sources(work)}\n\n"
        "Reply with ONLY edit blocks, no explanations, in exactly this format (the SEARCH text "
        "must match the existing file contents exactly and be unique in that file):\n\n"
        "<<<<<<< SEARCH main.py\n"
        "old lines\n"
        "=======\n"
        "new lines\n"
        ">>>>>>> REPLACE\n\n"
        "You may output several blocks, for several files."
        + _task_spec_suffix()
    )


# --------------------------------------------------------------- ciclo
def repair_loop(
    *,
    sandbox: Any,
    result: Any,
    exp_dir: Any,
    stage_dir: Path,
    llm: Any,
    timeout_sec: int,
    parse_metrics: Callable[[str], dict],
    max_repairs: int | None = None,
) -> Any:
    if max_repairs is None:
        try:
            max_repairs = int(os.environ.get("ARC_STAGE12_REPAIRS", "3"))
        except ValueError:
            max_repairs = 3
    if max_repairs <= 0 or llm is None or not exp_dir or not Path(exp_dir).is_dir():
        return result
    if _has_metrics(result, parse_metrics):
        return result

    src = Path(exp_dir)
    work = Path(stage_dir) / "experiment_repaired"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(src, work, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    log: list[dict[str, Any]] = []
    for attempt in range(1, max_repairs + 1):
        if _has_metrics(result, parse_metrics):
            break
        if getattr(result, "timed_out", False):
            log.append({"attempt": attempt, "note": "timeout senza metriche: nessuna riparazione"})
            break
        if "GPU_UNAVAILABLE" in (getattr(result, "stdout", "") or ""):
            # the GPU was full (other processes): an environment problem, not a bug - do not let the LLM edit the code
            logger.warning("Stage 12: GPU occupied by other processes - no code repair (see GPU_UNAVAILABLE in stdout)")
            log.append({"attempt": attempt, "note": "GPU_UNAVAILABLE: GPU occupata da altri processi, nessuna riparazione"})
            break
        err = _error_text(result)
        prompt = _build_prompt(work, err, Path(stage_dir), int(timeout_sec))
        logger.warning("Stage 12 auto-repair: attempt %d/%d", attempt, max_repairs)
        reply = llm.chat([{"role": "user", "content": prompt}], max_tokens=8192)
        text = getattr(reply, "content", None) or str(reply)
        edits = parse_edits(text)
        applied = apply_edits(work, edits)
        log.append(
            {
                "attempt": attempt,
                "error_tail": err[-800:],
                "edits_proposed": len(edits),
                "edits_applied": applied,
            }
        )
        if applied == 0:
            logger.warning("Stage 12 auto-repair: nessuna modifica applicabile, mi fermo")
            break
        result = sandbox.run_project(work, timeout_sec=timeout_sec)

    ok = _has_metrics(result, parse_metrics)
    try:
        (Path(stage_dir) / "stage12_repairs.json").write_text(
            json.dumps({"success": ok, "attempts": log}, indent=2), encoding="utf-8"
        )
    except OSError:
        pass

    if ok and log:
        # allinea i file dello Stage 10 al codice riparato (originale salvato a parte)
        try:
            backup = Path(stage_dir) / "experiment_before_repair"
            if backup.exists():
                shutil.rmtree(backup)
            shutil.copytree(src, backup, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            for p in work.rglob("*.py"):
                dest = src / p.relative_to(work)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
        except OSError as exc:
            logger.warning("Stage 12 auto-repair: copia sul progetto originale fallita: %s", exc)
        logger.warning("Stage 12 auto-repair: SUCCESSO dopo %d tentativo/i", len(log))
    return result
