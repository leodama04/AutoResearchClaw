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
    if metric is None:
        err = (sandbox.get("stderr") or "").strip()[-400:]
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
    """Replace the top-level assignment `var = {...}` with the given dict (None if not found)."""
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
def guard_candidate(best_files: dict, candidate: dict, space_cfg: dict | None, protected: list[str]) -> tuple[dict, list[str]]:
    """Undo every change outside what the refinement may touch.
    - files in `protected` are restored from the best version;
    - the config file keeps everything of the best version except the validated override dict."""
    notes: list[str] = []
    out = dict(candidate)
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
            clean, errs = validate_overrides(space_cfg, prop)
            notes += [f"{cfile}: {e}" for e in errs]
            new_text = write_overrides(best_files[cfile], var, clean)
            if new_text is not None:
                if new_text != cand_text:
                    notes.append(f"{cfile}: everything except {var} restored")
                out[cfile] = new_text
    # drop files the LLM invented in config mode (nothing but the known project files may exist)
    for name in list(out):
        if name not in best_files and _env("ARC_SEARCH_MODE") == "config":
            del out[name]
            notes.append(f"dropped unknown file {name}")
    return out, notes


# ---------------------------------------------------------------------------------- gate
def expected_from_stage12(run_dir: Path) -> dict:
    """Seed count / conditions / noise level of the reference run (stage 12)."""
    try:
        m = json.loads((Path(run_dir) / "stage-12" / "runs" / "run-1.json").read_text()).get("metrics") or {}
    except (OSError, ValueError):
        return {}
    conds = sorted(k[: -len("_n_seeds")] for k in m if k.endswith("_n_seeds"))
    n = m.get("proposed_n_seeds")
    std = m.get("proposed_val_roc_auc_std")
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


def _evaluated(log: dict, baseline_overrides: dict | None = None) -> list[tuple[dict, float | None, str]]:
    rows = [({}, None, "initial")]
    for it in log.get("iterations", []):
        if isinstance(it, dict) and "arc_overrides" in it:
            note = it.get("arc_rejected") or ("improved" if it.get("improved") else "")
            rows.append((it["arc_overrides"], it.get("metric"), note))
    return rows


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
        "Goal: improve a graph neural network on RelBench rel-f1 / driver-top3 (binary classification). Metric: validation "
        f"ROC-AUC averaged over {seeds} seeds, HIGHER is better. The training recipe is fixed; you only choose "
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
    rows = _evaluated(log)
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

    @property
    def config_mode(self) -> bool:
        return self.mode == "config"

    @property
    def gate_enabled(self) -> bool:
        # only for experiments whose reference run reports per-condition seed counts (*_n_seeds)
        return _env("ARC_VALID_GATE", "1") == "1" and bool(self.expected.get("seeds"))


def annotate(iter_record: dict, state: ModeState) -> None:
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
    info = {"seed_offset": int(state.confirm_offset), "valid": ok, "reason": why,
            "returncode": res.returncode, "metrics": res.metrics}
    (Path(stage_dir) / "confirmation.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
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
             "These seeds were never used to choose anything.", "", "| condition | val AUROC | test AUROC |", "|---|---|---|"]
    for cond in sorted(k[: -len("_n_seeds")] for k in m if k.endswith("_n_seeds")):
        lines.append(f"| {cond} | {m.get(cond + '_val_roc_auc_mean', float('nan')):.4f} ± {m.get(cond + '_val_roc_auc_std', float('nan')):.4f} "
                     f"| {m.get(cond + '_test_roc_auc_mean', float('nan')):.4f} ± {m.get(cond + '_test_roc_auc_std', float('nan')):.4f} |")
    (Path(stage_dir) / "confirmation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.warning("Stage 13: confirmation done -> %s", (Path(stage_dir) / "confirmation.md"))
