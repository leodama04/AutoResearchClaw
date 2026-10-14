"""Helpers for the stage-13 (ITERATIVE_REFINE) patches.

* hide_test(summary): removes test-split metrics from a run summary before it is
  shown to the LLM, so that refinement cannot (even implicitly) optimise on test.
* history_line(...): compact record of a refinement attempt (what changed, the
  validation metric, whether it helped) appended to the prompt context so the LLM
  can learn from earlier attempts.

Enabled by env ARC_HIDE_TEST_METRICS=1 (hide_test) -- history_line is always on.
"""

from __future__ import annotations

import difflib
import os
import re
from typing import Any

_TEST_TOKEN = re.compile(r"\btest\w*=\S+")
_TEST_METRIC_LINE = re.compile(r"^\s*\S*test\S*\s*:\s*[-+0-9.eE]+\s*$", re.IGNORECASE)


def _enabled() -> bool:
    return os.environ.get("ARC_HIDE_TEST_METRICS", "").strip() in ("1", "true", "yes")


def _drop_test_keys(d: Any) -> Any:
    if isinstance(d, dict):
        return {k: _drop_test_keys(v) for k, v in d.items() if "test" not in str(k).lower()}
    if isinstance(d, list):
        return [_drop_test_keys(v) for v in d]
    return d


def _clean_text(text: str) -> str:
    out = []
    for line in text.splitlines():
        if _TEST_METRIC_LINE.match(line):
            continue
        out.append(_TEST_TOKEN.sub("", line).rstrip())
    return "\n".join(out)


def hide_test(summary: dict) -> dict:
    """Return a copy of a stage-12 run payload without test-split information."""
    if not _enabled():
        return summary
    s = dict(summary)
    for key in ("metrics", "key_metrics", "structured_results"):
        if key in s:
            s[key] = _drop_test_keys(s[key])
    for key in ("stdout", "stderr"):
        if isinstance(s.get(key), str):
            s[key] = _clean_text(s[key])
    return s


def _diff(prev: dict[str, str], new: dict[str, str], limit: int = 1800) -> tuple[list[str], str]:
    changed, chunks = [], []
    for name in sorted(set(prev) | set(new)):
        a, b = prev.get(name, ""), new.get(name, "")
        if a == b:
            continue
        changed.append(name)
        d = difflib.unified_diff(
            a.splitlines(), b.splitlines(), f"a/{name}", f"b/{name}", n=0, lineterm=""
        )
        chunks.append("\n".join(list(d)[:60]))
    text = "\n".join(chunks)
    if len(text) > limit:
        text = text[:limit] + "\n... (diff truncated)"
    return changed, text


_ERR_LINE = re.compile(r"(Error|Exception|Traceback|error:|File \"[^\"]*experiment|line \d+, in )")


def error_excerpt(iter_record: dict, limit: int = 900) -> str:
    """The traceback of the failed run (warnings removed): what the LLM needs to fix its code."""
    texts = []
    for key in ("sandbox_after_fix", "sandbox"):
        sb = iter_record.get(key) or {}
        if sb.get("stderr"):
            texts.append(sb["stderr"])
    for text in texts:
        lines = [l for l in text.splitlines() if l.strip() and "Warning" not in l and "warnings.warn" not in l]
        keep = [l for l in lines if _ERR_LINE.search(l)]
        if keep:
            return "\n".join(keep[-8:])[-limit:]
        if lines:
            return "\n".join(lines[-6:])[-limit:]
    return ""


def history_line(
    iteration: int,
    iter_record: dict,
    prev_files: dict[str, str],
    new_files: dict[str, str],
    best_metric: float | None,
) -> str:
    changed, diff = _diff(prev_files, new_files)
    metric = iter_record.get("metric")
    sandbox = iter_record.get("sandbox") or {}
    lines = [f"REFINEMENT HISTORY - attempt {iteration} (your earlier modification, already evaluated):"]
    lines.append(f"  files changed: {', '.join(changed) or '(none)'}")
    if iter_record.get("arc_overrides") is not None:
        lines.append(f"  configuration overrides: {json.dumps(iter_record['arc_overrides'], sort_keys=True)}")
    if iter_record.get("arc_rejected"):
        lines.append(f"  REJECTED (not a valid evaluation): {iter_record['arc_rejected']}")
    if "arc_official_code" in iter_record:
        oc = iter_record["arc_official_code"]
        lines.append(f"  official code imported: {', '.join(oc) if oc else 'NONE (re-implemented from scratch)'}")
    discarded = [n for n in iter_record.get("arc_guard_notes", []) if "restored" in n or "dropped" in n or "removed" in n]
    if discarded:
        lines.append(f"  DISCARDED by the guard (did not reach the model): {'; '.join(discarded)[:300]}")
    if metric is None and "GPU_UNAVAILABLE" in str(sandbox.get("stdout") or ""):
        lines.append("  RESULT: NOT EVALUATED - the GPU was occupied by other processes (environment problem, "
                     "not caused by your change). You may retry the same idea.")
    elif metric is None:
        err = error_excerpt(iter_record)
        lines.append(
            "  RESULT: no primary_metric produced"
            + (f" (returncode={sandbox.get('returncode')}). stderr tail: {err}" if err else "")
        )
    else:
        verdict = "IMPROVED -> new best" if iter_record.get("improved") else "did NOT improve"
        lines.append(f"  RESULT: primary_metric={metric:.4f} ({verdict}; best so far={best_metric})")
        extras = [
            f"{k}={v:.4f}"
            for k, v in (sandbox.get("metrics") or {}).items()
            if isinstance(v, (int, float))
            and "test" not in k.lower()
            and "val" in k.lower()
            and k.endswith("_mean")
        ][:8]
        if extras:
            lines.append("  validation means: " + ", ".join(extras))
    if diff:
        lines.append("  change (unified diff):\n" + diff)
    lines.append("  Do not repeat attempts that did not help; try a different idea.")
    return "\n".join(lines)


# =====================================================================================================
# Extensions: validity gate, file guard, config-mode search, confirmation on fresh seeds
# =====================================================================================================
import ast
import json
import math
import random
import shutil
from pathlib import Path

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def canon(overrides: dict) -> tuple:
    return tuple(sorted((str(k), json.dumps(v)) for k, v in (overrides or {}).items()))


# ---------------------------------------------------------------------------------- search space
def load_space(path: str | None = None) -> dict | None:
    path = path or _env("ARC_SEARCH_SPACE_FILE")
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def validate_overrides(space_cfg: dict, overrides: Any) -> tuple[dict, list[str]]:
    """Keep only allowed keys/values (values equal to the default are dropped). Returns (clean, errors)."""
    errors: list[str] = []
    clean: dict = {}
    if not isinstance(overrides, dict):
        return {}, ["overrides is not a JSON object"]
    space, defaults = space_cfg["space"], space_cfg.get("defaults", {})
    for key, value in overrides.items():
        if key not in space:
            errors.append(f"unknown key {key!r}")
            continue
        allowed = space[key]["values"]
        match = next(
            (a for a in allowed if isinstance(a, bool) == isinstance(value, bool) and a == value), None
        )
        if match is None and not (isinstance(value, bool) and value in allowed):
            errors.append(f"{key}={value!r} not allowed (allowed: {allowed})")
            continue
        if defaults.get(key) == match and isinstance(defaults.get(key), bool) == isinstance(match, bool):
            continue
        clean[key] = match
    # Drop settings that have no effect for the chosen operator (e.g. attention heads for GraphSAGE), so that
    # functionally identical configurations are recognised as duplicates and never evaluated twice.
    eff = {**defaults, **clean}
    for key, cond in space_cfg.get("relevant_if", {}).items():
        if key in clean and any(eff.get(dep) not in allowed for dep, allowed in cond.items()):
            del clean[key]
    return clean, errors


def read_overrides(config_text: str, var: str) -> dict | None:
    try:
        tree = ast.parse(config_text)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var for t in node.targets):
            try:
                val = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                return None
            return val if isinstance(val, dict) else None
    return None


def write_overrides(config_text: str, var: str, overrides: dict) -> str | None:
    """Replace the top-level assignment `var = {...}` with the given dict (None if not found).
    The text is left untouched when the dict is already the same (no cosmetic differences)."""
    if read_overrides(config_text, var) == overrides:
        return config_text
    try:
        tree = ast.parse(config_text)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var for t in node.targets):
            lines = config_text.splitlines()
            new = f"{var} = {dict(sorted(overrides.items()))!r}"
            lines[node.lineno - 1 : node.end_lineno] = [new]
            return "\n".join(lines) + ("\n" if config_text.endswith("\n") else "")
    return None


# ---------------------------------------------------------------------------------- guard
_SRC_RE = re.compile(r'^PROPOSED_SOURCE\s*=.*$', re.MULTILINE)


def _proposed_source(config_text: str) -> str:
    try:
        tree = ast.parse(config_text)
    except SyntaxError:
        return ""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROPOSED_SOURCE" for t in node.targets):
            try:
                val = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                return ""
            return val if isinstance(val, str) else ""
    return ""


def set_proposed_source(config_text: str, source: str) -> str:
    if not _SRC_RE.search(config_text) or _proposed_source(config_text) == str(source)[:300]:
        return config_text
    return _SRC_RE.sub(lambda m: f"PROPOSED_SOURCE = {str(source)[:300]!r}", config_text, count=1)


LAST_GUARD: dict = {}
_VENDOR_IMPORT = re.compile(r"^\s*(?:from|import)\s+(vendor_\w+)", re.MULTILINE)


def official_imports(files: dict) -> list[str]:
    """Official-code modules (vendor_*.py) imported by the files the LLM writes."""
    found = set()
    for name, text in files.items():
        if name.endswith(".py") and not name.startswith(("vendor_", "rb_model_official")):
            found.update(_VENDOR_IMPORT.findall(text or ""))
    return sorted(found)


def skip_run() -> bool:
    """A candidate identical to the best version is not run at all (it would only measure noise)."""
    return bool(LAST_GUARD.get("unchanged")) and _env("ARC_SKIP_UNCHANGED", "1") == "1"


def skipped_run():
    from types import SimpleNamespace

    return SimpleNamespace(
        returncode=0, stdout="", elapsed_sec=0.0, metrics={}, timed_out=False, arc_skipped=True,
        stderr=("SKIPPED - nothing changed with respect to the current best version, so the run was not executed. "
                "Your edits did not reach the model: edits to protected files (main.py, rb_train.py, rb_data.py, "
                "rb_model_official.py, vendor_*.py ...) are discarded. Change rb_model.py / new files and activate the "
                "change in PROPOSED_OVERRIDES."),  # no 'Error'/'Warning'/'inf' words: must not trigger a repair
    )


def target_for_block(code: str, files: dict) -> str:
    """File an UNLABELLED code block returned by a repair belongs to (the pipeline used to call it main.py,
    which overwrote main.py with the model code in RUN-005)."""
    import difflib

    if "def build_model" in code or "class Model(" in code:
        return "rb_model.py"
    if "PROPOSED_OVERRIDES" in code:
        return "rb_config.py"
    best, score = "main.py", 0.0
    for name, text in files.items():
        if name.startswith("vendor_") or not name.endswith(".py"):
            continue
        r = difflib.SequenceMatcher(None, code[:4000], text[:4000]).ratio()
        if r > score:
            best, score = name, r
    return best


def retarget_repair(repaired: dict, current: dict, protected: list[str]) -> dict:
    """A repair that writes model code into a protected file (e.g. main.py) is moved to the file it belongs to."""
    prefixes = [x.strip() for x in _env("ARC_PROTECTED_PREFIXES", "vendor_").split(",") if x.strip()]
    locked = set(protected) | {n for n in current if any(n.startswith(p) for p in prefixes)}
    editable = {k: v for k, v in current.items() if k not in locked}
    out = {}
    for name, code in repaired.items():
        if name in locked and code != current.get(name):
            target = target_for_block(code, editable)
            if target not in locked:
                out[target] = code
                continue
        out[name] = code
    return out


def guard_candidate(best_files: dict, candidate: dict, space_cfg: dict | None, protected: list[str]) -> tuple[dict, list[str]]:
    """Undo every change outside what the refinement may touch.
    - files in `protected` are restored from the best version;
    - the config file keeps everything of the best version except the validated override dict."""
    notes: list[str] = []
    out = dict(candidate)
    prefixes = [x.strip() for x in _env("ARC_PROTECTED_PREFIXES", "vendor_").split(",") if x.strip()]
    for name in list(out):
        if any(name.startswith(pfx) for pfx in prefixes):
            if name in best_files and out[name] != best_files[name]:
                out[name] = best_files[name]
                notes.append(f"restored read-only file {name}")
            elif name not in best_files:
                del out[name]
                notes.append(f"dropped new read-only file {name}")
    for name in protected:
        if name in best_files and out.get(name) != best_files[name]:
            out[name] = best_files[name]
            notes.append(f"restored protected file {name}")
        elif name not in best_files and name in out:
            del out[name]
            notes.append(f"dropped new protected file {name}")
    if space_cfg:
        cfile, var = space_cfg["config_file"], space_cfg["variable"]
        if cfile in best_files:
            cand_text = candidate.get(cfile, best_files[cfile])
            prop = read_overrides(cand_text, var)
            if prop is None:
                prop = read_overrides(best_files[cfile], var) or {}
                notes.append(f"{cfile}: override dict unreadable, kept the best one")
            if _env("ARC_SEARCH_MODE") == "config":
                clean, errs = validate_overrides(space_cfg, prop)
            else:  # code mode: the LLM may introduce new keys for the components it implements
                clean, errs = (dict(prop) if isinstance(prop, dict) else {}), []
                locked = set(space_cfg.get("locked_keys", []))
                if _env("ARC_LOCK_RECIPE", "1") == "1" and locked & set(clean):
                    errs = [f"training-recipe keys are fixed and were removed: {sorted(locked & set(clean))}"]
                    clean = {k: v for k, v in clean.items() if k not in locked}
            notes += [f"{cfile}: {e}" for e in errs]
            new_text = write_overrides(best_files[cfile], var, clean)
            if new_text is not None and _env("ARC_SEARCH_MODE") != "config":
                new_text = set_proposed_source(new_text, _proposed_source(cand_text))
            if new_text is not None:
                if new_text != cand_text:
                    notes.append(f"{cfile}: everything except {var} restored")
                out[cfile] = new_text
    # drop files the LLM invented in config mode (nothing but the known project files may exist)
    for name in list(out):
        if name not in best_files and _env("ARC_SEARCH_MODE") == "config":
            del out[name]
            notes.append(f"dropped unknown file {name}")
    LAST_GUARD["unchanged"] = all(out.get(k) == v for k, v in best_files.items()) and set(out) == set(best_files)
    if LAST_GUARD["unchanged"]:
        notes.append("the candidate is identical to the current best version")
    LAST_GUARD["notes"] = list(notes)
    LAST_GUARD["official_imports"] = official_imports(out)
    return out, notes


# ---------------------------------------------------------------------------------- gate
def _task():
    try:
        from researchclaw.pipeline.stage_impls._arc_knowledge import task_info

        return task_info()
    except Exception:  # noqa: BLE001
        return {"dataset": "rel-f1", "task": "driver-top3", "type": "binary classification", "metric": "ROC-AUC",
                "metric_key": "roc_auc", "higher": True}


def expected_from_stage12(run_dir: Path) -> dict:
    """Seed count / conditions / noise level of the reference run (stage 12)."""
    try:
        m = json.loads((Path(run_dir) / "stage-12" / "runs" / "run-1.json").read_text()).get("metrics") or {}
    except (OSError, ValueError):
        return {}
    conds = sorted(k[: -len("_n_seeds")] for k in m if k.endswith("_n_seeds"))
    n = m.get("proposed_n_seeds")
    std = m.get(f"proposed_val_{_task()['metric_key']}_std")
    se = float(std) / math.sqrt(float(n)) if n and std else None
    return {"seeds": int(n) if n else None, "conditions": conds, "se": se}


def run_is_valid(run: Any, expected: dict, metric_key: str = "primary_metric") -> tuple[bool, str]:
    """A refinement run counts only if it ran to completion with every condition and every seed."""
    if run is None:
        return False, "no run"
    if getattr(run, "timed_out", False):
        return False, "timed out"
    if getattr(run, "returncode", 1) != 0:
        return False, f"exit code {getattr(run, 'returncode', None)}"
    m = getattr(run, "metrics", None) or {}
    if not isinstance(m.get(metric_key), (int, float)) or not math.isfinite(m[metric_key]):
        return False, f"no finite {metric_key}"
    seeds = {k: v for k, v in m.items() if k.endswith("_n_seeds")}
    if "proposed_n_seeds" not in seeds:
        return False, "proposed condition did not complete (no proposed_n_seeds)"
    if len(set(seeds.values())) != 1:
        return False, f"conditions ran different numbers of seeds: {seeds}"
    want = expected.get("seeds")
    if want and int(seeds["proposed_n_seeds"]) != want:
        return False, f"{int(seeds['proposed_n_seeds'])} seeds instead of {want}"
    missing = [c for c in expected.get("conditions", []) if f"{c}_n_seeds" not in seeds]
    if missing:
        return False, f"missing conditions: {missing}"
    return True, ""


def margin_ok(new: float, best: float | None, direction: str, margin: float) -> bool:
    if best is None or margin <= 0:
        return True
    return (new - best >= margin) if direction != "minimize" else (best - new >= margin)


# ---------------------------------------------------------------------------------- config-mode proposals
class _Resp:
    def __init__(self, content: str):
        self.content = content


LAST: dict = {}  # last proposal (read by the patched loop to annotate the iteration record)


def _extract_json(text: str) -> dict | None:
    text = _THINK.sub("", text or "")
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = dec.raw_decode(text[m.start():])
        except ValueError:
            continue
        if isinstance(obj, dict) and "overrides" in obj:
            return obj
    return None


def previous_passes(run_dir) -> list[dict]:
    """Refinement logs of earlier passes of this run (the pipeline archives them as stage-13_v1, _v2, ...)."""
    logs = []
    for p in Path(run_dir).glob("stage-13_v*/refinement_log.json"):
        try:
            L = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        L["_dir"] = str(p.parent)
        logs.append(L)
    logs.sort(key=lambda L: str(L.get("generated", "")))
    return logs


def _evaluated(log: dict, prev_logs: list | None = None) -> list[tuple[dict, float | None, str]]:
    """All configurations evaluated so far in this run (earlier passes first); carried-over records are skipped."""
    rows = [({}, None, "initial")]
    for L in list(prev_logs or []) + [log]:
        for it in L.get("iterations", []):
            if isinstance(it, dict) and "arc_overrides" in it and not it.get("arc_carried_from"):
                note = it.get("arc_rejected") or ("improved" if it.get("improved") else "")
                rows.append((it["arc_overrides"], it.get("metric"), note))
    return rows


def warm_start(state: "ModeState", best_files: dict, best_metric, direction: str = "maximize") -> dict | None:
    """Start this pass from the best ACCEPTED version of earlier passes (if it is at least as good as the current best)."""
    cfile, var = state.space["config_file"], state.space["variable"]
    best_rec, best_val = None, None
    best_dir = None
    for L in state.prev_logs:
        for it in L.get("iterations", []):
            m = it.get("metric") if isinstance(it, dict) else None
            if not isinstance(m, (int, float)) or it.get("arc_rejected") or it.get("arc_carried_from"):
                continue
            # only versions that were ACCEPTED as a new best (noise margin + re-check on other seeds). RUN-008: the best
            # metric of ANY attempt was used, so pass 2 started from a single, never re-checked run (test 0.742).
            if not it.get("improved") and _env("ARC_WARM_START_ANY") != "1":
                continue
            if state.config_mode and "arc_overrides" not in it:
                continue
            better = best_val is None or ((m > best_val) if direction != "minimize" else (m < best_val))
            if better:
                best_rec, best_val, best_dir = it, m, L.get("_dir")
    if best_rec is None:
        return None
    # The upstream pipeline already recovers the best metric of earlier passes (BUG-58) but NOT their files: warm-start
    # whenever the earlier best is at least as good as the current best metric (a tiny tolerance covers rounding).
    eps = 1e-9
    if best_metric is not None and ((best_val < best_metric - eps) if direction != "minimize" else (best_val > best_metric + eps)):
        return None
    if not state.config_mode:  # code mode: the whole project of the best earlier version
        vdir = Path(str(best_dir or "")) / str(best_rec.get("version_dir", "")).strip("/")
        if not vdir.is_dir():
            return None
        files = {p.name: p.read_text(encoding="utf-8") for p in vdir.glob("*.py")}
        if not files:
            return None
        best_rec = dict(best_rec)
        best_rec.setdefault("arc_overrides", read_overrides(files.get(cfile, ""), var) or {})
    else:
        new_text = write_overrides(best_files[cfile], var, best_rec["arc_overrides"])
        if new_text is None:
            return None
        files = dict(best_files)
        files[cfile] = new_text
    sbx = best_rec.get("sandbox_after_fix") or best_rec.get("sandbox") or {}
    record = {
        "iteration": 0, "version_dir": "experiment_v0/", "files": sorted(files), "validation_ok": True,
        "validation_summary": "carried over from an earlier pass", "repaired": False, "metric": best_val,
        "improved": False, "arc_overrides": dict(best_rec["arc_overrides"]),
        "arc_carried_from": f"iteration {best_rec.get('iteration')} of an earlier pass",
        "sandbox": {"returncode": sbx.get("returncode", 0), "metrics": sbx.get("metrics", {}),
                    "elapsed_sec": sbx.get("elapsed_sec"), "timed_out": False, "stderr": "", "stdout": ""},
    }
    return {"files": files, "metric": best_val, "overrides": dict(best_rec["arc_overrides"]), "record": record}


def _neighbours(space_cfg: dict, base: dict) -> list[dict]:
    defaults = space_cfg.get("defaults", {})
    out = []
    for key, spec in space_cfg["space"].items():
        for value in spec["values"]:
            cur = base.get(key, defaults.get(key))
            if value == cur:
                continue
            cand = dict(base)
            cand[key] = value
            clean, errs = validate_overrides(space_cfg, cand)
            if not errs:
                out.append(clean)
    return out


def _fallback(space_cfg: dict, best: dict, seen: set, iteration: int) -> dict:
    rng = random.Random(1000 + iteration)
    cands = [c for c in _neighbours(space_cfg, best) if canon(c) not in seen]
    if not cands:  # every neighbour of the best was tried: restart from the default
        cands = [c for c in _neighbours(space_cfg, {}) if canon(c) not in seen]
    return rng.choice(cands) if cands else {}


def _fmt(x) -> str:
    return f"{x:.4f}" if isinstance(x, (int, float)) and math.isfinite(x) else "n/a"


def build_proposal_prompt(space_cfg, rows, best, best_metric, baseline_metric, expected, margin, topic, max_keys) -> tuple[str, str]:
    se = expected.get("se")
    lines = []
    for i, (ov, metric, note) in enumerate(rows):
        m = _fmt(baseline_metric) if i == 0 else (_fmt(metric) if metric is not None else "FAILED/REJECTED")
        tag = f"  [{note}]" if note and note != "initial" else ""
        lines.append(f"  #{i}: {json.dumps(ov, sort_keys=True)} -> {m}{tag}")
    space = "\n".join(
        f"  - {k}: {json.dumps(v['values'])} -- {v.get('doc', '')}" for k, v in space_cfg["space"].items()
    )
    seeds = expected.get("seeds") or "several"
    noise = (f"the standard error of the metric is about {se:.3f}; " if se else "the metric is noisy; ")
    system = (
        "You are an ML researcher running a sequential search over a discrete architecture space. "
        "You answer with exactly one JSON object and nothing else."
    )
    user = (
        f"Topic: {topic}\n\n"
        f"Goal: improve a graph neural network on RelBench {_task()['dataset']} / {_task()['task']} ({_task()['type']}). "
        f"Metric: validation {_task()['metric']} averaged over {seeds} seeds; the numbers below are primary_metric values, "
        f"HIGHER is better{'' if _task()['higher'] else ' (primary_metric = -' + _task()['metric'] + ')'}. "
        "The training recipe is fixed; you only choose "
        "architecture settings.\n"
        f"Noise: {noise}a candidate is accepted as an improvement only if it beats the best so far by at least {margin:.3f}.\n\n"
        "SEARCH SPACE (key: allowed values -- meaning). The defaults are the official GraphSAGE setup: "
        f"{json.dumps(space_cfg.get('defaults', {}))}\n{space}\n\n"
        "EVALUATED SO FAR (overrides relative to the defaults -> validation metric):\n" + "\n".join(lines) + "\n\n"
        f"BEST SO FAR: {json.dumps(best, sort_keys=True)} -> {_fmt(best_metric)}\n\n"
        "RULES:\n"
        '- Reply with ONE JSON object: {"overrides": {...}, "rationale": "<one sentence>"}.\n'
        '- "overrides" is the COMPLETE set of settings that differ from the defaults for the next candidate.\n'
        f"- Change at most {max_keys} keys relative to the BEST configuration so you can attribute the effect.\n"
        "- Never repeat a configuration listed above. Use only the keys and values of the search space.\n"
        "- Early on, explore different dimensions; later, combine what helped and refine it.\n"
    )
    return system, user


def propose_config(chat, llm, state: "ModeState", best_files: dict, log: dict, iteration: int, best_metric, baseline_metric) -> _Resp:
    """Ask the LLM for the next configuration; fall back to a deterministic neighbour search."""
    space_cfg = state.space
    cfile, var = space_cfg["config_file"], space_cfg["variable"]
    best = read_overrides(best_files[cfile], var) or {}
    rows = _evaluated(log, state.prev_logs)
    seen = {canon(r[0]) for r in rows}
    max_keys = int(space_cfg.get("max_keys_changed_per_step", 3))
    system, user = build_proposal_prompt(space_cfg, rows, best, best_metric, baseline_metric, state.expected,
                                         state.margin, state.topic, max_keys)
    chosen, why, source = None, "", "llm"
    for attempt in range(2):
        try:
            resp = chat(llm, system, user + (f"\nYour previous answer was rejected: {why}\n" if why else ""), max_tokens=4096)
            obj = _extract_json(getattr(resp, "content", "") or "")
        except Exception as exc:  # noqa: BLE001
            obj, why = None, f"LLM call failed: {exc}"
        if obj is None:
            why = why or "no JSON object with an 'overrides' key found"
            continue
        clean, errs = validate_overrides(space_cfg, obj.get("overrides"))
        changed = {k for k in set(clean) | set(best) if clean.get(k) != best.get(k)}
        if errs:
            why = "; ".join(errs[:3])
        elif canon(clean) in seen:
            why = "this configuration was already evaluated"
        elif len(changed) > max_keys:
            why = f"{len(changed)} keys differ from the best configuration (max {max_keys})"
        else:
            chosen, why = clean, ""
            LAST.update(rationale=str(obj.get("rationale", ""))[:300])
            break
    if chosen is None:
        chosen, source = _fallback(space_cfg, best, seen, iteration), "fallback"
        LAST.update(rationale=f"fallback neighbour search ({why})")
    LAST.update(overrides=chosen, source=source, iteration=iteration)
    new_text = write_overrides(best_files[cfile], var, chosen)
    content = f"```filename:{cfile}\n{new_text}\n```" if new_text else ""
    return _Resp(content)


# ---------------------------------------------------------------------------------- state / env
class ModeState:
    def __init__(self, run_dir, stage_dir, topic=""):
        self.mode = _env("ARC_SEARCH_MODE", "code")
        self.space = load_space() if self.mode == "config" or _env("ARC_SEARCH_SPACE_FILE") else None
        if self.mode == "config" and self.space is None:
            self.mode = "code"  # no usable search space: behave as before
        self.protected = [x.strip() for x in _env("ARC_PROTECTED_FILES").split(",") if x.strip()]
        try:
            self.margin = float(_env("ARC_MIN_IMPROVEMENT", "0") or 0)
        except ValueError:
            self.margin = 0.0
        self.expected = expected_from_stage12(run_dir)
        self.topic = topic
        self.confirm_offset = _env("ARC_CONFIRM_SEED_OFFSET")
        self.stage_dir = Path(stage_dir)
        self.run_dir = Path(run_dir)
        self.prev_logs = previous_passes(run_dir)
        mf = _env("ARC_METHOD_FILE")
        if mf and not self.prev_logs:  # first pass of a run: never leak the description of an earlier run
            try:
                Path(mf).write_text("# (no description yet - generated at the end of stage 13)\n", encoding="utf-8")
            except OSError:
                pass

    @property
    def config_mode(self) -> bool:
        return self.mode == "config"

    @property
    def gate_enabled(self) -> bool:
        # only for experiments whose reference run reports per-condition seed counts (*_n_seeds)
        return _env("ARC_VALID_GATE", "1") == "1" and bool(self.expected.get("seeds"))


def annotate(iter_record: dict, state: ModeState) -> None:
    if LAST_GUARD.get("notes"):
        iter_record["arc_guard_notes"] = list(LAST_GUARD["notes"])[:6]
    iter_record["arc_official_code"] = list(LAST_GUARD.get("official_imports", []))
    if state.config_mode and LAST:
        iter_record["arc_overrides"] = dict(LAST.get("overrides", {}))
        iter_record["arc_source"] = LAST.get("source")
        iter_record["arc_rationale"] = LAST.get("rationale")


# ---------------------------------------------------------------------------------- confirmation on fresh seeds
_SEED_OFFSET_RE = re.compile(r'^SEED_OFFSET\s*=.*$', re.MULTILINE)


def make_confirm_files(best_files: dict, offset: int, cfile: str = "rb_config.py") -> dict | None:
    text = best_files.get(cfile)
    if not text or not _SEED_OFFSET_RE.search(text):
        return None
    out = dict(best_files)
    out[cfile] = _SEED_OFFSET_RE.sub(f"SEED_OFFSET = {int(offset)}", text, count=1)
    return out


def confirm(state: ModeState, config, stage_dir: Path, best_files: dict, best_version: str, log: dict, create_sandbox, write_project, logger) -> None:
    """Re-run the final project on seeds never used for selection; store the numbers, never use them to choose."""
    if not state.confirm_offset:
        return
    files = make_confirm_files(best_files, int(state.confirm_offset),
                               (state.space or {}).get("config_file", "rb_config.py"))
    if files is None:
        logger.warning("Stage 13: confirmation skipped (SEED_OFFSET not found in the config file)")
        return
    cdir = Path(stage_dir) / "confirm_project"
    write_project(cdir, files)
    sandbox = create_sandbox(config.experiment, Path(stage_dir) / "confirm_sandbox")
    res = sandbox.run_project(cdir, timeout_sec=config.experiment.time_budget_sec)
    ok, why = run_is_valid(res, state.expected)
    per_seed: list = []
    for rj in sorted((Path(stage_dir) / "confirm_sandbox").glob("_project*/results.json")):
        try:
            per_seed = json.loads(rj.read_text(encoding="utf-8")).get("results", [])
        except (OSError, ValueError):
            pass
    info = {"seed_offset": int(state.confirm_offset), "valid": ok, "reason": why,
            "returncode": res.returncode, "metrics": res.metrics}
    if ok and per_seed:
        info["paired"] = {f"{a}-{b}:{k}": paired_stats(per_seed, a, b, k)
                          for a, b in (("proposed", "baseline_tuned"), ("proposed", "baseline_graphsage"), ("baseline_tuned", "baseline_graphsage"))
                          for k in ("val", "test")}
    (Path(stage_dir) / "confirmation.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    try:
        write_method_file(state, best_files, best_version, log, info, per_seed)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Stage 13: could not write the method file: %s", exc)
    log["confirmation"] = {k: v for k, v in info.items() if k != "metrics"}
    if not ok:
        logger.warning("Stage 13: confirmation run not valid (%s)", why)
        return
    # expose the numbers to stage 14 (they are merged from the best iteration's metrics)
    extra = {f"confirm_{k}": v for k, v in (res.metrics or {}).items()
             if isinstance(v, (int, float)) and (k.endswith("_mean") or k.endswith("_std") or k.endswith("_n_seeds")
                                                 or k.startswith("improvement_over"))}
    for it in log.get("iterations", []):
        if isinstance(it, dict) and it.get("version_dir") == best_version:
            for key in ("sandbox", "sandbox_after_fix"):
                if isinstance(it.get(key), dict) and isinstance(it[key].get("metrics"), dict):
                    it[key]["metrics"].update(extra)
    m = res.metrics or {}
    lines = [f"# Confirmation on fresh seeds (offset {state.confirm_offset})", "",
             "These seeds were never used to choose anything.", "",
             f"| condition | val {_task()['metric']} | test {_task()['metric']} |", "|---|---|---|"]
    mk = _task()["metric_key"]
    for cond in sorted(k[: -len("_n_seeds")] for k in m if k.endswith("_n_seeds")):
        lines.append(f"| {cond} | {m.get(f'{cond}_val_{mk}_mean', float('nan')):.4f} ± {m.get(f'{cond}_val_{mk}_std', float('nan')):.4f} "
                     f"| {m.get(f'{cond}_test_{mk}_mean', float('nan')):.4f} ± {m.get(f'{cond}_test_{mk}_std', float('nan')):.4f} |")
    (Path(stage_dir) / "confirmation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.warning("Stage 13: confirmation done -> %s", (Path(stage_dir) / "confirmation.md"))


# =====================================================================================================
# Ground truth about the evaluated method + paired statistics (used by the analysis / paper stages)
# =====================================================================================================
def paired_stats(results: list[dict], a: str, b: str, key: str, higher: bool | None = None) -> dict | None:
    """Paired comparison of condition `a` minus `b` over common seeds (exact sign-flip test, bootstrap CI).
    `seeds_better` counts the seeds where `a` is better (higher, or lower for an error metric such as MAE)."""
    if higher is None:
        higher = bool(_task().get("higher", True))
    import itertools

    import numpy as np

    va = {r["seed"]: r[key] for r in results if r.get("condition") == a and key in r}
    vb = {r["seed"]: r[key] for r in results if r.get("condition") == b and key in r}
    seeds = sorted(set(va) & set(vb))
    if len(seeds) < 3:
        return None
    d = np.array([va[s] - vb[s] for s in seeds], dtype=float)
    n = len(d)
    mean, se = float(d.mean()), float(d.std(ddof=1) / math.sqrt(n))
    if n <= 16:
        flips = np.array(list(itertools.product([-1, 1], repeat=n)))
        p = float((np.abs((flips * d).mean(1)) >= abs(mean) - 1e-12).mean())
    else:
        p = float("nan")
    rng = np.random.default_rng(0)
    boots = np.array([d[rng.integers(0, n, n)].mean() for _ in range(10000)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n": n, "mean_diff": mean, "se": se, "ci95": [float(lo), float(hi)], "p_signflip": p,
            "seeds_better": int((d > 0).sum() if higher else (d < 0).sum())}


def _code_changes(files: dict) -> str:
    """Summary of what the LLM changed in the editable model with respect to the frozen official one."""
    import difflib

    new, off = files.get("rb_model.py", ""), files.get("rb_model_official.py", "")
    if not new or not off:
        return ""
    diff = [l for l in difflib.unified_diff(off.splitlines(), new.splitlines(), lineterm="", n=0)
            if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    added = re.findall(r"^\+\s*(?:class|def)\s+(\w+)", "\n".join(diff), re.MULTILINE)
    extra = sorted(n for n in files if n.endswith(".py") and n not in {
        "main.py", "rb_config.py", "rb_data.py", "rb_loader.py", "rb_model.py", "rb_model_official.py", "rb_text.py", "rb_train.py"})
    src = _proposed_source(files.get("rb_config.py", ""))
    parts = [f"- declared source (implementation card): {src or 'none'}",
             f"- rb_model.py vs the official model: {len(diff)} changed lines; new classes/functions: {added or 'none'}",
             "- the exact changed lines (describe THESE operations, using standard names such as TransformerConv; option "
             "names chosen by the LLM, e.g. a gnn_type called after a paper, are NOT the name of the method):",
             "```diff", *[l[:160] for l in diff[:60]], "```"]
    if extra:
        parts.append(f"- new files: {extra}")
    return "\n".join(parts)


def write_method_file(state: ModeState, best_files: dict, best_version: str, log: dict, conf_info: dict | None, results: list | None) -> None:
    """Authoritative description of what was actually evaluated, for the analysis / paper stages."""
    path = _env("ARC_METHOD_FILE")
    if not path:
        return
    cfile, var = state.space["config_file"], state.space["variable"]
    overrides = read_overrides(best_files.get(cfile, ""), var) or {}
    defaults = state.space.get("defaults", {})
    rows = _evaluated(log, state.prev_logs)
    n_eval = len(rows) - 1
    valid = [(o, m) for o, m, note in rows[1:] if m is not None]
    L = ["## GROUND TRUTH ABOUT THE EVALUATED METHOD (generated from the run's own files; authoritative)", ""]
    code_changes = _code_changes(best_files) if state.mode == "code" else ""
    if code_changes:
        L.append("The model evaluated as `proposed` is the OFFICIAL RelBench pipeline (PyTorch Frame feature encoder + relative-time "
                 "encoder + heterogeneous GNN + MLP head) with the code changes and settings below. Describe exactly these; do not "
                 "invent components.")
        L.append(code_changes)
        L.append("Settings of `proposed` that differ from the official defaults:")
    else:
        L.append("There is NO new named method, module or layer. The model evaluated as `proposed` is the OFFICIAL RelBench heterogeneous "
                 "GraphSAGE pipeline (PyTorch Frame feature encoder + relative-time encoder + GNN + MLP head) with only these "
                 "architecture settings changed (every other setting is the official default):")
    if overrides:
        for k, v in sorted(overrides.items()):
            L.append(f"- `{k}` = {v!r} (official default: {defaults.get(k)!r}) - {state.space['space'].get(k, {}).get('doc', '')}")
    else:
        L.append("- (none: `proposed` is identical to `baseline_tuned`; the search found no better configuration)")
    L += ["", "Conditions: `baseline_graphsage` = official model with the official training recipe (batch size 512); "
          "`baseline_tuned` = the same official architecture with a better recipe (batch size 128, i.e. 4x more optimiser updates); "
          "`proposed` = `baseline_tuned` + the changes above (same recipe as `baseline_tuned`).",
          f"Search procedure: sequential search over architecture settings proposed by an LLM and executed automatically; {n_eval} "
          f"configurations evaluated ({len(valid)} valid), selection metric = validation {_task()['metric']} averaged over seeds. The test split "
          "was never used for selection. The search space is in `search_space.json` (operator, depth, width, aggregation, dropout, "
          "residual / jumping knowledge, encoder depth/width/dropout, time encoding, readout depth).", ""]
    if valid:
        L.append(f"Evaluated configurations (primary_metric = validation {_task()['metric']} of `proposed`, mean over seeds"
                 f"{'' if _task()['higher'] else ', sign flipped'}):")
        for o, m in sorted(valid, key=lambda x: -x[1])[:12]:
            L.append(f"- {json.dumps(o, sort_keys=True)}: {m:.4f}")
        L.append("")
    if conf_info and conf_info.get("valid"):
        m = conf_info["metrics"]
        L.append(f"CONFIRMATION on fresh seeds (offset {conf_info['seed_offset']}, never used for selection) - the numbers to report:")
        for c in sorted(k[: -len("_n_seeds")] for k in m if k.endswith("_n_seeds")):
            mk, mn = _task()["metric_key"], _task()["metric"]
            L.append(f"- {c}: val {mn} {m.get(f'{c}_val_{mk}_mean', float('nan')):.4f} +/- {m.get(f'{c}_val_{mk}_std', float('nan')):.4f}, "
                     f"test {mn} {m.get(f'{c}_test_{mk}_mean', float('nan')):.4f} +/- {m.get(f'{c}_test_{mk}_std', float('nan')):.4f} "
                     f"({int(m[c + '_n_seeds'])} seeds)")
        for a, b in (("proposed", "baseline_tuned"), ("proposed", "baseline_graphsage"), ("baseline_tuned", "baseline_graphsage")):
            for key, name in (("val", "validation"), ("test", "test")):
                st = paired_stats(results or [], a, b, key)
                if st:
                    L.append(f"- paired {name} difference {a} - {b}: {st['mean_diff']:+.4f} (95% bootstrap CI [{st['ci95'][0]:+.4f}, {st['ci95'][1]:+.4f}], "
                             f"better on {st['seeds_better']}/{st['n']} seeds, sign-flip p = {st['p_signflip']:.3f})")
        L.append("")
    L += ["RULES FOR WRITING: describe the method exactly as above and do not invent components (no projection matrices, attention "
          "modules, new loss terms or named methods); hypotheses written before the experiments may mention components that were "
          "never implemented - ignore them. Report the confirmation numbers (not only the best search run), state which differences are "
          "statistically supported and which are not, and note that the official baseline is under-trained, so most of the gain over it "
          "comes from the training recipe (`baseline_tuned`), not from the architecture. Validation and test are single splits of one "
          f"dataset: do not generalise beyond {_task()['dataset']} / {_task()['task']}."]
    try:
        Path(path).write_text("\n".join(L) + "\n", encoding="utf-8")
    except OSError:
        pass


def method_text() -> str:
    path = _env("ARC_METHOD_FILE")
    if not path:
        return ""
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return text if "GROUND TRUTH ABOUT THE EVALUATED METHOD" in text else ""


# =====================================================================================================
# Knowledge gate (code mode) + "change actually activated" check + global deadline
# =====================================================================================================
def knowledge_gate(run, candidate_files: dict, state) -> tuple[bool, str]:
    m = getattr(run, "metrics", None) or {}
    if LAST_GUARD.get("unchanged") and _env("ARC_REJECT_UNCHANGED", "1") == "1":
        return False, ("nothing changed with respect to the current best version: re-running the same code only "
                       "measures noise - change the model")
    if m.get("proposed_identical_to_baseline") == 1.0:
        return False, ("`proposed` is functionally identical to `baseline_tuned` (same outputs at initialisation): "
                       "the change was not activated - enable it through PROPOSED_OVERRIDES or change rb_model.py")
    if getattr(state, "mode", "") == "code" and _env("ARC_REQUIRE_KNOWLEDGE_REF", "1") == "1":
        try:
            from researchclaw.pipeline.stage_impls._arc_knowledge import knowledge_ref_ok
        except ImportError:
            return True, ""
        cfile = (state.space or {}).get("config_file", "rb_config.py") if getattr(state, "space", None) else "rb_config.py"
        return knowledge_ref_ok(candidate_files or {}, cfile)
    return True, ""


def past_deadline() -> bool:
    """True when the global time budget of the run (ARC_RUN_STARTED_AT + ARC_DEADLINE_HOURS) is about to end;
    ARC_DEADLINE_RESERVE_MIN minutes are kept for the analysis and writing stages."""
    try:
        start = float(_env("ARC_RUN_STARTED_AT") or 0)
        hours = float(_env("ARC_DEADLINE_HOURS") or 0)
        reserve = float(_env("ARC_DEADLINE_RESERVE_MIN", "75") or 75)
    except ValueError:
        return False
    if start <= 0 or hours <= 0:
        return False
    import time as _t

    return _t.time() > start + hours * 3600 - reserve * 60


# =====================================================================================================
# Noise-robust acceptance: a candidate that beats the best is re-evaluated on a second set of seeds
# =====================================================================================================
def no_gain_value(best, direction: str):
    """A value that is never an improvement over `best` (used when the re-check run is not valid)."""
    return best - 1e-6 if direction != "minimize" else best + 1e-6


def recheck_enabled() -> bool:
    return _env("ARC_RECHECK", "1") == "1"


def recheck(metric_val, version_dir, stage_dir, iteration, config, create_sandbox, metric_key, iter_record, state, logger):
    """In RUN-005 the same code evaluated three times gave 0.790, 0.806 and 0.816: the 'improvements' were noise.
    Before accepting, re-run the candidate on seeds that differ from the selection seeds and use the MEAN of the two
    evaluations. Returns the new metric (None if the second run is not valid)."""
    import shutil

    offset = int(_env("ARC_RECHECK_SEED_OFFSET", "200") or 200)
    files = {p.name: p.read_text(encoding="utf-8") for p in Path(version_dir).glob("*.py")}
    cfile = (state.space or {}).get("config_file", "rb_config.py") if getattr(state, "space", None) else "rb_config.py"
    mod = make_confirm_files(files, offset, cfile)
    if mod is None:
        return metric_val
    rdir = Path(stage_dir) / f"recheck_v{iteration}"
    if rdir.exists():
        shutil.rmtree(rdir, ignore_errors=True)
    rdir.mkdir(parents=True)
    for name, text in mod.items():
        (rdir / name).write_text(text, encoding="utf-8")
    sandbox = create_sandbox(config.experiment, Path(stage_dir) / f"recheck_sandbox_v{iteration}")
    res = sandbox.run_project(rdir, timeout_sec=config.experiment.time_budget_sec)
    ok, why = run_is_valid(res, state.expected, metric_key)
    second = (res.metrics or {}).get(metric_key) if ok else None
    iter_record["arc_recheck"] = {"seed_offset": offset, "first": metric_val, "second": second, "valid": ok, "reason": why}
    if second is None:
        logger.warning("Stage 13 iteration %d: re-check run not valid (%s)", iteration, why)
        return None
    mean = (float(metric_val) + float(second)) / 2.0
    logger.warning("Stage 13 iteration %d: re-check %.4f / %.4f -> %.4f", iteration, metric_val, second, mean)
    return mean


# =====================================================================================================
# 0.6.3: repair only real failures, recent history in the prompt, environment problems (busy GPU)
# =====================================================================================================
def gpu_unavailable(run: Any) -> bool:
    """main.py printed GPU_UNAVAILABLE: the GPU stayed full (other processes) - nothing to repair in the code."""
    return "GPU_UNAVAILABLE" in (getattr(run, "stdout", "") or "")


def repair_issues(run: Any, metric_val, detect) -> str:
    """Text for the stage-13 runtime repair, or '' when no repair is needed.

    Upstream asks the LLM to 'repair' every run whose stderr contains the word Warning; torch_frame prints
    UserWarnings in every RelBench run, so every attempt - even a valid one - was followed by a repair call and a
    second run, and the evaluated code was the repaired one. Here the repair runs only if the run really failed:
    non-zero exit (not a timeout), no primary metric, or NaN/Inf metrics. ARC_REPAIR_ON_WARNINGS=1 restores upstream."""
    if _env("ARC_REPAIR_ON_WARNINGS") == "1":
        return detect(run)
    if gpu_unavailable(run) or getattr(run, "arc_skipped", False):
        return ""  # environment problem / unchanged candidate that was not run: nothing to repair
    rc = getattr(run, "returncode", None)
    timed_out = bool(getattr(run, "timed_out", False))
    bad_values = False
    for v in (getattr(run, "metrics", None) or {}).values():
        try:
            bad_values = bad_values or not math.isfinite(float(v))
        except (TypeError, ValueError):
            pass
    failed = (rc not in (0, None) and not timed_out) or metric_val is None or bad_values
    if not failed:
        return ""
    text = detect(run) or ""
    if not text:
        tail = (getattr(run, "stderr", "") or "")[-3000:]
        text = (f"The run exited with code {rc} and produced no primary metric."
                + (f"\nstderr tail:\n{tail}" if tail.strip() else ""))
    return text


_HISTORY_PREFIX = "REFINEMENT HISTORY"


def _digest(entry: str) -> str:
    lines = entry.splitlines()
    m = re.search(r"attempt (\d+)", lines[0] if lines else "")
    head = f"attempt {m.group(1)}" if m else (lines[0][:60] if lines else "")
    keep = [ln.strip() for ln in lines[1:]
            if ln.strip().startswith(("files changed", "configuration overrides", "REJECTED", "RESULT", "official code"))]
    return head + ": " + " | ".join(x[:160] for x in keep)


def summaries_for_prompt(summaries: list, keep_last: int | None = None, max_chars: int | None = None) -> list:
    """Run summaries for the iterative_improve prompt.

    Upstream passes run_summaries[:20], i.e. the FIRST 20 entries: after ~19 attempts the LLM no longer saw the
    outcome of its latest attempts. Kept: the stage-12 summaries (first 20 non-history entries), a one-line digest
    of older attempts and the last `keep_last` attempts in full, within `max_chars`."""
    if keep_last is None:
        keep_last = int(_env("ARC_HISTORY_LAST", "12") or 12)
    if max_chars is None:
        max_chars = int(_env("ARC_HISTORY_MAX_CHARS", "40000") or 40000)
    base = [s for s in summaries if not str(s).startswith(_HISTORY_PREFIX)][:20]
    hist = [s for s in summaries if str(s).startswith(_HISTORY_PREFIX)]
    old, recent = hist[:-keep_last] if keep_last > 0 else hist, hist[-keep_last:] if keep_last > 0 else []
    while recent and sum(len(x) for x in recent) > max_chars:
        old, recent = old + recent[:1], recent[1:]
    out = list(base)
    if old:
        digest = [_digest(x) for x in old]
        text = "EARLIER ATTEMPTS (one line each, oldest first; full details only for the most recent ones):\n" + \
            "\n".join(f"- {d}" for d in digest)
        if len(text) > max_chars // 2:
            text = text[: max_chars // 4] + "\n- ...\n" + text[-max_chars // 4:]
        out.append(text)
    return out + recent

